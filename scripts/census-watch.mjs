#!/usr/bin/env node
/**
 * census-watch.mjs — local watcher + deadline enforcer for the 2026-07-08
 * whole-catalog quality census.
 *
 * WHY THIS EXISTS (and why it runs locally, not as a cloud routine):
 *   The 2026-07-08 census graded 27 marketplace source-entries D/F and put them on a
 *   delist clock (deadline 2026-07-22 — see the `# census 2026-07-08 … deadline 2026-07-22`
 *   comments in sources.yaml and bead claude-ss50.8). Those sources live in cross-owner
 *   upstream repos (datopian/*, wondelai/*, numman-ali/*, …). A previous cloud routine
 *   tried to watch them but its sandboxed GitHub-App session was scoped to a single owner
 *   (jeremylongshore), so every cross-owner read was blocked (add_repo cross-tier rejected,
 *   raw api.github.com intercepted). This script runs on the dev box where `gh` has
 *   unrestricted cross-owner read access, so it can actually do the job. The deadline
 *   ENFORCEMENT (below) moved here for the same reason: the cloud one-shot that was meant
 *   to enforce on 2026-07-23 could not reach the cross-owner census upstreams either
 *   (disabled 2026-07-10; its semantics are replicated by --enforce).
 *
 * WATCH MODE (default — daily cron):
 *   1. Parses sources.yaml, selecting the entries carrying the census delist-deadline marker.
 *   2. Collapses them to unique upstream repos (n-skills / wondelai are monorepos → many
 *      source-entries share one repo).
 *   3. For each upstream, reads the default-branch HEAD (sha + commit date) via `gh api`.
 *   4. Classifies each: GONE (repo deleted/archived → auto-delist), MOVED (pushed since the
 *      census date → the maintainer MAY have landed the fix → re-grade candidate), or
 *      DORMANT (no activity since census → delist candidate on the deadline).
 *   5. Diffs against the previous run's state so subsequent runs surface *new* movement,
 *      and rewrites the state file. First run initializes the baseline.
 *
 * ENFORCE MODE (--enforce — fired ONCE by the cron wrapper when the deadline passes):
 *   Replicates the disabled cloud one-shot's semantics against the LIVE delist clock
 *   (sources.yaml on origin/main at run time — never a frozen list; entries fixed or
 *   removed since notify day simply are not on the clock any more):
 *   1. For each delist-clock cluster (unique upstream repo), validates every notified
 *      skill at UPSTREAM default-branch HEAD with validate-skills-schema.py
 *      --marketplace --json. Cluster PASSES only if ALL its skills have 0 errors.
 *      Deleted/private/archived upstream = FAIL. Partial pass = FAIL. Upstream is truth —
 *      the mirror may lag or be quarantined, so grading the mirror would be wrong.
 *   2. For still-failing clusters, builds branch fix/census-deadline-removals off
 *      origin/main in its own temp clone (never disturbs the invoking checkout) with ONE
 *      commit: remove each failing cluster's sources.yaml entries (dated NOTE comment
 *      with the notify-issue link + re-listing-welcome), delete their mirror dirs under
 *      plugins/, drop their catalog entries from marketplace.extended.json + regenerate
 *      the derived artifacts (marketplace.json, plugin package.jsons, README AUTO-TOC —
 *      otherwise validate-catalog-invariants.py fails the PR on catalog entries whose
 *      source dir no longer exists), and swap the scan-allowlist.txt TEMPORARY
 *      sources-change-unscanned line for this PR's scoped reason. sources.yaml is
 *      yaml.safe_load-validated and prettier-checked before commit.
 *   3. Opens ONE PR ([skip auto-bump], results table, DO NOT MERGE — Jeremy merges;
 *      this script never calls merge).
 *   4. Posts the results table on the census tracking issue (#984) and one closing
 *      comment per still-open notify issue (thank-you-verified on PASS,
 *      removed-with-PR-link + re-listing-welcome on FAIL). Courtesy-tier repos
 *      (Skyvern, x-twitter-scraper) and kobiton are NEVER touched.
 *   5. Idempotent: if the branch/PR already exists it is detected and reported, never
 *      duplicated; every comment carries a hidden marker and is skipped when present,
 *      so a partially-failed run can be safely retried the next day.
 *
 *   --enforce --dry-run does everything READ-ONLY (upstream validation + would-remove
 *   report; no clone, no branch, no PR, no comments, no state writes). Live --enforce
 *   additionally refuses to run before the deadline has passed (defense-in-depth on
 *   top of the wrapper's days-left gate).
 *
 * OUTPUT: a human report to stdout + a machine state file. With --json the machine
 *   payload goes to stdout and the human report to stderr (so wrappers can jq it).
 *
 * Zero runtime deps (no js-yaml) on purpose: a local cron must run without `npm install`.
 * sources.yaml has a stable 2-space list indent, so raw block parsing is reliable.
 *
 * Usage:  node scripts/census-watch.mjs [--json]
 *         node scripts/census-watch.mjs --enforce --dry-run [--json]
 *         node scripts/census-watch.mjs --enforce [--json]
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';
import { execFileSync, spawnSync } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.join(__dirname, '..');
const SOURCES_FILE = path.join(REPO_ROOT, 'sources.yaml');
const VALIDATOR = path.join(__dirname, 'validate-skills-schema.py');
const STATE_DIR = path.join(os.homedir(), '.local', 'state', 'census-watch');
const STATE_FILE = path.join(STATE_DIR, 'state.json');
const ENFORCE_RESULT_FILE = path.join(STATE_DIR, 'enforce-result.json');

const CENSUS_DATE = '2026-07-08'; // the whole-catalog census that set the clock
const DEADLINE = '2026-07-22'; // delist deadline for sources still failing
const DEADLINE_MARKER = `deadline ${DEADLINE}`; // stable comment string in sources.yaml

// Enforcement surface (marketplace repo, tracking issue, removal branch).
const MARKETPLACE_REPO = 'jeremylongshore/claude-code-plugins-plus-skills';
const MARKETPLACE_OWNER = 'jeremylongshore'; // author of the 2026-07-08 notify issues
const RESULTS_ISSUE = 984; // census tracking issue — gets the results table
const ENFORCE_BRANCH = 'fix/census-deadline-removals';
// Hidden idempotency marker planted in every comment this script posts.
const COMMENT_MARKER = '<!-- census-enforce:2026-07-22 -->';
// Courtesy-tier / partner-channel repos: NEVER acted on, even if a deadline
// marker somehow appears against them in sources.yaml.
const NEVER_TOUCH = [/skyvern/i, /x-twitter/i, /kobiton/i];
const SIGNATURE = '- Jeremy Longshore\nintentsolutions.io';

const JSON_OUT = process.argv.includes('--json');
const ENFORCE = process.argv.includes('--enforce');
const DRY_RUN = process.argv.includes('--dry-run');

/** Parse a sources.yaml text by raw 2-space list blocks; return census-marked entries. */
export function parseOnClockSources(raw) {
  // Split on the top-level list-item delimiter. slice(1) drops the file header.
  const blocks = raw.split(/\n {2}- name:/).slice(1);
  const out = [];
  for (const b of blocks) {
    if (!b.includes(DEADLINE_MARKER)) continue;
    const name = (b.match(/^\s*(\S.*)$/m)?.[1] || '(unknown)').trim();
    const repoM = b.match(/\n\s*repo:\s*(\S+)/);
    if (!repoM) continue;
    out.push({
      name,
      repo: repoM[1].trim(),
      sourcePath: (b.match(/\n\s*source_path:\s*(\S+)/)?.[1] || '').trim(),
      targetPath: (b.match(/\n\s*target_path:\s*(\S+)/)?.[1] || '').trim(),
    });
  }
  return out;
}

