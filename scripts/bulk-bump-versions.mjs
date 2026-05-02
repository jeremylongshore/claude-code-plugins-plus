#!/usr/bin/env node
/**
 * bulk-bump-versions.mjs
 *
 * One-time sweep to break the v1.0.0 freeze.
 *
 * Background: `scripts/generate-plugin-package-jsons.mjs` defaults every newly
 * minted plugin's `package.json` to `version: "1.0.0"`. Until a human bumps it
 * the value never changes, and `publish-changed-packages.yml` (which gates on
 * "declared version not yet on npm") never republishes. Downstream `pnpm
 * update` users have been frozen on the bytes that first shipped — for some
 * packages, since 2026-01-09.
 *
 * What this script does, for every `@intentsolutionsio/*` package.json under
 * `plugins/**` and `packages/**`:
 *
 *   1. Read the declared local version.
 *   2. Probe the npm registry for the package's latest version.
 *   3. Decide:
 *        - declared == npm-latest  →  bump one MINOR (e.g. 1.0.0 → 1.1.0,
 *                                     5.0.0 → 5.1.0). Real new functionality
 *                                     has accumulated since first publish;
 *                                     patch would understate the gap.
 *        - declared >  npm-latest  →  leave as-is (someone already bumped).
 *        - declared <  npm-latest  →  leave as-is + flag (registry is ahead;
 *                                     human should reconcile).
 *        - not on npm at all       →  leave version, but flag as a coverage
 *                                     gap. The publish workflow will pick it
 *                                     up as a fresh publish on next merge.
 *        - rate-limited / network  →  leave + flag for a re-run.
 *
 * On `--apply` (default off) the script writes the new versions. Without
 * `--apply` it only prints the plan + the coverage gap report.
 *
 * Usage:
 *   node scripts/bulk-bump-versions.mjs           # dry-run; print plan
 *   node scripts/bulk-bump-versions.mjs --apply   # write new versions
 *   node scripts/bulk-bump-versions.mjs --apply --filter '^@intentsolutionsio/lang.*'
 *
 * Exit codes:
 *   0 — clean run; plan computed (with or without --apply).
 *   1 — registry probes hit persistent rate-limits or server errors. The
 *       script bails before writing so we don't stamp a partial bump.
 */

import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const SKIP_DIRS = new Set(['node_modules', '.git', 'dist', 'build', '.next', '.astro']);
const SCOPE = '@intentsolutionsio/';

function walkPackageJsons(dir) {
  const out = [];
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const ent of entries) {
    const p = join(dir, ent.name);
    if (ent.isDirectory()) {
      if (SKIP_DIRS.has(ent.name)) continue;
      out.push(...walkPackageJsons(p));
    } else if (ent.isFile() && ent.name === 'package.json') {
      out.push(p);
    }
  }
  return out;
}

function readPkg(path) {
  try {
    return { raw: readFileSync(path, 'utf-8') };
  } catch {
    return null;
  }
}

function parsePkg(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

// Strict X.Y.Z parse. Pre-release / build-metadata tails are not supported in
// this codebase; everything ships as plain MAJOR.MINOR.PATCH. If we ever see
// a non-conforming version we bail rather than guess.
function parseVersion(v) {
  if (!v || typeof v !== 'string') return null;
  const m = /^(\d+)\.(\d+)\.(\d+)$/.exec(v.trim());
  if (!m) return null;
  return { major: +m[1], minor: +m[2], patch: +m[3] };
}

function fmtVersion(p) {
  return `${p.major}.${p.minor}.${p.patch}`;
}

function bumpMinor(v) {
  return { major: v.major, minor: v.minor + 1, patch: 0 };
}

function compareVersions(a, b) {
  if (a.major !== b.major) return a.major - b.major;
  if (a.minor !== b.minor) return a.minor - b.minor;
  return a.patch - b.patch;
}

async function fetchNpmLatest(name) {
  // Same tagged-result pattern as fetch-npm-stats: distinguish 404 from
  // rate-limit so callers can react instead of guessing.
  const enc = encodeURIComponent(name);
  const url = `https://registry.npmjs.org/${enc}`;
  let lastError = null;
  for (let i = 0; i < 4; i++) {
    let res;
    try {
      res = await fetch(url);
    } catch (err) {
      lastError = err;
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
      continue;
    }
    if (res.status === 404) return { kind: 'not-found' };
    if (res.status === 429) {
      await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, i)));
      continue;
    }
    if (res.status >= 500) {
      lastError = new Error(`HTTP ${res.status}`);
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
      continue;
    }
    if (!res.ok) return { kind: 'error', status: res.status };
    try {
      const meta = await res.json();
      const latest = meta?.['dist-tags']?.latest;
      if (!latest) return { kind: 'no-latest', meta };
      return { kind: 'found', latest, meta };
    } catch (err) {
      lastError = err;
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
    }
  }
  if (lastError) return { kind: 'server-error', error: lastError.message };
  return { kind: 'rate-limited' };
}

