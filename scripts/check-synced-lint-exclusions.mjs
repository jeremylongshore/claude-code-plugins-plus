#!/usr/bin/env node
/**
 * check-synced-lint-exclusions.mjs
 *
 * Every external-synced plugin (a dir carrying a `.source.json` marker) is a
 * mirror of upstream code and must NOT be held to this repo's markdown / Python
 * lint style — otherwise the sync PR red-fails markdownlint / ruff on content
 * the next sync overwrites anyway (the bug that blocked the beads-dolt sync).
 *
 * This gate asserts every synced dir is excluded in BOTH:
 *   - .markdownlint-cli2.jsonc  (the `ignores` array, as `<dir>/**`)
 *   - ruff.toml                 (the `extend-exclude` array, as `<dir>`)
 * and fails with the exact lines to add when one drifts. It only ever reports
 * MISSING exclusions — it never rewrites the configs, so it is safe to run in
 * CI and cannot clobber hand-maintained entries.
 *
 * Usage: node scripts/check-synced-lint-exclusions.mjs   (exit 1 on drift)
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const syncedDirs = execFileSync(
  'bash',
  ['-c', 'find plugins -maxdepth 3 -name .source.json -exec dirname {} \\;'],
  { cwd: ROOT },
)
  .toString()
  .trim()
  .split('\n')
  .filter(Boolean)
  .sort();

const md = fs.readFileSync(path.join(ROOT, '.markdownlint-cli2.jsonc'), 'utf8');
const ruff = fs.readFileSync(path.join(ROOT, 'ruff.toml'), 'utf8');

const missingMd = syncedDirs.filter((d) => !md.includes(`"${d}/**"`));
const missingRuff = syncedDirs.filter((d) => !ruff.includes(`"${d}"`));

if (missingMd.length === 0 && missingRuff.length === 0) {
  console.log(`✓ all ${syncedDirs.length} synced plugins are excluded from markdownlint + ruff`);
  process.exit(0);
}

console.error('✗ synced-plugin lint-exclusion drift detected:\n');
if (missingMd.length) {
  console.error('  Add to the "ignores" array in .markdownlint-cli2.jsonc:');
  missingMd.forEach((d) => console.error(`    "${d}/**",`));
  console.error('');
}
if (missingRuff.length) {
  console.error('  Add to "extend-exclude" in ruff.toml:');
  missingRuff.forEach((d) => console.error(`    "${d}",`));
  console.error('');
}
console.error('These dirs carry a .source.json (external-synced) marker; their mirrored');
console.error("markdown/python must be excluded from this repo's lint gates.");
process.exit(1);