function onClockSources() {
  return parseOnClockSources(fs.readFileSync(SOURCES_FILE, 'utf8'));
}

/** Read the default-branch HEAD of an upstream repo via gh. Returns null on 404/gone. */
function upstreamHead(repo) {
  let meta;
  try {
    meta = JSON.parse(
      execFileSync(
        'gh',
        ['api', `repos/${repo}`, '--jq', '{default_branch, archived, pushed_at}'],
        { encoding: 'utf8' },
      ),
    );
  } catch {
    return { gone: true };
  }
  if (meta.archived) return { gone: true, archived: true, pushedAt: meta.pushed_at };
  let head;
  try {
    const line = execFileSync(
      'gh',
      [
        'api',
        `repos/${repo}/commits/${meta.default_branch}`,
        '--jq',
        '.sha + "|" + .commit.committer.date',
      ],
      { encoding: 'utf8' },
    ).trim();
    const [sha, date] = line.split('|');
    head = { sha: sha.slice(0, 12), date };
  } catch {
    head = { sha: null, date: meta.pushed_at };
  }
  return {
    gone: false,
    defaultBranch: meta.default_branch,
    headSha: head.sha,
    headDate: head.date,
  };
}

function classify(info) {
  if (info.gone) return info.archived ? 'GONE-ARCHIVED' : 'GONE-DELETED';
  if (!info.headDate) return 'DORMANT';
  return new Date(info.headDate) > new Date(`${CENSUS_DATE}T00:00:00Z`) ? 'MOVED' : 'DORMANT';
}

function daysLeftAt(now) {
  return Math.ceil((new Date(`${DEADLINE}T23:59:59Z`) - now) / 86_400_000);
}

// ─────────────────────────────────────────────────────────────────────────────
// Enforce mode — pure decision/transform logic (exported for the fixture tests
// in census-watch.test.mjs; no network, no fs).
// ─────────────────────────────────────────────────────────────────────────────

/** True when the delist deadline has fully passed (enforcement is due). */
export function enforcementDue(now) {
  return daysLeftAt(now) <= 0;
}

/** Courtesy-tier / partner guard — repos and source names we never act on. */
export function isNeverTouch(s) {
  return NEVER_TOUCH.some((re) => re.test(String(s)));
}

/**
 * Cluster verdict per the fix-or-removed policy.
 *   cluster = {
 *     upstream: { gone, archived? },
 *     skills:   [{ name, found, errors }],   // one row per notified source-entry
 *   }
 * PASS only if the upstream exists AND every notified skill was found AND every
 * one has 0 validator errors at upstream HEAD. Anything else — deleted/private/
 * archived upstream, a missing skill, a partial pass — is FAIL.
 */
export function clusterVerdict(cluster) {
  const reasons = [];
  if (cluster.upstream?.gone) {
    reasons.push(
      cluster.upstream.archived
        ? 'upstream repo is archived'
        : 'upstream repo is deleted or private',
    );
    return { verdict: 'FAIL', reasons };
  }
  if (!cluster.skills || cluster.skills.length === 0) {
    return { verdict: 'FAIL', reasons: ['no notified skills resolvable at upstream HEAD'] };
  }
  for (const s of cluster.skills) {
    if (!s.found) reasons.push(`${s.name}: SKILL.md not found at upstream HEAD`);
    else if (s.errors > 0)
      reasons.push(`${s.name}: ${s.errors} validator error(s) at upstream HEAD`);
  }
  return reasons.length ? { verdict: 'FAIL', reasons } : { verdict: 'PASS', reasons: [] };
}

/**
 * Remove source entries from a sources.yaml text, leaving one dated NOTE
 * comment block per removal group at the position of its first removed entry.
 *   removals = [{ names: [entry names], noteLines: [plain text lines] }]
 * Entry blocks are the `  - name:` line plus following lines indented >= 4
 * (or blank); trailing blank lines stay so spacing survives. Returns
 * { text, removedNames }.
 */