async function plan(pkgFiles, filterRegex) {
  const items = [];
  for (const path of pkgFiles) {
    const file = readPkg(path);
    if (!file) continue;
    const pkg = parsePkg(file.raw);
    if (!pkg || !pkg.name || pkg.private) continue;
    if (!pkg.name.startsWith(SCOPE)) continue;
    if (filterRegex && !filterRegex.test(pkg.name)) continue;
    items.push({ path, raw: file.raw, pkg });
  }

  // Serial fetch (concurrency=4) — avoid hammering the registry.
  const results = [];
  let i = 0;
  const concurrency = 4;
  async function worker() {
    while (i < items.length) {
      const idx = i++;
      const it = items[idx];
      const declared = parseVersion(it.pkg.version);
      const probe = await fetchNpmLatest(it.pkg.name);
      results[idx] = { ...it, declared, probe };
    }
  }
  await Promise.all(Array.from({ length: concurrency }, () => worker()));
  return results;
}

function decide(item) {
  const { declared, probe, pkg } = item;
  if (!declared) {
    return {
      action: 'skip',
      reason: `local version "${pkg.version}" is not strict X.Y.Z — manual review needed`,
    };
  }
  if (probe.kind === 'rate-limited') {
    return { action: 'skip-flag', reason: 'rate-limited; re-run later', flag: 'rate-limited' };
  }
  if (probe.kind === 'server-error') {
    return {
      action: 'skip-flag',
      reason: `registry server error: ${probe.error}`,
      flag: 'error',
    };
  }
  if (probe.kind === 'error') {
    return {
      action: 'skip-flag',
      reason: `registry returned HTTP ${probe.status}`,
      flag: 'error',
    };
  }
  if (probe.kind === 'not-found' || probe.kind === 'no-latest') {
    return {
      action: 'first-publish',
      reason:
        'no npm record yet — coverage gap; publish-changed-packages.yml will pick it up on next merge',
      flag: 'coverage-gap',
    };
  }
  // Found
  const npmLatest = parseVersion(probe.latest);
  if (!npmLatest) {
    return {
      action: 'skip',
      reason: `npm latest "${probe.latest}" is not strict X.Y.Z — manual review needed`,
    };
  }
  const cmp = compareVersions(declared, npmLatest);
  if (cmp > 0) {
    return {
      action: 'leave-ahead',
      reason: `local ${fmtVersion(declared)} > npm ${fmtVersion(npmLatest)}; already bumped`,
    };
  }
  if (cmp < 0) {
    return {
      action: 'skip-flag',
      reason: `local ${fmtVersion(declared)} < npm ${fmtVersion(npmLatest)}; registry is ahead — reconcile manually`,
      flag: 'behind-npm',
    };
  }
  // Equal — bump one minor.
  const newVersion = bumpMinor(declared);
  return {
    action: 'bump',
    from: fmtVersion(declared),
    to: fmtVersion(newVersion),
    reason: `local matches npm at ${fmtVersion(declared)}; bumping minor`,
  };
}

function applyBump(item, newVersionStr) {
  // Edit the JSON text in-place so we don't reorder keys or normalize
  // whitespace / trailing commas. Anchor the replace on the existing version
  // string to avoid clobbering any nested "version" field in dependencies etc.
  const oldLine = `"version": "${item.pkg.version}"`;
  const newLine = `"version": "${newVersionStr}"`;
  if (!item.raw.includes(oldLine)) {
    throw new Error(
      `Cannot find exact "${oldLine}" line in ${item.path}; refusing to edit`
    );
  }
  const updated = item.raw.replace(oldLine, newLine);
  writeFileSync(item.path, updated);
}

