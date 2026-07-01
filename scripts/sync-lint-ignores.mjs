#!/usr/bin/env node
/**
 * sync-lint-ignores.mjs
 *
 * Every external-synced plugin (a dir carrying a `.source.json` marker) is a
 * mirror of upstream code and must NOT be held to this repo's markdown / Python
 * lint style — otherwise the sync PR red-fails markdownlint / ruff on content
 * the next sync overwrites anyway (the bug that blocked the beads-dolt sync).
 *
 * This generator DERIVES the synced-plugin lint-exclusion lists in BOTH:
 *   - .markdownlint-cli2.jsonc  (the `ignores` array, as `"<dir>/**"`)
 *   - ruff.toml                 (the `extend-exclude` array, as `"<dir>"`)
 * from the discovered set of `.source.json`-marked dirs, so a newly-synced
 * source self-registers instead of requiring a hand-edit.
 *
 * markdownlint-cli2 has no real `--ignore` CLI flag, so the config `ignores`
 * array is the only authoritative exclusion surface; likewise ruff's config
 * `extend-exclude`. These configs are what CI runs against — keeping them
 * derived (not hand-maintained) is the whole point.
 *
 * ── Sentinel contract ─────────────────────────────────────────────────────
 * The generator manages ONLY the text between a BEGIN/END sentinel pair in
 * each config. Everything outside the sentinels (manual entries, explanatory
 * comments, the array close) is untouched — so hand-maintained entries can
 * never be clobbered. Every managed entry carries a trailing comma (both JSONC
 * and TOML tolerate a trailing comma before the closing bracket, and the END
 * sentinel comment sits between the last entry and the `]`), which removes the
 * last-entry-no-comma special case. Do not hand-edit between the sentinels —
 * run this script.
 *
 * Discovery is identical to the check it supersedes:
 *   find plugins -maxdepth 3 -name .source.json -exec dirname {} \;
 *
 * Usage:
 *   node scripts/sync-lint-ignores.mjs           # WRITE mode — canonicalize
 *                                                 # the managed blocks in place
 *   node scripts/sync-lint-ignores.mjs --check    # CI drift gate — exit 1 if
 *                                                 # either file WOULD change,
 *                                                 # printing the fix command
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CHECK = process.argv.includes('--check');
const FIX_CMD = 'node scripts/sync-lint-ignores.mjs';

// ── Discovery — identical to the superseded check ─────────────────────────
const syncedDirs = [
  ...new Set(
    execFileSync(
      'bash',
      ['-c', 'find plugins -maxdepth 3 -name .source.json -exec dirname {} \\;'],
      { cwd: ROOT },
    )
      .toString()
      .trim()
      .split('\n')
      .filter(Boolean),
  ),
].sort();

// ── Managed-file targets ──────────────────────────────────────────────────
const TARGETS = [
  {
    file: '.markdownlint-cli2.jsonc',
    begin:
      '    // >>> BEGIN sync-lint-ignores (managed by scripts/sync-lint-ignores.mjs — run it; do not hand-edit) <<<',
    end: '    // >>> END sync-lint-ignores <<<',
    render: (dir) => `    "${dir}/**",`,
  },
  {
    file: 'ruff.toml',
    begin:
      '  # >>> BEGIN sync-lint-ignores (managed by scripts/sync-lint-ignores.mjs — run it; do not hand-edit) <<<',
    end: '  # >>> END sync-lint-ignores <<<',
    render: (dir) => `  "${dir}",`,
  },
];

/**
 * Rebuild a file's content with the managed block (between BEGIN and END
 * sentinels) replaced by the freshly-rendered entries. Everything outside the
 * sentinels is preserved verbatim.
 */
function rebuild(target) {
  const abs = path.join(ROOT, target.file);
  const original = fs.readFileSync(abs, 'utf8');
  // Preserve the file's existing line ending. A CRLF checkout (Windows, or
  // git core.autocrlf=true) would otherwise leave a trailing \r on every line
  // after split('\n'), so the sentinel lookup below would never match and the
  // generator would wrongly report a missing sentinel.
  const eol = original.includes('\r\n') ? '\r\n' : '\n';
  const lines = original.split(eol);

  const beginIdx = lines.indexOf(target.begin);
  const endIdx = lines.indexOf(target.end);

  if (beginIdx === -1 || endIdx === -1) {
    throw new Error(
      `${target.file}: missing sync-lint-ignores sentinel(s) ` +
        `(BEGIN ${beginIdx === -1 ? 'NOT FOUND' : 'ok'}, ` +
        `END ${endIdx === -1 ? 'NOT FOUND' : 'ok'}). ` +
        'The managed region must be delimited by the BEGIN/END sentinel comments.',
    );
  }
  if (endIdx < beginIdx) {
    throw new Error(`${target.file}: END sentinel appears before BEGIN sentinel.`);
  }

  const before = lines.slice(0, beginIdx + 1); // through the BEGIN sentinel
  const after = lines.slice(endIdx); // from the END sentinel onward
  const rendered = syncedDirs.map(target.render);

  const rebuilt = [...before, ...rendered, ...after].join(eol);

  // Current entries inside the managed block, for drift reporting.
  const currentEntries = lines.slice(beginIdx + 1, endIdx);

  return { abs, original, rebuilt, currentEntries };
}

/**
 * Extract the plugin-dir set currently represented inside a target's managed
 * block, from its rendered entry lines. Works for both `"<dir>/**",` and
 * `"<dir>",` shapes by pulling the first quoted string and trimming a `/**`.
 */
function dirsFromEntries(entryLines) {
  const dirs = new Set();
  for (const line of entryLines) {
    const m = line.match(/"([^"]+)"/);
    if (!m) continue;
    dirs.add(m[1].replace(/\/\*\*$/, ''));
  }
  return dirs;
}

let anyDrift = false;
const results = [];

for (const target of TARGETS) {
  const r = rebuild(target);
  const changed = r.original !== r.rebuilt;
  results.push({ target, ...r, changed });
  if (changed) anyDrift = true;
}

if (CHECK) {
  if (!anyDrift) {
    console.log(
      `✓ all ${syncedDirs.length} synced plugins are excluded from markdownlint + ruff (in sync)`,
    );
    process.exit(0);
  }

  console.error('✗ synced-plugin lint-exclusion drift detected:\n');
  const want = new Set(syncedDirs);
  for (const { target, currentEntries } of results) {
    const have = dirsFromEntries(currentEntries);
    const missing = [...want].filter((d) => !have.has(d)).sort();
    const extra = [...have].filter((d) => !want.has(d)).sort();
    if (missing.length === 0 && extra.length === 0) continue;
    console.error(`  ${target.file}:`);
    missing.forEach((d) => console.error(`    + missing: ${d}`));
    extra.forEach((d) => console.error(`    - stale:   ${d}`));
    console.error('');
  }
  console.error(`These dirs carry a .source.json (external-synced) marker; their mirrored`);
  console.error(`markdown/python must be excluded from this repo's lint gates.`);
  console.error(`\nFix: ${FIX_CMD}`);
  process.exit(1);
}

// ── WRITE mode ────────────────────────────────────────────────────────────
for (const { target, abs, rebuilt, changed } of results) {
  if (changed) {
    fs.writeFileSync(abs, rebuilt);
    console.log(`✓ wrote ${syncedDirs.length} synced-plugin exclusions to ${target.file}`);
  } else {
    console.log(`✓ ${target.file} already up to date`);
  }
}