export function buildSourcesRemoval(raw, removals) {
  const lines = raw.split('\n');
  const isEntryStart = (l) => /^ {2}- name:\s*\S/.test(l);
  const blocks = [];
  for (let i = 0; i < lines.length; i++) {
    if (!isEntryStart(lines[i])) continue;
    let end = i + 1;
    while (end < lines.length && (lines[end].trim() === '' || /^ {4,}/.test(lines[end]))) end++;
    while (end > i + 1 && lines[end - 1].trim() === '') end--; // leave trailing blanks in place
    blocks.push({ name: lines[i].replace(/^ {2}- name:\s*/, '').trim(), start: i, end });
  }
  const groupOf = new Map();
  removals.forEach((r, gi) => r.names.forEach((n) => groupOf.set(n, gi)));
  const keep = new Array(lines.length).fill(true);
  const inserts = new Map();
  const noteDone = new Set();
  const removedNames = [];
  for (const b of blocks) {
    const gi = groupOf.get(b.name);
    if (gi === undefined) continue;
    removedNames.push(b.name);
    for (let i = b.start; i < b.end; i++) keep[i] = false;
    if (!noteDone.has(gi)) {
      noteDone.add(gi);
      inserts.set(
        b.start,
        removals[gi].noteLines.map((l) => `  # ${l}`.trimEnd()),
      );
    }
  }
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    if (inserts.has(i)) out.push(...inserts.get(i));
    if (keep[i]) out.push(lines[i]);
  }
  // Collapse runs of blank lines left by the removals (prettier-yaml friendly).
  const collapsed = [];
  for (const l of out) {
    if (l.trim() === '' && collapsed.length && collapsed[collapsed.length - 1].trim() === '')
      continue;
    collapsed.push(l);
  }
  return { text: collapsed.join('\n'), removedNames };
}

/**
 * scan-allowlist.txt temp-line convention (see that file's comments): at most
 * ONE TEMPORARY sources-change-unscanned waiver may exist; each sources PR
 * swaps the previous PR's line(s) for its own scoped reason. Replaces every
 * existing `sources.yaml:`/`sources.lock.json:` sources-change-unscanned line
 * with `newLine` at the first one's position (appends if none existed).
 */
export function swapAllowlistTempLine(raw, newLine) {
  const lines = raw.split('\n');
  const isTemp = (l) => /^sources(\.yaml|\.lock\.json):sources-change-unscanned(\s|$)/.test(l);
  const firstIdx = lines.findIndex(isTemp);
  const kept = lines.filter((l) => !isTemp(l));
  if (firstIdx === -1) {
    while (kept.length && kept[kept.length - 1].trim() === '') kept.pop();
    kept.push('', newLine, '');
  } else {
    kept.splice(firstIdx, 0, newLine); // no temp line precedes firstIdx, so the index maps 1:1
  }
  return kept.join('\n');
}

/** Title matcher for the 2026-07-08 upstream notify issues. */
export function isNotifyIssueTitle(title) {
  return /2026-07-22|delist/i.test(String(title));
}

// ─────────────────────────────────────────────────────────────────────────────
// Enforce mode — impure helpers (gh / fs / subprocess).
// ─────────────────────────────────────────────────────────────────────────────

function ghJson(apiPath, extraArgs = []) {
  return JSON.parse(
    execFileSync('gh', ['api', apiPath, ...extraArgs], { encoding: 'utf8', maxBuffer: 64e6 }),
  );
}

/** The LIVE sources.yaml — origin/main via the API, independent of any local checkout state. */
function fetchLiveSourcesRaw() {
  const resp = ghJson(`repos/${MARKETPLACE_REPO}/contents/sources.yaml?ref=main`);
  return Buffer.from(resp.content, 'base64').toString('utf8');
}

function assertSaneRepoSlug(repo) {
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo)) {
    throw new Error(`refusing to act on malformed repo slug: ${JSON.stringify(repo)}`);
  }
}

/** Download + extract an upstream repo tarball at `ref`; returns the extracted root dir. */
function downloadUpstream(repo, ref, workDir) {
  assertSaneRepoSlug(repo);
  const tarPath = path.join(workDir, `${repo.replace('/', '__')}.tar.gz`);
  const outDir = path.join(workDir, repo.replace('/', '__'));
  fs.mkdirSync(outDir, { recursive: true });
  const tarball = execFileSync('gh', ['api', `repos/${repo}/tarball/${ref}`], {
    maxBuffer: 512e6,
  });
  fs.writeFileSync(tarPath, tarball);
  execFileSync('tar', ['-xzf', tarPath, '-C', outDir]);
  const entries = fs
    .readdirSync(outDir)
    .filter((e) => fs.statSync(path.join(outDir, e)).isDirectory());
  if (entries.length !== 1) throw new Error(`unexpected tarball layout for ${repo}: [${entries}]`);
  return path.join(outDir, entries[0]);
}

/** Locate the notified skill's SKILL.md(s) under sourcePath at upstream HEAD. */
function findSkillFiles(extractedRoot, sourcePath) {
  const base = path.join(extractedRoot, sourcePath);
  const direct = path.join(base, 'SKILL.md');
  try {
    if (fs.statSync(direct).isFile()) return [direct];
  } catch {
    /* fall through to the recursive search (upstream may have restructured) */
  }
  const found = [];
  const walk = (dir, depth) => {
    if (depth > 6) return;
    let items;
    try {
      items = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const it of items) {
      if (it.name === 'node_modules' || it.name === '.git') continue;
      const p = path.join(dir, it.name);
      if (it.isDirectory()) walk(p, depth + 1);
      else if (it.name === 'SKILL.md') found.push(p);
    }
  };
  walk(base, 0);
  return found.sort();
}

