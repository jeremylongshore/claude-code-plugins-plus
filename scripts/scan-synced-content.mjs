#!/usr/bin/env node
/**
 * scan-synced-content.mjs — deterministic supply-chain scanner for mirrored
 * external plugin content.
 *
 * WHY THIS EXISTS
 *   sync-external.mjs mirrors external repos (markdown, 60+ shell scripts, python,
 *   JSON hook/MCP configs) into plugins/** via a weekly auto-generated PR.
 *   sources.yaml pins nothing, so a compromised or rogue upstream author's next
 *   push rides into the marketplace and executes in users' agents. Nothing
 *   deterministic reads a sync diff for an injected payload, and an AI reviewer
 *   can miss a one-liner buried in a 100K-line diff. This scanner is that
 *   deterministic gate.
 *
 * GRADED FINDINGS (mirrors the escape-scan REFUSE / CHALLENGE / FLAG model — a
 * false-positive storm gets a gate disabled, so the grades are deliberately
 * separated so only genuinely-malicious content HARD-fails):
 *
 *   REFUSE    (exit 2, always fails)   high-confidence malicious, in a file that
 *             can AUTO-EXECUTE (a script, or a hook/MCP JSON/YAML config):
 *               - pipe-to-shell in an executable script (curl … | sh)
 *               - reverse-shell one-liners (bash -i >& /dev/tcp/…, nc -e /bin/sh)
 *               - decode-then-exec (base64 -d | sh, eval(atob(…)))
 *               - secret/env exfiltration to a network sink (env | curl,
 *                 cat ~/.ssh/… | curl, curl --data @~/.aws/credentials)
 *               - crypto-miner signatures (stratum+tcp://, xmrig, …)
 *             The SAME pattern inside a doc (README/SKILL.md prose) is graded
 *             CHALLENGE, not REFUSE — it doesn't auto-run and is often legit
 *             security-education content.
 *
 *   CHALLENGE (exit 1 unless --warn-only or waived)   dual-use, must be SEEN:
 *               - a documented `curl … | sh` install step (legit in a README,
 *                 but a human must confirm it — CHALLENGE, not REFUSE)
 *               - a malicious-class pattern (above) appearing in a DOC
 *               - a hook definition (.claude hooks auto-execute)
 *               - an MCP server config with a remote URL
 *               - an allowed-tools list that grants a network tool (WebFetch/WebSearch)
 *               - dynamic code exec (eval / new Function / os.system / shell=True)
 *               - outbound network calls in a shell/py script
 *
 *   FLAG      (exit 0, report-only)   smells worth a look:
 *               - an allowed-tools list that grants Bash (ubiquitous → FLAG, not
 *                 CHALLENGE, to avoid a false-positive storm)
 *               - very long single-line base64-ish blobs / heavy obfuscation
 *               - non-ASCII homoglyphs in code identifiers/commands
 *               - unusually large binary-ish files
 *               - JS outbound network calls (fetch/axios)
 *
 * USAGE
 *   node scripts/scan-synced-content.mjs                      # scan plugins/community/**
 *   node scripts/scan-synced-content.mjs --changed-only --base origin/main
 *   node scripts/scan-synced-content.mjs --changed-only --base HEAD   # working-tree diff
 *   node scripts/scan-synced-content.mjs path/a path/b        # explicit path list
 *   node scripts/scan-synced-content.mjs --warn-only ...      # CHALLENGE→exit 0 (REFUSE still 2)
 *   node scripts/scan-synced-content.mjs --json ...           # machine-readable findings
 *
 * ALLOWLIST
 *   scripts/scan-allowlist.txt holds `path:rule  reason` waivers. A waiver
 *   downgrades a CHALLENGE or FLAG to a reported-but-passing note. REFUSE is
 *   NEVER waivable via the allowlist (fail closed) — a real hard-block must be
 *   fixed at the source, not signed away.
 *
 * ANTI-EVASION (best-effort — this is a pattern scanner, defense in depth, NOT a
 * sandbox). We normalize before matching: strip comments, join `\`-continued
 * lines, and collapse quote/`+`/backslash string-concatenation so `"cur"+"l"`,
 * `c'u'rl`, and `cur\<nl>l` reduce toward `curl`. What we CANNOT catch — and do
 * not claim to — is enumerated at the bottom of this file (KNOWN BYPASSES).
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { execFileSync } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, '..');
const ALLOWLIST_FILE = path.join(__dirname, 'scan-allowlist.txt');
const DEFAULT_SCAN_ROOT = 'plugins/community';

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
};

export const GRADE = { REFUSE: 'REFUSE', CHALLENGE: 'CHALLENGE', FLAG: 'FLAG' };

const SCANNABLE_EXT = new Set([
  '.md',
  '.mdx',
  '.markdown',
  '.txt',
  '.sh',
  '.bash',
  '.zsh',
  '.py',
  '.js',
  '.mjs',
  '.cjs',
  '.ts',
  '.tsx',
  '.jsx',
  '.json',
  '.yaml',
  '.yml',
]);

/** Classify a file by extension/path so grading can be context-aware. */
export function fileClass(relPath) {
  const ext = path.extname(relPath).toLowerCase();
  const base = path.basename(relPath).toLowerCase();
  if (['.md', '.mdx', '.markdown', '.txt'].includes(ext)) return 'doc';
  if (['.sh', '.bash', '.zsh'].includes(ext)) return 'shell';
  if (ext === '.py') return 'python';
  if (['.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx'].includes(ext)) return 'js';
  if (ext === '.json' || base === '.mcp.json') return 'json';
  if (['.yaml', '.yml'].includes(ext)) return 'yaml';
  return 'other';
}

