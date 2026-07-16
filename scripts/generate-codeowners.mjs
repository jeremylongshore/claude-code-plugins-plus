#!/usr/bin/env node
/**
 * generate-codeowners.mjs
 *
 * Home-Assistant-style per-plugin ownership. Reads the optional `maintainer`
 * field from each plugin entry in `.claude-plugin/marketplace.extended.json`
 * and regenerates the per-plugin owner block in `.github/CODEOWNERS` — the
 * lines that make a plugin's steward auto-own its reviews, so ~470 plugins +
 * a growing cohort scale without hand-editing one giant ownership file.
 *
 * The block is bounded by sentinels that must already exist in CODEOWNERS:
 *   # BEGIN generated per-plugin owners
 *   # END generated per-plugin owners
 * Everything OUTSIDE the sentinels (the hand-authored per-area owners) is left
 * untouched.
 *
 * The `maintainer` field is OPTIONAL and may be:
 *   "maintainer": "octocat"                     → /plugins/<cat>/<name>/ @octocat
 *   "maintainer": "@octocat"                    → same (leading @ tolerated)
 *   "maintainer": ["octocat", "hubot"]          → both handles on one line
 * A plugin with no `maintainer` field is skipped (it falls through to its
 * area owner via the hand-authored rules above the block). Population is
 * incremental — this generator is safe to run at any coverage level.
 *
 * Usage:
 *   node scripts/generate-codeowners.mjs           # rewrite the block in place
 *   node scripts/generate-codeowners.mjs --check    # CI: exit 1 if stale (no write)
 *   node scripts/generate-codeowners.mjs --dry-run   # print the block, no write
 *
 * Governance context: GOVERNANCE.md § "Scaling: per-plugin ownership".
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const CATALOG = join(ROOT, '.claude-plugin', 'marketplace.extended.json');
const CODEOWNERS = join(ROOT, '.github', 'CODEOWNERS');

const BEGIN = '# BEGIN generated per-plugin owners';
const END = '# END generated per-plugin owners';

const HANDLE_RE = /^@?[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$/;

/** Normalize a maintainer value into a sorted, deduped list of `@handle`s. */
function normalizeHandles(value, pluginName) {
  const raw = Array.isArray(value) ? value : [value];
  const handles = [];
  for (const entry of raw) {
    if (typeof entry !== 'string' || !entry.trim()) continue;
    const bare = entry.trim().replace(/^@/, '');
    if (!HANDLE_RE.test(bare)) {
      throw new Error(
        `Invalid maintainer handle "${entry}" on plugin "${pluginName}". ` +
          `Expected a GitHub username (optionally @-prefixed).`,
      );
    }
    handles.push(`@${bare}`);
  }
  return [...new Set(handles)].sort();
}

/** Derive the CODEOWNERS path for a plugin from its catalog `source`. */
function ownerPathFor(plugin) {
  // source looks like "./plugins/<category>/<name>" — CODEOWNERS wants
  // "/plugins/<category>/<name>/" (leading slash, trailing slash = dir match).
  const src = String(plugin.source || '')
    .replace(/^\.\//, '')
    .replace(/\/+$/, '');
  if (!src.startsWith('plugins/')) return null; // packages/, mcp shims, etc.
  return `/${src}/`;
}

function buildBlock() {
  const catalog = JSON.parse(readFileSync(CATALOG, 'utf8'));
  const plugins = Array.isArray(catalog.plugins) ? catalog.plugins : [];

  const rows = [];
  for (const plugin of plugins) {
    if (plugin.maintainer == null) continue;
    const handles = normalizeHandles(plugin.maintainer, plugin.name);
    if (handles.length === 0) continue;
    const path = ownerPathFor(plugin);
    if (!path) continue;
    rows.push({ path, owners: handles.join(' ') });
  }

  // Deterministic order so the diff is stable across runs.
  rows.sort((a, b) => a.path.localeCompare(b.path));

  const lines = [BEGIN];
  if (rows.length === 0) {
    lines.push('# (no per-plugin `maintainer` fields set yet — populate incrementally)');
  } else {
    const pad = Math.max(...rows.map((r) => r.path.length));
    for (const r of rows) lines.push(`${r.path.padEnd(pad)}  ${r.owners}`);
  }
  lines.push(END);
  return lines.join('\n');
}

function spliceBlock(current, block) {
  const beginIdx = current.indexOf(BEGIN);
  const endIdx = current.indexOf(END);
  if (beginIdx === -1 || endIdx === -1 || endIdx < beginIdx) {
    throw new Error(
      `Sentinels not found in .github/CODEOWNERS. Expected both:\n  ${BEGIN}\n  ${END}`,
    );
  }
  const before = current.slice(0, beginIdx);
  const after = current.slice(endIdx + END.length);
  return `${before}${block}${after}`;
}

function main() {
  const args = new Set(process.argv.slice(2));
  const check = args.has('--check');
  const dryRun = args.has('--dry-run');

  const block = buildBlock();

  if (dryRun) {
    process.stdout.write(block + '\n');
    return;
  }

  const current = readFileSync(CODEOWNERS, 'utf8');
  const updated = spliceBlock(current, block);

  if (check) {
    if (updated !== current) {
      console.error(
        '❌ .github/CODEOWNERS per-plugin block is stale.\n' +
          '   Run: node scripts/generate-codeowners.mjs\n' +
          '   (regenerates the block from the `maintainer` fields in ' +
          'marketplace.extended.json)',
      );
      process.exit(1);
    }
    console.log('✅ .github/CODEOWNERS per-plugin block is in sync.');
    return;
  }

  if (updated !== current) {
    writeFileSync(CODEOWNERS, updated);
    console.log('✅ Regenerated the per-plugin owner block in .github/CODEOWNERS.');
  } else {
    console.log('✅ .github/CODEOWNERS already up to date — no change.');
  }
}

main();