/** Run the marketplace validator on one SKILL.md; return its error count. */
function validateSkillFile(absPath) {
  const res = spawnSync('python3', [VALIDATOR, '--marketplace', '--json', absPath], {
    encoding: 'utf8',
    maxBuffer: 64e6,
  });
  // Non-zero exit is EXPECTED when the file has errors — read the JSON regardless.
  let parsed;
  try {
    parsed = JSON.parse(res.stdout);
  } catch {
    throw new Error(
      `validator produced no parseable JSON for ${absPath} (exit ${res.status}): ${String(
        res.stdout || res.stderr,
      ).slice(0, 300)}`,
    );
  }
  const fileRows = parsed.filter((r) => r && typeof r === 'object' && 'path' in r);
  if (fileRows.length === 0) throw new Error(`validator returned no file row for ${absPath}`);
  return fileRows.reduce((n, r) => n + (r.errors?.length || 0), 0);
}

/** Find the still-open 2026-07-08 notify issue we filed on an upstream repo. */
function findNotifyIssue(repo) {
  try {
    const issues = ghJson(
      `repos/${repo}/issues?state=open&creator=${MARKETPLACE_OWNER}&per_page=100`,
    );
    const hit = issues.find((i) => isNotifyIssueTitle(i.title));
    return hit ? { number: hit.number, url: hit.html_url, title: hit.title } : null;
  } catch {
    return null;
  }
}

/** Post a comment once (skips when the idempotency marker is already present). */
function ensureIssueComment(repoSlug, issueNumber, body) {
  const comments = ghJson(`repos/${repoSlug}/issues/${issueNumber}/comments?per_page=100`);
  if (comments.some((c) => (c.body || '').includes(COMMENT_MARKER))) return 'already-posted';
  execFileSync(
    'gh',
    ['api', '-X', 'POST', `repos/${repoSlug}/issues/${issueNumber}/comments`, '-f', `body=${body}`],
    { encoding: 'utf8' },
  );
  return 'posted';
}

function closeIssue(repoSlug, issueNumber) {
  try {
    execFileSync(
      'gh',
      ['api', '-X', 'PATCH', `repos/${repoSlug}/issues/${issueNumber}`, '-f', 'state=closed'],
      { encoding: 'utf8' },
    );
    return 'closed';
  } catch {
    return 'close-failed (left open)';
  }
}

function existingEnforcePR() {
  try {
    const prs = JSON.parse(
      execFileSync(
        'gh',
        [
          'pr',
          'list',
          '--repo',
          MARKETPLACE_REPO,
          '--head',
          ENFORCE_BRANCH,
          '--state',
          'all',
          '--json',
          'number,url,state',
        ],
        { encoding: 'utf8' },
      ),
    );
    return prs[0] || null;
  } catch {
    return null;
  }
}

function remoteBranchExists() {
  try {
    const out = execFileSync(
      'git',
      ['-C', REPO_ROOT, 'ls-remote', '--heads', 'origin', ENFORCE_BRANCH],
      { encoding: 'utf8' },
    );
    return out.trim().length > 0;
  } catch {
    return false;
  }
}

function run(cmd, args, opts = {}) {
  return execFileSync(cmd, args, { encoding: 'utf8', maxBuffer: 64e6, ...opts });
}

/**
 * Build the removal branch + PR in an isolated temp clone (the invoking
 * checkout is shared with other sessions and is never touched). Returns the PR URL.
 */