const isScript = (cls) => cls === 'shell' || cls === 'python' || cls === 'js';

// A malicious-pattern grade: REFUSE when it can auto-execute (a script, or a
// hook/MCP JSON/YAML config), CHALLENGE when it only appears in PROSE (a doc) —
// a reverse-shell string inside a README does not auto-run and is often
// legitimate security-education content, so a human confirms rather than a hard
// block nuking every pentest skill. (Known limitation: a doc-embedded payload a
// user copy-pastes is CHALLENGE, not REFUSE — see KNOWN BYPASSES.)
const refuseUnlessDoc = (cls) => (cls === 'doc' ? GRADE.CHALLENGE : GRADE.REFUSE);

// ─────────────────────────────────────────────────────────────────────────────
// Normalization (anti-evasion). Strip comments so commented-out text does not
// fire, join `\`-continued shell lines, and collapse quote/`+`/backslash
// string-concatenation so split dangerous tokens are revealed. We ALSO keep the
// raw text and scan both; a hit in EITHER view is reported (fail-closed).
// ─────────────────────────────────────────────────────────────────────────────

/** Remove `/* … *\/` block comments from JS/TS, preserving newlines/line count. */
function stripBlockComments(text) {
  return text.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '));
}

/**
 * Strip a single line's trailing/inline comment for the given language.
 * Quote-aware for the common cases; `//` inside `://` (URLs) is preserved.
 * Best-effort, documented — a determined attacker can still confuse it, which
 * is why we ALSO scan the raw line for the strong REFUSE patterns.
 */
function stripLineComment(line, cls) {
  const cutAt = (idx) => (idx >= 0 ? line.slice(0, idx) : line);
  if (cls === 'shell' || cls === 'python' || cls === 'yaml') {
    // Cut at the first `#` that is not inside single/double quotes.
    // Escape-aware: a backslash-escaped quote (`\"`) outside single quotes does
    // NOT toggle the string state, so `echo "x \" # " && curl url|sh` can't hide
    // the payload behind a fake trailing comment (red-team: escaped-quote bypass).
    let inS = false;
    let inD = false;
    let esc = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (esc) {
        esc = false;
        continue;
      }
      if (c === '\\' && !inS) {
        esc = true; // single quotes don't process backslash escapes in shell
        continue;
      }
      if (c === "'" && !inD) inS = !inS;
      else if (c === '"' && !inS) inD = !inD;
      else if (c === '#' && !inS && !inD) {
        // require start-of-line or preceding whitespace so `foo#bar` fragments
        // (rare) aren't mis-cut; a leading `#` still cuts.
        if (i === 0 || /\s/.test(line[i - 1])) return cutAt(i);
      }
    }
    return line;
  }
  if (cls === 'js') {
    // Cut at `//` that is not part of `://` and not inside a quote.
    // Escape-aware: an escaped quote inside a string (`"\""`, `'\''`, \`\\\`\`)
    // doesn't close it, so a `//` cut can't be smuggled past an escaped quote.
    let inS = false;
    let inD = false;
    let inB = false;
    let esc = false;
    for (let i = 0; i < line.length - 1; i++) {
      const c = line[i];
      if (esc) {
        esc = false;
        continue;
      }
      if (c === '\\' && (inS || inD || inB)) {
        esc = true; // backslash escapes only matter inside a string literal
        continue;
      }
      if (c === "'" && !inD && !inB) inS = !inS;
      else if (c === '"' && !inS && !inB) inD = !inD;
      else if (c === '`' && !inS && !inD) inB = !inB;
      else if (c === '/' && line[i + 1] === '/' && !inS && !inD && !inB) {
        if (i > 0 && line[i - 1] === ':') continue; // http:// etc
        return cutAt(i);
      }
    }
    return line;
  }
  return line; // doc / json / other → no line-comment stripping
}

/** Collapse quote/`+`/backslash concatenation, KEEPING unrelated spaces so `\s+`
 *  patterns still match. Reveals `"cur"+"l"` → `curl`, `"cur" + "l"` → `curl`,
 *  `c'u'rl` → `curl`. The whitespace AROUND a `+` is part of the concatenation
 *  and is dropped; other spaces are preserved. */
