#!/usr/bin/env node
/**
 * check-capability-coverage.mjs — every tool token in the corpus maps to an
 * abstract capability (blueprint 727, Epic 3 bead 3.3).
 *
 * Sweeps every tracked SKILL.md and agent definition, parses the four
 * tool-list fields (`allowed-tools`, `disallowed-tools` on skills; `tools`,
 * `disallowedTools` on agents) with a REAL YAML parser, tokenizes through the
 * single shared parser (scripts/lib/tool-token-parser.mjs), and asserts:
 *
 *   builtin     → must be a key in capability-map.json `builtins`
 *   mcp         → covered by the `shapes.mcp` rule
 *   namespaced  → covered by the `shapes.namespaced` rule
 *   unknown     → must appear in `dispositions.tolerated` with a reason;
 *                 otherwise this gate FAILS, naming file and token
 *
 * Frontmatter that js-yaml cannot parse is skipped here — structural
 * frontmatter validity is the schema validator's jurisdiction (E1.11 made an
 * unparseable allowlist an ERROR there); this gate owns vocabulary coverage,
 * not YAML hygiene, and double-reporting the same defect creates two owners
 * for one fact.
 */

import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import yaml from 'js-yaml';
import { parseTokenList } from './lib/tool-token-parser.mjs';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');

const MAP = JSON.parse(
  readFileSync(join(ROOT, 'schemas', 'canonical', 'v0', 'capability-map.json'), 'utf-8'),
);

const FIELDS = ['allowed-tools', 'disallowed-tools', 'tools', 'disallowedTools'];

export function coverageForFrontmatter(fm, map = MAP) {
  const uncovered = [];
  const counts = { builtin: 0, mcp: 0, namespaced: 0, tolerated: 0 };
  for (const field of FIELDS) {
    if (!(field in (fm ?? {}))) continue;
    for (const token of parseTokenList(fm[field])) {
      if (token.kind === 'builtin') {
        if (map.builtins[token.name]) counts.builtin += 1;
        else
          uncovered.push({
            field,
            raw: token.raw,
            why: `builtin "${token.name}" not in capability map`,
          });
      } else if (token.kind === 'mcp' || token.kind === 'namespaced') {
        counts[token.kind] += 1;
      } else if (map.dispositions?.tolerated?.[token.raw]) {
        counts.tolerated += 1;
      } else {
        uncovered.push({ field, raw: token.raw, why: 'unknown token with no disposition' });
      }
    }
  }
  return { uncovered, counts };
}

function trackedTargets() {
  const files = execFileSync('git', ['ls-files'], {
    cwd: ROOT,
    encoding: 'utf-8',
    maxBuffer: 256 * 1024 * 1024,
  })
    .split('\n')
    .filter(Boolean);
  return files.filter(
    (f) =>
      /(^|\/)SKILL\.md$/.test(f) ||
      (f.startsWith('plugins/') && /\/agents\/[^/]+\.md$/.test(f)) ||
      /^\.claude\/agents\/[^/]+\.md$/.test(f),
  );
}

export function sweep() {
  const violations = [];
  const totals = { files: 0, bearing: 0, tokens: 0, unparseableFrontmatter: 0 };
  for (const file of trackedTargets()) {
    totals.files += 1;
    let text;
    try {
      text = readFileSync(join(ROOT, file), 'utf-8');
    } catch {
      continue;
    }
    const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!m) continue;
    let fm;
    try {
      fm = yaml.load(m[1]);
    } catch {
      totals.unparseableFrontmatter += 1; // the validator's jurisdiction
      continue;
    }
    if (!fm || typeof fm !== 'object') continue;
    if (!FIELDS.some((f) => f in fm)) continue;
    totals.bearing += 1;
    const { uncovered, counts } = coverageForFrontmatter(fm);
    totals.tokens +=
      counts.builtin + counts.mcp + counts.namespaced + counts.tolerated + uncovered.length;
    for (const u of uncovered) violations.push({ file, ...u });
  }
  return { violations, totals };
}

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
  const { violations, totals } = sweep();
  for (const v of violations) {
    console.error(`capability-coverage: VIOLATION — ${v.file} [${v.field}] "${v.raw}": ${v.why}`);
  }
  if (violations.length > 0) {
    console.error(
      `capability-coverage: FAIL — ${violations.length} uncovered token(s). Map the builtin, or add a dispositions.tolerated entry with a reason.`,
    );
    process.exit(1);
  }
  console.log(
    `capability-coverage: OK (${totals.bearing} allowlist-bearing files of ${totals.files}; ${totals.tokens} tokens all covered; ${totals.unparseableFrontmatter} unparseable frontmatter left to the validator)`,
  );
}