function buildRemovalPR({ failing, today, resultsTable }) {
  const cloneDir = fs.mkdtempSync(path.join(os.tmpdir(), 'census-removal-'));
  try {
    const originUrl = run('git', ['-C', REPO_ROOT, 'remote', 'get-url', 'origin']).trim();
    run('git', ['clone', '--quiet', '--depth', '50', '--branch', 'main', originUrl, cloneDir]);
    run('git', ['-C', cloneDir, 'checkout', '-q', '-b', ENFORCE_BRANCH]);

    // 1. sources.yaml — remove the failing clusters' entries, leave dated NOTEs.
    const srcPath = path.join(cloneDir, 'sources.yaml');
    const rawSources = fs.readFileSync(srcPath, 'utf8');
    const removals = failing.map((c) => ({
      names: c.sources.map((s) => s.name),
      noteLines: [
        `NOTE ${today}: ${c.sources.length} source(s) from ${c.repo} removed per the`,
        `2026-07-08 quality-census fix-or-removed policy (deadline ${DEADLINE}) — still failing`,
        `the marketplace validator at upstream HEAD ${c.upstream.headSha || '(gone)'}.`,
        `Notify issue: ${c.notifyIssue?.url || '(not found at enforcement time)'}`,
        `Re-listing is welcome once the skills pass scripts/validate-skills-schema.py --marketplace.`,
      ],
    }));
    const { text: newSources, removedNames } = buildSourcesRemoval(rawSources, removals);
    const expected = failing.reduce((n, c) => n + c.sources.length, 0);
    if (removedNames.length !== expected) {
      throw new Error(
        `sources.yaml removal mismatch: expected ${expected} entries, matched ${removedNames.length} — aborting before any write`,
      );
    }
    fs.writeFileSync(srcPath, newSources);
    run('python3', ['-c', 'import sys, yaml; yaml.safe_load(open(sys.argv[1]))', srcPath]);

    // 2. Mirror directories under plugins/.
    const removedDirs = [];
    for (const c of failing) {
      for (const s of c.sources) {
        if (!s.targetPath.startsWith('plugins/')) {
          throw new Error(`refusing to delete non-plugins path: ${s.targetPath}`);
        }
        const abs = path.join(cloneDir, s.targetPath);
        if (fs.existsSync(abs)) {
          fs.rmSync(abs, { recursive: true });
          removedDirs.push(s.targetPath);
        }
      }
    }

    // 3. Catalog entries (marketplace.extended.json) for the removed mirrors —
    //    required, or validate-catalog-invariants.py fails the PR.
    const extPath = path.join(cloneDir, '.claude-plugin', 'marketplace.extended.json');
    const ext = JSON.parse(fs.readFileSync(extPath, 'utf8'));
    const removedSourceSet = new Set(
      failing.flatMap((c) => c.sources.map((s) => `./${s.targetPath}`)),
    );
    const beforeCount = ext.plugins.length;
    ext.plugins = ext.plugins.filter((p) => !removedSourceSet.has(p.source));
    const removedCatalog = beforeCount - ext.plugins.length;
    fs.writeFileSync(extPath, JSON.stringify(ext, null, 2) + '\n');

    // 4. Derived artifacts. sync-marketplace.cjs needs the kernel and
    //    generate-readme-toc.mjs needs prettier — reuse the invoking checkout's
    //    node_modules (same commit family), else install fresh.
    const localNM = path.join(REPO_ROOT, 'node_modules');
    const cloneNM = path.join(cloneDir, 'node_modules');
    if (fs.existsSync(path.join(localNM, '@intentsolutions', 'core'))) {
      fs.symlinkSync(localNM, cloneNM, 'dir');
    } else {
      run('pnpm', ['install', '--frozen-lockfile', '--filter', 'claude-code-plugins-monorepo'], {
        cwd: cloneDir,
      });
    }
    const prettierBin = path.join(cloneNM, '.bin', 'prettier');
    run(prettierBin, ['--write', extPath], { cwd: cloneDir });
    run('node', [path.join(cloneDir, 'scripts', 'sync-marketplace.cjs')], { cwd: cloneDir });
    run('node', [path.join(cloneDir, 'scripts', 'generate-plugin-package-jsons.mjs')], {
      cwd: cloneDir,
    });
    run('node', [path.join(cloneDir, 'scripts', 'generate-readme-toc.mjs')], { cwd: cloneDir });

    // 5. scan-allowlist.txt — swap the TEMPORARY sources-change-unscanned line
    //    for this PR's scoped reason (one temp line max, per that file's rules).
    const allowPath = path.join(cloneDir, 'scripts', 'scan-allowlist.txt');
    const failRepos = failing.map((c) => c.repo).join(', ');
    fs.writeFileSync(
      allowPath,
      swapAllowlistTempLine(
        fs.readFileSync(allowPath, 'utf8'),
        `sources.yaml:sources-change-unscanned  ${today} census-deadline enforcement PR: removes the still-failing census clusters (${failRepos}) per the 2026-07-08 fix-or-removed policy — every notified skill re-validated at upstream default-branch HEAD by census-watch --enforce before removal; entries removed only, no source added or repointed`,
      ),
    );

    // 6. Gate the tree the same way CI will: sources.yaml must stay prettier-clean.
    const check = spawnSync(prettierBin, ['--check', 'sources.yaml'], {
      cwd: cloneDir,
      encoding: 'utf8',
    });
    if (check.status !== 0) {
      run(prettierBin, ['--write', 'sources.yaml'], { cwd: cloneDir });
      run(prettierBin, ['--check', 'sources.yaml'], { cwd: cloneDir }); // throws if still dirty
    }

    // Drop the node_modules symlink before committing (gitignored, but be explicit).
    try {
      fs.unlinkSync(cloneNM);
    } catch {
      /* real dir from pnpm install — gitignored, leave it */
    }

    // 7. ONE commit + push + ONE PR. NEVER merged by automation — Jeremy merges.
    const removedEntries = removedNames.length;
    const commitMsg = [
      `fix(census): remove ${removedEntries} still-failing source entries at the ${DEADLINE} census deadline`,
      '',
      `The 2026-07-08 whole-catalog quality census put these sources on a fix-or-removed`,
      `clock (notify issues filed upstream, deadline ${DEADLINE}). census-watch --enforce`,
      `re-validated every notified skill at upstream default-branch HEAD with`,
      `validate-skills-schema.py --marketplace on ${today}; these clusters still fail, so their`,
      `sources.yaml entries (dated NOTE comments left in place), mirror dirs under plugins/,`,
      `and catalog entries are removed. Derived artifacts regenerated via sync-marketplace.`,
      `Re-listing is welcome once the skills pass the validator.`,
      '',
      `Clusters removed: ${failRepos}`,
      '',
      SIGNATURE,
    ].join('\n');
    run('git', ['-C', cloneDir, 'add', '-A']);
    run('git', ['-C', cloneDir, 'commit', '-q', '-m', commitMsg]);
    run('git', ['-C', cloneDir, 'push', '-q', 'origin', `HEAD:refs/heads/${ENFORCE_BRANCH}`]);

    const prBody = [
      '## DO NOT MERGE — human review required (Jeremy merges)',
      '',
      `Automated census-deadline enforcement (\`scripts/census-watch.mjs --enforce\`, fired ${today}).`,
      `The 2026-07-08 quality census set a fix-or-removed deadline of ${DEADLINE}; per the`,
      'owner-set policy, external authors fix their own content or their listing is removed —',
      'we never fix it for them. Every notified skill was re-validated at UPSTREAM',
      'default-branch HEAD (`validate-skills-schema.py --marketplace --json`) before removal;',
      'the live sources.yaml delist clock was read at run time, so anything fixed or already',
      'removed since notify day is untouched.',
      '',
      '### Results at upstream HEAD',
      '',
      resultsTable,
      '',
      '### What this PR does (one commit)',
      '',
      `- Removes ${removedEntries} \`sources.yaml\` entries (${failing.length} cluster(s)) with dated NOTE comments (notify-issue link + re-listing-welcome).`,
      `- Deletes ${removedDirs.length} mirror dir(s) under \`plugins/\`.`,
      `- Drops ${removedCatalog} catalog entries from \`marketplace.extended.json\` and regenerates the derived artifacts (\`marketplace.json\`, plugin package.jsons, README AUTO-TOC) so \`validate-catalog-invariants.py\` stays green.`,
      "- Swaps the TEMPORARY `sources-change-unscanned` line in `scripts/scan-allowlist.txt` for this PR's scoped reason (per that file's one-temp-line convention).",
      '- `sources.yaml` validated with `yaml.safe_load` + prettier-checked.',
      '',
      'Sources are removed, never edited — re-listing is welcome once the skills pass the',
      'marketplace validator. `sources.lock.json` entries for removed sources become inert',
      'and can be pruned by the next `--relock` (left untouched here to keep the lock canonical).',
      '',
      '[skip auto-bump]',
      '',
      SIGNATURE,
    ].join('\n');
    const prUrl = run(
      'gh',
      [
        'pr',
        'create',
        '--repo',
        MARKETPLACE_REPO,
        '--base',
        'main',
        '--head',
        ENFORCE_BRANCH,
        '--title',
        `fix(census): remove still-failing census clusters at the ${DEADLINE} deadline [skip auto-bump]`,
        '--body',
        prBody,
      ],
      { cwd: cloneDir },
    ).trim();
    return { prUrl, removedEntries, removedDirs, removedCatalog };
  } finally {
    fs.rmSync(cloneDir, { recursive: true, force: true });
  }
}

