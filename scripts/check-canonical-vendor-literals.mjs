#!/usr/bin/env node
/**
 * check-canonical-vendor-literals.mjs — no Claude-specific token may appear in
 * the harness-free core (blueprint 727, Epic 3 bead 3.10).
 *
 * Migration must be falsifiable (§ 5.4 rule 3): without this gate, vendor
 * drift returns within one generation cycle. The CANONICAL LAYER is:
 *
 *   - every `skill-card.yaml` in the tree (home B of the § 5.1 split)
 *   - every file under a plugin's `canonical/` directory (future bodies)
 *
 * In a canonical-layer file this gate FAILS on:
 *   1. a concrete model id        (claude-sonnet-4, … — via THE shared
 *                                  classifier; bead handles stay protected)
 *   2. a harness-branded variable (${CLAUDE_*})
 *   3. an MCP tool spelling       (mcp__server__tool)
 *   4. harness tool scoping       (Bash(...), or any Builtin(...) form)
 *   5. a harness denylist field   (disallowedTools / disallowed-tools)
 *
 * EXEMPT BY DESIGN (the translation layer, where harness tokens are the
 * subject matter, not drift): `scripts/adapters/`, and the v0 contract
 * documentation set (`schemas/canonical/v0/`) whose schema comments and
 * README cite harness spellings as counter-examples.
 */

import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { MODEL_ID, classifyModelToken } from './lib/model-id-classifier.mjs';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');

export function isCanonicalLayer(path) {
  if (path.startsWith('scripts/adapters/')) return false;
  if (path.startsWith('schemas/canonical/v0/')) return false;
  return (
    path.endsWith('/skill-card.yaml') ||
    path === 'skill-card.yaml' ||
    /(^|\/)canonical\//.test(path)
  );
}

const RULES = [
  {
    kind: 'harness-variable',
    re: /\$\{CLAUDE_[A-Z_]+\}/,
    why: 'canonical text uses the portable ${SKILL_DIR} family; the adapter emits the branded form',
  },
  {
    kind: 'mcp-spelling',
    re: /\bmcp__[A-Za-z0-9_-]+/,
    why: 'canonical declares requires.services[{kind: mcp, name}] — never the harness tool spelling',
  },
  {
    kind: 'tool-scoping',
    re: /\b[A-Z][A-Za-z]*\([^)]*\)/,
    why: 'canonical declares abstract capabilities — Bash(...)-style scoping is the adapter map',
  },
  {
    kind: 'denylist-field',
    re: /\bdisallowed[-_ ]?[Tt]ools\b/,
    why: 'canonical carries constraints.forbid — the denylist spelling is per-harness',
  },
];

export function scanCanonicalText(path, text) {
  const violations = [];
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    for (const rule of RULES) {
      const m = line.match(rule.re);
      if (m) violations.push({ path, line: i + 1, kind: rule.kind, token: m[0], why: rule.why });
    }
    for (const token of line.match(MODEL_ID) || []) {
      if (classifyModelToken(token, line) !== 'bead-id') {
        violations.push({
          path,
          line: i + 1,
          kind: 'model-literal',
          token,
          why: 'canonical carries model_class tiers — a concrete model id is vendor lock-in relocated',
        });
      }
    }
  }
  return violations;
}

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
  const files = execFileSync('git', ['ls-files'], {
    cwd: ROOT,
    encoding: 'utf-8',
    maxBuffer: 256 * 1024 * 1024,
  })
    .split('\n')
    .filter(Boolean);
  const targets = files.filter(isCanonicalLayer);
  const violations = [];
  for (const f of targets) {
    let text;
    try {
      text = readFileSync(join(ROOT, f), 'utf-8');
    } catch {
      continue;
    }
    violations.push(...scanCanonicalText(f, text));
  }
  for (const v of violations) {
    console.error(
      `canonical-vendor-literals: VIOLATION (${v.kind}) — ${v.path}:${v.line} "${v.token}": ${v.why}`,
    );
  }
  if (violations.length > 0) {
    console.error(`canonical-vendor-literals: FAIL — ${violations.length} violation(s).`);
    process.exit(1);
  }
  console.log(
    `canonical-vendor-literals: OK (${targets.length} canonical-layer file(s) scanned; zero vendor literals)`,
  );
}
