#!/usr/bin/env node
/**
 * check-changelog-coverage.mjs — every released tag must have release notes.
 *
 * WHY THIS EXISTS
 * ---------------
 * On 2026-08-06 `/changelog` was found with THREE entries, newest v4.16.0 dated
 * 2026-03-07, while the site ran v4.33.0. Seventeen tagged releases — 556
 * commits across March to May — had shipped with no notes at all, and nothing
 * anywhere failed. The homepage even linked "what's new →" at that page.
 *
 * A changelog rots for the same reason the missing og:image survived five
 * months: nothing in the build depends on it being right. This makes something
 * depend on it.
 *
 * THE INVARIANT
 * -------------
 * For every `vX.Y.Z` git tag there is a matching entry in
 * marketplace/src/content/blog/ carrying that `version:` in its frontmatter.
 *
 * Deliberately NOT checked: entry quality, or whether unreleased work has notes.
 * A gate that demands prose nobody has written yet gets disabled. This asserts
 * only the mechanical fact that a shipped version is documented.
 *
 * FLOOR — why this does not demand notes for every tag ever cut.
 * 46 tags predate the changelog entirely (v1.0.0 through v4.13.0, back to the
 * repo's first release). Requiring notes for those would fail the gate on day
 * one and it would be switched off within a week — the same reason one generic
 * pattern is excluded from scripts/name-leak-gate.sh. The floor is the OLDEST
 * release that actually has notes, so coverage can only ever ratchet forward:
 * everything from the floor up must be documented, everything below is
 * grandfathered. Backfilling history lowers the floor automatically.
 *
 * USAGE
 *   node scripts/check-changelog-coverage.mjs
 *   node scripts/check-changelog-coverage.mjs --warn-only
 */

import { readdirSync, readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const NOTES_DIR = join(ROOT, 'marketplace', 'src', 'content', 'blog');
const WARN_ONLY = process.argv.includes('--warn-only');

// Tags only — a shallow CI clone may have none, which is not a failure.
let tags = [];
try {
  tags = execFileSync('git', ['tag', '--list', 'v[0-9]*.[0-9]*.[0-9]*'], {
    cwd: ROOT,
    encoding: 'utf8',
  })
    .split('\n')
    .map((t) => t.trim())
    // `git tag --list` takes a GLOB, not a regex: `v[0-9]*.[0-9]*.[0-9]*` has a
    // literal dot and zero-or-more wildcards, so it admits shapes it looks like
    // it excludes. Filter strictly here instead of trusting the glob.
    .filter((t) => /^v\d+\.\d+\.\d+$/.test(t));
} catch {
  console.log('changelog-coverage: git tags unavailable — skipping');
  process.exit(0);
}

if (tags.length === 0) {
  // Loud, not silent. A gate that quietly no-ops is indistinguishable from a
  // passing one — which is precisely how this script shipped inert.
  console.log(
    '::warning title=changelog-coverage::No version tags visible — the gate did NOT run. If this is CI, the checkout needs fetch-tags: true.',
  );
  console.log('changelog-coverage: no version tags visible — SKIPPED (not a pass)');
  process.exit(0);
}

// Versions that have a release-notes file, read from frontmatter rather than
// the filename so a rename cannot silently break coverage.
const documented = new Set();
// Recursive: a flat directory today, but an Astro subdirectory grouping
// (blog/2026/…) would otherwise silently stop counting posts and weaken the gate.
for (const f of readdirSync(NOTES_DIR, { recursive: true })) {
  if (!String(f).endsWith('.md')) continue;
  const m = readFileSync(join(NOTES_DIR, String(f)), 'utf8').match(
    /^version:\s*"?([0-9][^"\s]*)"?/m,
  );
  if (m) documented.add(m[1]);
}

const cmp = (a, b) => {
  const pa = a.split('.').map(Number);
  const pb = b.split('.').map(Number);
  for (let i = 0; i < 3; i++) if ((pa[i] || 0) !== (pb[i] || 0)) return (pa[i] || 0) - (pb[i] || 0);
  return 0;
};

// PINNED, not derived. Deriving it from the oldest documented entry looked
// tidier and was wrong: deleting that entry silently RAISED the floor and the
// gate went green with one fewer release covered. Verified by removing
// v4.14.0's notes — the floor moved to v4.15.0 and reported "0 missing".
// A ratchet that a file deletion can loosen is not a ratchet.
//
// Lowering this requires backfilling the releases below it first, as a visible
// edit in review — the same contract as scripts/.design-tokens-baseline.json.
const FLOOR = '4.14.0';
if (!documented.has(FLOOR)) {
  console.error(
    `The pinned floor v${FLOOR} has no release notes. Either restore them, or\n` +
      `lower FLOOR in this script deliberately — do not let it drift.`,
  );
  process.exit(WARN_ONLY ? 0 : 1);
}
const versions = tags.map((t) => t.replace(/^v/, ''));
const inScope = versions.filter((v) => cmp(v, FLOOR) >= 0);
const grandfathered = versions.length - inScope.length;
const missing = inScope.filter((v) => !documented.has(v));

console.log(
  `changelog-coverage: floor v${FLOOR} — ${inScope.length} in scope, ` +
    `${inScope.length - missing.length} documented, ${missing.length} missing ` +
    `(${grandfathered} older tags grandfathered)`,
);

if (missing.length) {
  console.error(
    `\n${missing.length} released version(s) have no release notes:\n` +
      missing.map((v) => `  v${v}`).join('\n') +
      `\n\nAdd a file to marketplace/src/content/blog/ with \`version: "X.Y.Z"\` in\n` +
      `its frontmatter. /changelog renders that collection, and the homepage links\n` +
      `to it — an undocumented release makes that link lie.`,
  );
  process.exit(WARN_ONLY ? 0 : 1);
}
console.log('changelog-coverage: every released tag has notes');