function renderResultsTable(clusters) {
  const rows = [
    '| Cluster (upstream) | Notified skills | Found at HEAD | Errors at HEAD | Verdict |',
    '|---|---|---|---|---|',
  ];
  for (const c of clusters) {
    const found = c.skills.filter((s) => s.found).length;
    const errs = c.skills.reduce((n, s) => n + (s.errors || 0), 0);
    const verdict =
      c.verdict === 'PASS' ? 'PASS — listing retained' : `FAIL — ${c.reasons[0] || 'removed'}`;
    rows.push(
      `| ${c.repo}${c.upstream.headSha ? ` @ \`${c.upstream.headSha}\`` : ''} | ${c.skills.length} | ${found} | ${errs} | ${verdict} |`,
    );
  }
  return rows.join('\n');
}

/**
 * The enforcement run. Read-only when dryRun; otherwise builds the removal PR,
 * posts the #984 results comment, and closes the still-open notify issues.
 */
function runEnforce({ dryRun }) {
  const say = (msg) => (JSON_OUT ? console.error(msg) : console.log(msg));
  const now = new Date();
  const today = now.toISOString().slice(0, 10);
  const daysLeft = daysLeftAt(now);

  if (!dryRun && !enforcementDue(now)) {
    console.error(
      `census-watch --enforce: refusing to run live enforcement before the deadline has passed ` +
        `(${DEADLINE}, ${daysLeft} day(s) left). Use --dry-run for a read-only rehearsal.`,
    );
    process.exit(2);
  }

  say(`\n  Census-deadline enforcement${dryRun ? ' (DRY RUN — read-only)' : ''}`);
  say(`  policy: fix-or-removed · deadline ${DEADLINE} · days left ${daysLeft}`);

  // LIVE clock: sources.yaml on origin/main at run time — never a frozen list.
  const liveRaw = fetchLiveSourcesRaw();
  const allEntries = parseOnClockSources(liveRaw);
  const entries = [];
  for (const e of allEntries) {
    if (isNeverTouch(e.repo) || isNeverTouch(e.name)) {
      say(`  SKIP (never-touch guard): ${e.name} (${e.repo})`);
      continue;
    }
    entries.push(e);
  }
  say(
    `  live delist clock: ${entries.length} source-entries across ${new Set(entries.map((e) => e.repo)).size} upstream repo(s)\n`,
  );

  const result = {
    mode: dryRun ? 'enforce-dry-run' : 'enforce',
    ok: true,
    generatedAt: now.toISOString(),
    deadline: DEADLINE,
    daysLeft,
    clusters: [],
    actions: { pr: null, prExisted: false, resultsComment: null, notifyIssues: [] },
    slackSummary: '',
  };

  if (entries.length === 0) {
    say(
      '  The delist clock is EMPTY — every census source was fixed or already removed. Nothing to enforce.',
    );
    if (!dryRun) {
      const body = `${COMMENT_MARKER}\n**Census-deadline enforcement (${DEADLINE}) — clock empty.** At enforcement time the live \`sources.yaml\` carried zero delist-clock entries: every 2026-07-08 census source was either fixed upstream or already removed. No removal PR needed.\n\n${SIGNATURE}`;
      result.actions.resultsComment = ensureIssueComment(MARKETPLACE_REPO, RESULTS_ISSUE, body);
      fs.mkdirSync(STATE_DIR, { recursive: true });
      fs.writeFileSync(ENFORCE_RESULT_FILE, JSON.stringify(result, null, 2) + '\n');
    }
    result.slackSummary = 'census clock empty — nothing to enforce; #984 updated';
    if (JSON_OUT) console.log(JSON.stringify(result, null, 2));
    return;
  }

  // Group into clusters by upstream repo and validate at upstream HEAD.
  const byRepo = new Map();
  for (const e of entries) {
    if (!byRepo.has(e.repo)) byRepo.set(e.repo, []);
    byRepo.get(e.repo).push(e);
  }

  const workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'census-enforce-'));
  const clusters = [];
  try {
    for (const [repo, sources] of [...byRepo.entries()].sort()) {
      say(`  validating ${repo} (${sources.length} skill(s)) at upstream HEAD ...`);
      const upstream = upstreamHead(repo);
      const skills = [];
      if (!upstream.gone) {
        const root = downloadUpstream(repo, upstream.headSha || upstream.defaultBranch, workDir);
        for (const s of sources) {
          const files = findSkillFiles(root, s.sourcePath);
          if (files.length === 0) {
            skills.push({ name: s.name, found: false, errors: null });
            say(`      ${s.name}: SKILL.md NOT FOUND under ${s.sourcePath}/`);
          } else {
            const errors = files.reduce((n, f) => n + validateSkillFile(f), 0);
            skills.push({ name: s.name, found: true, errors });
            say(`      ${s.name}: ${errors} error(s)`);
          }
        }
      } else {
        say(`      upstream GONE${upstream.archived ? ' (archived)' : ' (deleted/private)'}`);
      }
      const { verdict, reasons } = clusterVerdict({ upstream, skills });
      const notifyIssue = findNotifyIssue(repo);
      clusters.push({ repo, sources, upstream, skills, verdict, reasons, notifyIssue });
      say(`    → ${verdict}${reasons.length ? ` (${reasons.length} reason(s))` : ''}\n`);
    }
  } finally {
    fs.rmSync(workDir, { recursive: true, force: true });
  }

  const failing = clusters.filter((c) => c.verdict === 'FAIL');
  const passing = clusters.filter((c) => c.verdict === 'PASS');
  const resultsTable = renderResultsTable(clusters);
  result.clusters = clusters.map((c) => ({
    repo: c.repo,
    verdict: c.verdict,
    reasons: c.reasons,
    headSha: c.upstream.headSha || null,
    skills: c.skills,
    sources: c.sources.map((s) => s.name),
    notifyIssue: c.notifyIssue?.url || null,
  }));

  say(`  VERDICTS: ${passing.length} PASS / ${failing.length} FAIL`);
  say(resultsTable.replace(/^/gm, '  '));

  if (dryRun) {
    const wouldRemove = failing.flatMap((c) => c.sources.map((s) => s.name));
    say(
      `\n  DRY RUN — would remove ${wouldRemove.length} source entr(ies) across ${failing.length} cluster(s):`,
    );
    for (const c of failing) {
      say(
        `    ${c.repo}: ${c.sources.length} entries + ${c.sources.length} mirror dir(s); notify issue ${c.notifyIssue?.url || '(not found)'}`,
      );
    }
    say(
      `  Would open ONE PR on branch ${ENFORCE_BRANCH} (DO NOT MERGE), comment on #${RESULTS_ISSUE},`,
    );
    say(`  and post a closing comment on each still-open notify issue. No side effects taken.\n`);
    result.slackSummary = `dry-run: ${failing.length} cluster(s) would be removed (${wouldRemove.length} sources), ${passing.length} would pass`;
    if (JSON_OUT) console.log(JSON.stringify(result, null, 2));
    return;
  }

  // ── LIVE side effects ──────────────────────────────────────────────────────
  // Idempotency: one branch, one PR, ever. Detect + reuse, never duplicate.
  const prior = existingEnforcePR();
  if (failing.length > 0) {
    if (prior) {
      say(`  Removal PR already exists (${prior.url}, ${prior.state}) — not duplicating.`);
      result.actions.pr = prior.url;
      result.actions.prExisted = true;
    } else if (remoteBranchExists()) {
      say(
        `  Branch ${ENFORCE_BRANCH} already exists on origin without a PR — not rebuilding; open the PR manually or delete the branch and rerun.`,
      );
      result.actions.pr = null;
      result.actions.prExisted = true;
    } else {
      const { prUrl } = buildRemovalPR({ failing, today, resultsTable });
      say(`  Opened removal PR: ${prUrl}  (DO NOT MERGE — Jeremy merges)`);
      result.actions.pr = prUrl;
    }
  } else {
    say('  Every cluster PASSED — no removal PR needed.');
  }

  // Results comment on the census tracking issue.
  const prLine = result.actions.pr
    ? `\n\nRemoval PR: ${result.actions.pr} — **DO NOT MERGE without review** (Jeremy merges).`
    : failing.length === 0
      ? '\n\nEvery cluster passed at upstream HEAD — **no removal PR needed**.'
      : '';
  const resultsBody = `${COMMENT_MARKER}\n**Census-deadline enforcement (${DEADLINE}) — results at upstream default-branch HEAD** (\`census-watch.mjs --enforce\`, ${today}; live \`sources.yaml\` clock, validator \`--marketplace\`)\n\n${resultsTable}${prLine}\n\n${SIGNATURE}`;
  result.actions.resultsComment = ensureIssueComment(MARKETPLACE_REPO, RESULTS_ISSUE, resultsBody);
  say(`  #${RESULTS_ISSUE} results comment: ${result.actions.resultsComment}`);

  // One short closing comment per still-open notify issue.
  for (const c of clusters) {
    if (!c.notifyIssue) {
      result.actions.notifyIssues.push({ repo: c.repo, status: 'no-open-notify-issue' });
      continue;
    }
    const body =
      c.verdict === 'PASS'
        ? `${COMMENT_MARKER}\nVerified at the ${DEADLINE} deadline: the notified skills now pass the marketplace validator at your default-branch HEAD — thank you for fixing them. The listing stays live. Closing this out.\n\n${SIGNATURE}`
        : `${COMMENT_MARKER}\nThe ${DEADLINE} deadline passed with the notified skills still failing the marketplace validator at your default-branch HEAD, so the listing has been removed per the fix-or-removed policy (removal PR: ${result.actions.pr || 'pending'}). Re-listing is welcome any time once the skills pass — just open an issue or PR on the marketplace repo. Closing this out.\n\n${SIGNATURE}`;
    const posted = ensureIssueComment(c.repo, c.notifyIssue.number, body);
    const closed =
      posted === 'posted' ? closeIssue(c.repo, c.notifyIssue.number) : 'already-handled';
    result.actions.notifyIssues.push({
      repo: c.repo,
      issue: c.notifyIssue.url,
      comment: posted,
      close: closed,
    });
    say(`  notify issue ${c.notifyIssue.url}: comment ${posted}, ${closed}`);
  }

  result.slackSummary =
    failing.length === 0
      ? `all ${clusters.length} census cluster(s) PASSED at upstream HEAD — no removals; #${RESULTS_ISSUE} updated`
      : `${failing.length} cluster(s) removed (${failing.reduce((n, c) => n + c.sources.length, 0)} sources) via ${result.actions.pr || 'existing PR/branch'} — DO NOT MERGE without review; ${passing.length} passed; #${RESULTS_ISSUE} + notify issues updated`;

  fs.mkdirSync(STATE_DIR, { recursive: true });
  fs.writeFileSync(ENFORCE_RESULT_FILE, JSON.stringify(result, null, 2) + '\n');
  say(`\n  Enforcement complete. Result: ${ENFORCE_RESULT_FILE}\n`);
  if (JSON_OUT) console.log(JSON.stringify(result, null, 2));
}