export function concatCollapse(line) {
  return line.replace(/\s*\+\s*/g, '').replace(/["'`\\]/g, '');
}

/**
 * Produce the logical lines to scan: comment-stripped, with `\`-continued
 * shell/js lines joined onto their starting line number. Returns
 * [{ n, text }] where n is the 1-based starting line number.
 */
export function normalizeLines(rawText, cls) {
  const text = cls === 'js' ? stripBlockComments(rawText) : rawText;
  const rawLines = text.split('\n');
  const stripped = rawLines.map((l) => stripLineComment(l, cls));
  const out = [];
  for (let i = 0; i < stripped.length; i++) {
    let text = stripped[i];
    const startN = i + 1;
    // Join trailing-backslash continuations (shell/js) so a pipe split across
    // a continuation is scanned as one logical line. Join with '' (not ' ') —
    // a shell line-continuation deletes the backslash-newline entirely, so
    // `cu\<NL>rl` is the token `curl`, not `cu rl` (red-team: continuation split).
    while ((cls === 'shell' || cls === 'js') && /\\\s*$/.test(text) && i + 1 < stripped.length) {
      text = text.replace(/\\\s*$/, '') + stripped[i + 1];
      i++;
    }
    out.push({ n: startN, text });
  }
  return out;
}

// ─────────────────────────────────────────────────────────────────────────────
// Line-level rules. Each is tested against BOTH the stripped line and its
// concat-collapsed form; a match in either is a finding (deduped by id+line).
// `grade` may be a function of the file class (e.g. pipe-to-shell is REFUSE in a
// script, CHALLENGE in a doc). `langs` limits which file classes a rule applies
// to ('*' = all).
// ─────────────────────────────────────────────────────────────────────────────
const LINE_RULES = [
  {
    id: 'pipe-to-shell',
    // json/yaml added (red-team F1): `.mcp.json` stdio commands + hook/config
    // YAML are canonical auto-execute surfaces, and `curl|sh` inside them was
    // previously invisible. Interpreters beyond sh added (F3): fetch-and-run via
    // python/node/perl/ruby is identical RCE. Process-substitution added (F2):
    // `bash <(curl …)` is unobfuscated textbook RCE the pipe anchor missed.
    langs: ['shell', 'python', 'js', 'doc', 'json', 'yaml'],
    re: /\b(?:curl|wget)\b[^\n|]{0,200}\|\s*(?:sudo\s+)?(?:sh|bash|zsh|dash|ksh|python[0-9.]*|node|perl|ruby)\b|(?:\b(?:sh|bash|zsh|dash|ksh|source)\b|(?:^|[;&|])\s*\.)\s+<\(\s*(?:curl|wget)\b/i,
    grade: (cls) => (cls === 'doc' ? GRADE.CHALLENGE : GRADE.REFUSE),
    label: 'pipe-to-shell (curl/wget fetched into a shell/interpreter)',
  },
  {
    id: 'reverse-shell',
    langs: '*',
    // Require the reverse-shell idiom (>& /dev/tcp, bash -i + /dev/tcp, 0>&1, or
    // nc -e). A plain connectivity check `echo > /dev/tcp/host/443` (no `&`, no
    // `-i`, no `0>&1`) intentionally does NOT match.
    re: /(?:>&\s*\/dev\/(?:tcp|udp)\/|\b(?:ba|z)?sh\b\s+-[a-z]*i[a-z]*\b[^\n]{0,80}\/dev\/(?:tcp|udp)\/|\/dev\/(?:tcp|udp)\/\S+\/\d+\s+0>&1|\bn(?:c|cat)\b[^\n]{0,40}-e\s*\/(?:bin|usr\/bin)\/(?:ba|z)?sh|mkfifo\b[^\n]{0,80}\|\s*n(?:c|cat)\b)/i,
    grade: refuseUnlessDoc,
    label: 'reverse-shell one-liner',
  },
  {
    id: 'decode-exec',
    langs: '*',
    re: /(?:\b(?:base64|base32|xxd|openssl\s+enc)\b[^\n|]{0,80}(?:-d|--decode|-D)\b[^\n]{0,80}\|\s*(?:sudo\s+)?(?:sh|bash|zsh|python[0-9.]*|node|perl|ruby)\b|\beval\s*\(\s*(?:atob|Buffer\.from|decodeURIComponent)\b|\b(?:exec|eval)\s*\(\s*base64\.b64decode|eval\s+"?\$\([^)]*\|\s*base64\s+(?:-d|--decode))/i,
    grade: refuseUnlessDoc,
    label: 'decode-then-execute',
  },
  {
    id: 'secret-exfil',
    langs: '*',
    re: /(?:\b(?:printenv|env|set)\b\s*\|\s*(?:curl|wget|nc|ncat|http)\b|\b(?:cat|less|head|tail|xxd|base64)\b\s+[^\n|]{0,80}(?:\.ssh\/|\.aws\/credentials|\/\.aws\/|\.env\b|\.netrc|id_rsa|id_ed25519|id_dsa)[^\n|]{0,80}\|\s*(?:curl|wget|nc|ncat)\b|\b(?:curl|wget)\b[^\n]{0,200}(?:--data|--data-binary|-d|-F|--form|--upload-file|-T)\b[^\n]{0,80}(?:\.ssh\/|\.aws\/credentials|\.env\b|id_rsa|id_ed25519|printenv|\$\{?HOME\}?\/\.ssh))/i,
    grade: refuseUnlessDoc,
    label: 'secret/env exfiltration to a network sink',
  },
  {
    id: 'crypto-miner',
    langs: '*',
    re: /(?:stratum\+(?:tcp|ssl):\/\/|\bxmrig\b|\bminerd\b|\bcryptonight\b|\bcoinhive\b|--donate-level\b|\bcpuminer\b)/i,
    grade: refuseUnlessDoc,
    label: 'crypto-miner signature',
  },
  {
    id: 'dynamic-exec',
    // json/yaml added (red-team F1): a config string value can carry an exec()
    // that runs when the config is loaded/executed.
    langs: ['shell', 'python', 'js', 'json', 'yaml'],
    // Dual-use dynamic code execution. redis `.eval(` (a Lua call, not code
    // exec) is excluded to match the repo's existing dangerous-pattern gate.
    re: /(?:\bnew\s+Function\s*\(|\bos\.system\s*\(|subprocess\.(?:run|call|Popen|check_output|check_call)\s*\([^\n]*shell\s*=\s*True|(?<!redis\.)(?<!\.redis)\beval\s*\(|(?<![.\w])exec\s*\()/i,
    grade: () => GRADE.CHALLENGE,
    label: 'dynamic code execution',
  },
  {
    id: 'outbound-network',
    // json/yaml added (red-team F1): an outbound call embedded in a config
    // string (e.g. an .mcp.json stdio command) must at least be SEEN (CHALLENGE).
    langs: ['shell', 'python', 'json', 'yaml'],
    re: /(?:\b(?:curl|wget|nc|ncat|telnet)\b|\brequests\.(?:get|post|put|delete|patch|head)\s*\(|\burllib(?:2|\.request)?\b|\bhttpx\b|\bhttp\.client\b|\bsocket\.connect\b)/i,
    grade: () => GRADE.CHALLENGE,
    label: 'outbound network call in a shell/py script',
  },
  {
    id: 'outbound-network-js',
    langs: ['js'],
    re: /(?:\bfetch\s*\(|\baxios\b|\bhttps?\.request\s*\(|\bXMLHttpRequest\b)/i,
    grade: () => GRADE.FLAG,
    label: 'outbound network call in a JS script',
  },
  {
    id: 'long-base64-blob',
    langs: '*',
    re: /[A-Za-z0-9+/]{160,}={0,2}/,
    grade: () => GRADE.FLAG,
    label: 'very long single-line base64-ish blob',
    concatSafe: false, // never test the concat view — collapse would create noise
  },
  {
    id: 'heavy-obfuscation',
    langs: ['shell', 'python', 'js'],
    re: /(?:(?:\\x[0-9a-fA-F]{2}){6,}|(?:\\u[0-9a-fA-F]{4}){6,}|String\.fromCharCode\s*\((?:[^)]*,){6,}|(?:chr\(\d+\)\s*\+\s*){5,})/,
    grade: () => GRADE.FLAG,
    label: 'heavy character-code / hex-escape obfuscation',
    concatSafe: false,
  },
];

// Homoglyph detection: Cyrillic (U+0400–04FF) or Greek (U+0370–03FF) letters
// appearing adjacent to ASCII letters in a code-ish line — a classic
// look-alike-identifier trick.
const HOMOGLYPH_RE = /[A-Za-z][Ͱ-ϿЀ-ӿ]|[Ͱ-ϿЀ-ӿ][A-Za-z]/;

// ─────────────────────────────────────────────────────────────────────────────
// File-level rules (whole-file signals, not line-anchored to a token).
// ─────────────────────────────────────────────────────────────────────────────

/** Detect a .claude hook definition (hooks auto-execute → must be seen). */
function detectHookDefinition(relPath, text, cls) {
  const findings = [];
  const inHooksDir = /(?:^|\/)hooks\//.test(relPath);
  const base = path.basename(relPath).toLowerCase();
  // Match BOTH quoted (JSON) and unquoted (YAML) keys (red-team F1): a YAML hook
  // block uses `hooks:` / `PostToolUse:` with no quotes, which the quoted-only
  // pattern missed entirely — so an unquoted-YAML hook did not even CHALLENGE.
  const hooksKey = /(?:"hooks"|(?:^|\n)[ \t]*hooks)\s*:/;
  const eventKey =
    /(?:"(?:PreToolUse|PostToolUse|PreCompact|SessionStart|SessionEnd|UserPromptSubmit|Notification|Stop|SubagentStop)"|(?:^|\n)[ \t]*(?:PreToolUse|PostToolUse|PreCompact|SessionStart|SessionEnd|UserPromptSubmit|Notification|Stop|SubagentStop))\s*:/;
  if (
    (cls === 'json' || cls === 'yaml' || cls === 'doc' || inHooksDir) &&
    (hooksKey.test(text) || eventKey.test(text) || (inHooksDir && isScript(cls)))
  ) {
    const line = lineOf(text, hooksKey) || lineOf(text, eventKey) || 1;
    findings.push({
      id: 'hook-definition',
      grade: GRADE.CHALLENGE,
      line,
      label: 'hook definition (auto-executes in the agent)',
      snippet: base,
    });
  }
  return findings;
}

/**
 * Detect single-file secret exfiltration (red-team F4): a read of a credential
 * file / env co-occurring with a network SINK in the same file. The line-level
 * `secret-exfil` rule is curl/wget-piped-specific and misses the python idiom
 * `open('~/.ssh/id_rsa').read()` … `urllib.request.urlopen(url, data)` /
 * `requests.post(url, data=os.environ)` split across statements. This is a
 * file-level co-occurrence check: a secret READ + a network SINK anywhere in a
 * script → REFUSE (the bytes exfiltrate on execution), doc → CHALLENGE.
 */
function detectSecretExfilCoOccurrence(relPath, text, cls) {
  const findings = [];
  if (!['shell', 'python', 'js', 'doc'].includes(cls)) return findings;
  const secretRead =
    /(?:open\s*\(\s*['"][^'"\n]*(?:\.ssh\/|id_rsa|id_ed25519|id_dsa|\.aws\/credentials|\.netrc|\.env\b|\.git-credentials)|\bos\.environ\b|\bprocess\.env\b|\breadFileSync\s*\(\s*['"][^'"\n]*(?:\.ssh\/|id_rsa|\.aws\/credentials|\.env\b))/;
  const networkSink =
    /(?:urllib\.request\.urlopen|urllib2\.urlopen|requests\.(?:post|put|patch)|httpx\.(?:post|put|patch)|http\.client|socket\.(?:connect|sendall)|\.sendall\s*\(|fetch\s*\(|axios\.(?:post|put)|https?\.request\s*\()/;
  if (secretRead.test(text) && networkSink.test(text)) {
    const line = lineOf(text, secretRead) || 1;
    const grade = cls === 'doc' ? GRADE.CHALLENGE : GRADE.REFUSE;
    findings.push({
      id: 'secret-exfil-cooccur',
      grade,
      line,
      label: 'secret/credential read co-occurring with a network sink (single-file exfil)',
      snippet: path.basename(relPath),
    });
  }
  return findings;
}

/** Detect an MCP server config carrying a remote URL. */
function detectMcpRemote(relPath, text, cls) {
  const findings = [];
  const base = path.basename(relPath).toLowerCase();
  const looksMcp = base === '.mcp.json' || /"mcpServers"\s*:/.test(text);
  if (!looksMcp) return findings;
  const remoteUrl = /"url"\s*:\s*"https?:\/\//i;
  const remoteType = /"type"\s*:\s*"(?:http|sse|ws|websocket)"/i;
  if (remoteUrl.test(text) || remoteType.test(text)) {
    const line = lineOf(text, remoteUrl) || lineOf(text, remoteType) || 1;
    findings.push({
      id: 'mcp-remote',
      grade: GRADE.CHALLENGE,
      line,
      label: 'MCP server config with a remote URL',
      snippet: base,
    });
  }
  return findings;
}

/**
 * Detect an allowed-tools list that grants privileged tools. Graded split:
 *   - network tools (WebFetch / WebSearch) → CHALLENGE (rarer; a skill that can
 *     reach the network is the genuinely "must be seen" case for exfil).
 *   - Bash → FLAG only. Bash is table-stakes for skills (thousands declare it),
 *     so a CHALLENGE here would be a guaranteed false-positive storm — exactly
 *     what gets a gate disabled. A reviewer still sees the FLAG note.
 * (Without a base-vs-head diff we can't prove a grant is NEWLY added; on a
 * --changed-only run this only fires for a changed file, which is the closest
 * deterministic proxy for "adds".)
 */
function detectPrivilegedTools(relPath, text, cls) {
  if (!['doc', 'json', 'yaml'].includes(cls)) return [];
  const lines = text.split('\n');
  const findings = [];
  const header = /allowed[-_]tools\s*[:=]/i;
  const net = /\b(WebFetch|WebSearch)\b/;
  const bash = /\bBash\b/;
  for (let i = 0; i < lines.length; i++) {
    if (!header.test(lines[i])) continue;
    // Same line (inline list) or the following YAML/JSON list window.
    const windowText = lines.slice(i, i + 20).join('\n');
    if (net.test(windowText)) {
      findings.push({
        id: 'allowed-tools-network',
        grade: GRADE.CHALLENGE,
        line: i + 1,
        label: 'allowed-tools grants a network tool (WebFetch/WebSearch)',
        snippet: lines[i].trim().slice(0, 80),
      });
    } else if (bash.test(windowText)) {
      findings.push({
        id: 'allowed-tools-bash',
        grade: GRADE.FLAG,
        line: i + 1,
        label: 'allowed-tools grants Bash',
        snippet: lines[i].trim().slice(0, 80),
      });
    }
  }
  return findings;
}

/** 1-based line number of the first match of `re` in `text`, or 0. */
function lineOf(text, re) {
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (re.test(lines[i])) return i + 1;
  }
  return 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// Core: scan one file's content → findings[]. Pure (no fs), so tests drive it
// directly with in-memory fixtures.
// ─────────────────────────────────────────────────────────────────────────────
/**
 * @param {string} text     file content (utf8)
 * @param {string} relPath  repo-relative path (drives file-class grading)
 * @returns {Array<{id,grade,line,label,snippet}>}
 */
export function scanContent(text, relPath) {
  const cls = fileClass(relPath);
  const findings = [];
  const seen = new Set();
  const push = (f) => {
    const key = `${f.id}:${f.line}`;
    if (seen.has(key)) return;
    seen.add(key);
    findings.push(f);
  };

  // File-level signals.
  for (const f of detectHookDefinition(relPath, text, cls)) push(f);
  for (const f of detectSecretExfilCoOccurrence(relPath, text, cls)) push(f);
  for (const f of detectMcpRemote(relPath, text, cls)) push(f);
  for (const f of detectPrivilegedTools(relPath, text, cls)) push(f);

  // Line-level signals over normalized (+ concat) views.
  const logical = normalizeLines(text, cls);
  for (const { n, text: lineText } of logical) {
    const collapsed = concatCollapse(lineText);
    for (const rule of LINE_RULES) {
      if (rule.langs !== '*' && !rule.langs.includes(cls)) continue;
      const views = rule.concatSafe === false ? [lineText] : [lineText, collapsed];
      let matched = null;
      for (const v of views) {
        const m = rule.re.exec(v);
        if (m) {
          matched = m[0];
          break;
        }
      }
      if (!matched) continue;
      const grade = typeof rule.grade === 'function' ? rule.grade(cls) : rule.grade;
      push({
        id: rule.id,
        grade,
        line: n,
        label: rule.label,
        snippet: matched.trim().slice(0, 100),
      });
    }
    // Homoglyph — only when there IS a non-ASCII letter adjacent to ASCII.
    if (HOMOGLYPH_RE.test(lineText)) {
      push({
        id: 'homoglyph',
        grade: GRADE.FLAG,
        line: n,
        label: 'non-ASCII homoglyph adjacent to ASCII in code',
        snippet: lineText.trim().slice(0, 80),
      });
    }
  }
  return findings;
}

// ─────────────────────────────────────────────────────────────────────────────
// Allowlist: `path:rule  reason`. Downgrades CHALLENGE/FLAG (never REFUSE).
// ─────────────────────────────────────────────────────────────────────────────
/** Parse allowlist text → [{ pathGlob, rule, reason }]. Reason is REQUIRED. */
export function parseAllowlist(text) {
  const out = [];
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    // Split off the reason: everything after the first run of 2+ spaces or a `#`.
    const m = /^(\S+?):([A-Za-z0-9-]+)(?:\s{2,}|\s*#\s*|\s+)(.+)$/.exec(line);
    if (!m) continue; // malformed (e.g. missing reason) → ignored, not honored
    const [, pathGlob, rule, reason] = m;
    if (!reason.trim()) continue;
    out.push({ pathGlob, rule, reason: reason.trim() });
  }
  return out;
}

/** Glob (`*`/`**`) match for allowlist paths. */
function globMatch(glob, filePath) {
  const esc = glob
    .replace(/[.+^${}()|[\]\\]/g, '\\$&')
    .replace(/\*\*/g, '<<DS>>')
    .replace(/\*/g, '[^/]*')
    .replace(/<<DS>>/g, '.*');
  return new RegExp('^' + esc + '$').test(filePath);
}

/** Is (filePath, ruleId) waived? REFUSE is never waivable. */
export function isWaived(waivers, filePath, ruleId, grade) {
  if (grade === GRADE.REFUSE) return null;
  for (const w of waivers) {
    if (w.rule !== ruleId) continue;
    if (w.pathGlob === filePath || globMatch(w.pathGlob, filePath)) return w.reason;
  }
  return null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Exit-code decision from a flat list of per-file findings.
// ─────────────────────────────────────────────────────────────────────────────
export function decideExit(findings, { warnOnly = false } = {}) {
  const active = findings.filter((f) => !f.waivedReason);
  const hasRefuse = active.some((f) => f.grade === GRADE.REFUSE);
  const hasChallenge = active.some((f) => f.grade === GRADE.CHALLENGE);
  if (hasRefuse) return 2;
  if (hasChallenge && !warnOnly) return 1;
  return 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// File collection.
// ─────────────────────────────────────────────────────────────────────────────
function isBinary(buf) {
  const n = Math.min(buf.length, 8000);
  for (let i = 0; i < n; i++) if (buf[i] === 0) return true;
  return false;
}

function walk(absDir, relPrefix, acc) {
  let entries;
  try {
    entries = fs.readdirSync(absDir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const ent of entries) {
    if (ent.name === '.git' || ent.name === 'node_modules') continue;
    const abs = path.join(absDir, ent.name);
    const rel = relPrefix ? `${relPrefix}/${ent.name}` : ent.name;
    if (ent.isDirectory()) walk(abs, rel, acc);
    else if (ent.isFile()) acc.push(rel);
  }
}

/** Files changed vs a base ref (committed diff + staged + untracked). */
function changedFiles(base) {
  const run = (args) => {
    try {
      return execFileSync('git', ['-C', ROOT_DIR, ...args], {
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'ignore'],
      })
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
    } catch {
      return [];
    }
  };
  const set = new Set([
    ...run(['diff', '--name-only', '--diff-filter=d', base]),
    ...run(['diff', '--name-only', '--diff-filter=d', '--cached', base]),
    ...run(['ls-files', '--others', '--exclude-standard']),
  ]);
  return [...set];
}

/** Resolve the list of repo-relative files to scan from CLI options. */
function collectTargets(opts) {
  let rels = [];
  if (opts.changedOnly) {
    // Scope to the sync's actual write surface (plugins/**). The mirrored
    // content is the threat model; first-party scripts/ + workflows are covered
    // by CodeQL/review and — critically — this scanner's OWN test fixtures live
    // under scripts/, so scanning them would self-flag the malicious sample
    // strings. sources.yaml-only PRs legitimately produce no plugin diff here;
    // their protection is the sync-time scan of the resulting mirrored content.
    rels = changedFiles(opts.base || 'origin/main').filter((r) => r.startsWith('plugins/'));
  } else if (opts.paths.length > 0) {
    for (const p of opts.paths) {
      const abs = path.resolve(ROOT_DIR, p);
      let st;
      try {
        st = fs.statSync(abs);
      } catch {
        continue;
      }
      if (st.isDirectory()) {
        const acc = [];
        walk(abs, path.relative(ROOT_DIR, abs), acc);
        rels.push(...acc);
      } else {
        rels.push(path.relative(ROOT_DIR, abs));
      }
    }
  } else {
    const acc = [];
    walk(path.join(ROOT_DIR, DEFAULT_SCAN_ROOT), DEFAULT_SCAN_ROOT, acc);
    rels = acc;
  }
  // Keep only existing, scannable files.
  return rels.filter((rel) => {
    const ext = path.extname(rel).toLowerCase();
    const inHooks = /(?:^|\/)hooks\//.test(rel);
    if (!SCANNABLE_EXT.has(ext) && !inHooks) return false;
    return fs.existsSync(path.resolve(ROOT_DIR, rel));
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const opts = { changedOnly: false, base: null, warnOnly: false, json: false, paths: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--changed-only') opts.changedOnly = true;
    else if (a === '--warn-only') opts.warnOnly = true;
    else if (a === '--json') opts.json = true;
    else if (a === '--base') opts.base = argv[++i];
    else if (a.startsWith('--base=')) opts.base = a.slice('--base='.length);
    else if (a.startsWith('--')) {
      /* ignore unknown flags */
    } else opts.paths.push(a);
  }
  return opts;
}

function loadWaivers() {
  if (!fs.existsSync(ALLOWLIST_FILE)) return [];
  try {
    return parseAllowlist(fs.readFileSync(ALLOWLIST_FILE, 'utf8'));
  } catch {
    return [];
  }
}

function log(msg, color = '') {
  console.log(`${color}${msg}${colors.reset}`);
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const waivers = loadWaivers();
  const targets = collectTargets(opts);

  const gradeColor = { REFUSE: colors.red, CHALLENGE: colors.yellow, FLAG: colors.magenta };
  const gradeIcon = { REFUSE: '✗', CHALLENGE: '⚠', FLAG: 'ℹ' };

  let all = [];
  let scanned = 0;
  const perFile = [];

  for (const rel of targets) {
    const abs = path.resolve(ROOT_DIR, rel);
    let buf;
    try {
      buf = fs.readFileSync(abs);
    } catch {
      continue;
    }
    scanned++;
    let findings = [];
    if (isBinary(buf)) {
      if (buf.length > 256 * 1024) {
        findings.push({
          id: 'large-binaryish',
          grade: GRADE.FLAG,
          line: 1,
          label: `unusually large binary-ish file (${Math.round(buf.length / 1024)} KB)`,
          snippet: path.basename(rel),
        });
      }
    } else {
      findings = scanContent(buf.toString('utf8'), rel);
    }
    for (const f of findings) {
      f.file = rel;
      f.waivedReason = isWaived(waivers, rel, f.id, f.grade);
    }
    if (findings.length) perFile.push({ rel, findings });
    all = all.concat(findings);
  }

  // F6/F7 — trust-surface change with nothing to scan must not pass silently.
  // In --changed-only mode we scope to plugins/**, so a root sources.yaml /
  // sources.lock.json edit (adding or repointing an upstream source) scans zero
  // files and would go green. The mirrored content of the new source is scanned
  // at sync time, but a human must still confirm the source is vetted + pinned —
  // so emit a waivable CHALLENGE (fails the gate loudly; a reviewer clears it with
  // a `sources.yaml:sources-change-unscanned  <reason>` line in scan-allowlist.txt).
  if (opts.changedOnly && scanned === 0) {
    const trustFiles = changedFiles(opts.base || 'origin/main').filter(
      (r) => r === 'sources.yaml' || r === 'sources.yml' || r === 'sources.lock.json',
    );
    if (trustFiles.length) {
      const f = {
        id: 'sources-change-unscanned',
        grade: GRADE.CHALLENGE,
        line: 1,
        label:
          'source-list change with no mirrored content in this diff — the changed source is ' +
          'scanned at sync time; confirm it is vetted and pinned in sources.lock.json',
        snippet: trustFiles.join(', ').slice(0, 100),
        file: trustFiles[0],
      };
      f.waivedReason = isWaived(waivers, f.file, f.id, f.grade);
      perFile.push({ rel: f.file, findings: [f] });
      all = all.concat(f);
    }
  }

  const exitCode = decideExit(all, { warnOnly: opts.warnOnly });

  if (opts.json) {
    // Use process.stdout.write (not console.log + process.exit) so a large
    // report is fully flushed to a pipe before the process exits — process.exit
    // can truncate a big buffered write mid-flush.
    process.stdout.write(
      JSON.stringify({ scanned, findings: all, exitCode, warnOnly: opts.warnOnly }, null, 2) + '\n',
    );
    process.exitCode = exitCode;
    return;
  }

  log('🔒 Scanning synced content for injected payloads…\n', colors.bright + colors.cyan);
  log(
    `Scanned ${scanned} file(s)${opts.changedOnly ? ` (changed vs ${opts.base || 'origin/main'})` : ''}\n`,
    colors.dim,
  );

  const counts = { REFUSE: 0, CHALLENGE: 0, FLAG: 0, waived: 0 };
  for (const { rel, findings } of perFile) {
    for (const f of findings) {
      if (f.waivedReason) {
        counts.waived++;
        log(
          `  ✓ ${rel}:${f.line} [${f.grade} WAIVED] ${f.id} — ${f.label} (waived: ${f.waivedReason})`,
          colors.dim,
        );
      } else {
        counts[f.grade]++;
        const c = gradeColor[f.grade];
        log(`  ${gradeIcon[f.grade]} ${rel}:${f.line} [${f.grade}] ${f.id} — ${f.label}`, c);
        log(`      matched: ${f.snippet}`, colors.dim);
      }
    }
  }

  if (counts.REFUSE + counts.CHALLENGE + counts.FLAG === 0) {
    log('  ✓ No suspicious patterns detected', colors.green);
  }

  log(
    `\n📊 ${counts.REFUSE} REFUSE · ${counts.CHALLENGE} CHALLENGE · ${counts.FLAG} FLAG · ${counts.waived} waived\n`,
    colors.bright,
  );

  if (exitCode === 2) {
    log('❌ REFUSE — high-confidence malicious content. Sync/PR blocked.\n', colors.red);
  } else if (exitCode === 1) {
    log(
      '⚠️  CHALLENGE — dual-use content needs human sign-off. Add a `path:rule  reason` waiver\n' +
        '   to scripts/scan-allowlist.txt (in this PR) once reviewed, or fix the source.\n',
      colors.yellow,
    );
  } else if (opts.warnOnly && counts.CHALLENGE > 0) {
    log(
      '⚠️  CHALLENGE present but --warn-only set (REFUSE would still block). Review the auto-PR.\n',
      colors.yellow,
    );
  } else {
    log('✅ No blocking findings.\n', colors.green);
  }

  process.exitCode = exitCode;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  main();
}

/*
 * KNOWN BYPASSES (this is a pattern scanner, NOT a sandbox — defense in depth):
 *   - Command-name indirection via a RUNTIME value: `C=$(printf '\x63url'); $C … | sh`,
 *     an env-var-built binary name, or `${arr[@]}` reassembly. We collapse
 *     compile-time quote/`+` concatenation only.
 *   - A payload delivered as base64/gzip DATA that a *later* step or a fetched
 *     remote resource decodes+executes. We flag long base64 blobs (FLAG) but do
 *     not decode-and-re-scan, and we cannot see what a remote URL returns.
 *   - Logic split across MULTIPLE files (read secret in file A, POST in file B).
 *     Our exfil rules are single-logical-line.
 *   - Novel homoglyph ranges beyond Greek/Cyrillic, or an all-non-ASCII identifier.
 *   - Semantically-malicious but syntactically-benign code (a legit-looking API
 *     client that ships data to an attacker endpoint whose URL passes our checks).
 *   - Anything in a file type we don't scan, or below our size/threshold cutoffs.
 * The mitigation for all of these is layered review: REFUSE hard-blocks the
 * obvious classes; CHALLENGE forces a human onto the dual-use classes; the
 * auto-sync PR is itself reviewed before merge; and gitleaks/CodeQL run in
 * parallel. This scanner raises the cost of the cheap attacks, it does not
 * eliminate a determined, sandbox-grade adversary.
 */