async function main() {
  const args = process.argv.slice(2);
  const apply = args.includes('--apply');
  let filterRegex = null;
  const filterIdx = args.indexOf('--filter');
  if (filterIdx !== -1 && args[filterIdx + 1]) {
    const raw = args[filterIdx + 1];
    // Defense-in-depth: cap length and reject control characters before
    // compiling. The script is developer-only (no service input path), but
    // a runaway pattern could ReDoS the local run. CodeQL js/regex-injection
    // is suppressed because the input is bounded + the catch handles errors.
    if (raw.length > 200) {
      console.error(`--filter pattern too long (${raw.length} > 200 chars)`);
      process.exit(2);
    }
    if (/[\x00-\x1f\x7f]/.test(raw)) {
      console.error(`--filter pattern contains control characters; refusing`);
      process.exit(2);
    }
    try {
      filterRegex = new RegExp(raw); // lgtm[js/regex-injection]
    } catch (err) {
      console.error(`Bad --filter regex: ${err.message}`);
      process.exit(2);
    }
  }

  const candidatePaths = [
    ...walkPackageJsons(join(ROOT, 'plugins')),
    ...walkPackageJsons(join(ROOT, 'packages')),
  ];

  console.log(`Scanning ${candidatePaths.length} package.json files...`);
  const items = await plan(candidatePaths, filterRegex);
  console.log(`@intentsolutionsio/* candidates: ${items.length}`);

  const buckets = {
    bump: [],
    'first-publish': [],
    'leave-ahead': [],
    'skip-flag': [],
    skip: [],
  };
  for (const item of items) {
    const decision = decide(item);
    item.decision = decision;
    buckets[decision.action].push(item);
  }

  console.log('');
  console.log(`  bump (1 minor):   ${buckets.bump.length}`);
  console.log(`  first-publish:    ${buckets['first-publish'].length}  (coverage gap)`);
  console.log(`  leave-ahead:      ${buckets['leave-ahead'].length}`);
  console.log(`  skip-flag:        ${buckets['skip-flag'].length}`);
  console.log(`  skip:             ${buckets.skip.length}`);

  if (buckets.bump.length) {
    console.log('\n--- BUMP PLAN ---');
    for (const it of buckets.bump) {
      console.log(`  ${it.pkg.name.padEnd(50)}  ${it.decision.from} → ${it.decision.to}`);
    }
  }
  if (buckets['first-publish'].length) {
    console.log('\n--- COVERAGE GAPS (no npm record) ---');
    for (const it of buckets['first-publish']) {
      console.log(`  ${it.pkg.name.padEnd(50)}  declared ${it.pkg.version}  (${relative(ROOT, it.path)})`);
    }
    console.log(
      '  → Will publish on next merge to main. Run `node scripts/generate-plugin-package-jsons.mjs --probe` to confirm name availability.'
    );
  }
  if (buckets['skip-flag'].length) {
    console.log('\n--- FLAGGED (rate-limit / behind-npm / error) ---');
    for (const it of buckets['skip-flag']) {
      console.log(
        `  [${it.decision.flag}] ${it.pkg.name.padEnd(45)}  ${it.decision.reason}`
      );
    }
  }
  if (buckets.skip.length) {
    console.log('\n--- SKIP (manual review) ---');
    for (const it of buckets.skip) {
      console.log(`  ${it.pkg.name.padEnd(50)}  ${it.decision.reason}`);
    }
  }

  // Bail if any registry probe was unreliable. The bump set is partial in
  // that case and we'd ship inconsistent versions. Prefer a clean re-run.
  const hasUnreliable = buckets['skip-flag'].some(
    (i) => i.decision.flag === 'rate-limited' || i.decision.flag === 'error'
  );
  if (hasUnreliable) {
    console.error(
      '\n✗ Registry probes were unreliable for at least one package. ' +
        'Re-run when npm is responsive instead of writing a partial bump set.'
    );
    process.exit(1);
  }

  if (!apply) {
    console.log('\n(dry-run; pass --apply to write new versions)');
    return;
  }

  console.log('\nWriting new versions...');
  let written = 0;
  for (const it of buckets.bump) {
    applyBump(it, it.decision.to);
    written += 1;
  }
  console.log(`Wrote ${written} package.json updates.`);
  console.log(
    '\nNext: commit, push, merge to main. publish-changed-packages.yml will publish each bumped package + each coverage-gap package.'
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