// ─────────────────────────────────────────────────────────────────────────────
// Watch mode (the original daily report — unchanged behavior).
// ─────────────────────────────────────────────────────────────────────────────

function main() {
  const sources = onClockSources();
  // repo -> [source names]
  const byRepo = new Map();
  for (const s of sources) {
    if (!byRepo.has(s.repo)) byRepo.set(s.repo, []);
    byRepo.get(s.repo).push(s.name);
  }

  // Read prior state by attempting the read directly (no existsSync check first) —
  // an existsSync-then-readFileSync pair is a time-of-check/time-of-use race (CWE-367).
  let prev = { repos: {} };
  let firstRun = true;
  try {
    prev = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    firstRun = false;
  } catch {
    // No readable prior state (file missing or unparseable) → treat as first run.
  }

  const now = new Date();
  const daysLeft = daysLeftAt(now);

  const results = [];
  for (const [repo, names] of [...byRepo.entries()].sort()) {
    const info = upstreamHead(repo);
    const cls = classify(info);
    const before = prev.repos[repo];
    let delta;
    if (firstRun || !before) delta = 'init';
    else if (before.headSha !== info.headSha) delta = 'CHANGED-since-last-run';
    else delta = 'same';
    results.push({
      repo,
      sources: names,
      class: cls,
      headSha: info.headSha || null,
      headDate: info.headDate || null,
      delta,
    });
  }

  const state = {
    generatedAt: now.toISOString(),
    censusDate: CENSUS_DATE,
    deadline: DEADLINE,
    daysLeft,
    repos: Object.fromEntries(
      results.map((r) => [r.repo, { headSha: r.headSha, headDate: r.headDate, class: r.class }]),
    ),
  };
  fs.mkdirSync(STATE_DIR, { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2) + '\n');

  if (JSON_OUT) {
    console.log(JSON.stringify({ ...state, results }, null, 2));
    return;
  }

  const moved = results.filter((r) => r.class === 'MOVED');
  const dormant = results.filter((r) => r.class === 'DORMANT');
  const gone = results.filter((r) => r.class.startsWith('GONE'));
  const changed = results.filter((r) => r.delta === 'CHANGED-since-last-run');

  const sourceCount = sources.length;
  console.log(
    `\n  Census watch — ${CENSUS_DATE} D/F cohort · delist deadline ${DEADLINE} (${daysLeft} days left)`,
  );
  console.log(`  ${sourceCount} source-entries on the clock across ${byRepo.size} upstream repos`);
  console.log(`  state: ${STATE_FILE}${firstRun ? '  (initialized this run)' : ''}\n`);

  const pad = (s, n) => String(s).padEnd(n);
  console.log(
    `  ${pad('UPSTREAM REPO', 34)}${pad('CLASS', 15)}${pad('HEAD DATE', 22)}${pad('Δ', 10)}SOURCES`,
  );
  console.log(`  ${'-'.repeat(96)}`);
  for (const r of results) {
    console.log(
      `  ${pad(r.repo, 34)}${pad(r.class, 15)}${pad((r.headDate || '—').slice(0, 19), 22)}${pad(r.delta === 'init' ? 'init' : r.delta === 'same' ? '·' : '⚑ NEW', 10)}${r.sources.join(', ')}`,
    );
  }

  console.log(`\n  SUMMARY`);
  console.log(
    `   • ${moved.length} upstream(s) MOVED since ${CENSUS_DATE} → RE-GRADE candidates (a fix may have landed):`,
  );
  moved.forEach((r) =>
    console.log(`       ${r.repo}  (${r.sources.length} skill(s): ${r.sources.join(', ')})`),
  );
  console.log(
    `   • ${dormant.length} upstream(s) DORMANT → DELIST candidates on ${DEADLINE} unless re-graded:`,
  );
  dormant.forEach((r) =>
    console.log(`       ${r.repo}  (${r.sources.length} skill(s): ${r.sources.join(', ')})`),
  );
  if (gone.length) {
    console.log(`   • ${gone.length} upstream(s) GONE → auto-delist:`);
    gone.forEach((r) => console.log(`       ${r.repo}  [${r.class}]`));
  }
  if (!firstRun && changed.length) {
    console.log(`   • ${changed.length} upstream(s) CHANGED since last watch → re-grade now:`);
    changed.forEach((r) => console.log(`       ${r.repo}`));
  }
  console.log(
    `\n  Next: re-grade the MOVED upstreams (validator), flip verified:true on any that now pass,`,
  );
  console.log(
    `  and on ${DEADLINE} delist whatever is still DORMANT/failing (bead claude-ss50.8).\n`,
  );
}

// Entry guard: only dispatch when executed directly (the fixture tests in
// census-watch.test.mjs import this module and must not trigger a run).
const isEntry = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isEntry) {
  if (ENFORCE) runEnforce({ dryRun: DRY_RUN });
  else main();
}
