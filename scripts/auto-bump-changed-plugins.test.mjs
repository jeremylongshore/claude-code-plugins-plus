/**
 * auto-bump-changed-plugins.test.mjs — the idempotency contract (blocker 62ye.5).
 *
 * The auto-bump workflow re-runs on every PR `synchronize`. Before the fix it
 * re-derived the bump from the CURRENT local version and only checked "did a
 * source file change vs base" — which stays true for the whole PR — so it
 * walked the version forward on every run (0.2.1 → 0.2.2 → …), each bump pushing
 * a GITHUB_TOKEN head that fires no checks and leaves the PR BLOCKED on
 * unreported required contexts. bumpDecision() keys the decision on the version
 * at the PR base, making a second run a no-op.
 *
 * Run: node --test scripts/auto-bump-changed-plugins.test.mjs
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  parseVersion,
  compareVersion,
  bumpDecision,
  bumpMinor,
} from './auto-bump-changed-plugins.mjs';
import {
  setCatalogEntryVersion,
  editCatalogVersions,
  editSkillFrontmatter,
  findSkillFiles,
} from './reconstruct-versions.mjs';

const v = (s) => parseVersion(s);

// Recurrence guard: a display bump must stamp EVERY SKILL.md in the plugin,
// not only the ones in the PR diff — otherwise a non-SKILL edit (command/README)
// strands sibling skills' frontmatter a minor behind the plugin/catalog cards
// and the surface drift regrows. planDisplayBump now sources skillFiles from
// findSkillFiles(dir), so this locks that helper to the "all skills" contract.
test('findSkillFiles returns every SKILL.md under a multi-skill plugin dir', () => {
  const files = findSkillFiles('plugins/saas-packs/clerk-pack');
  assert.ok(Array.isArray(files));
  assert.ok(files.length > 1, `expected multiple skills, got ${files.length}`);
  for (const f of files) {
    assert.ok(f.endsWith('/SKILL.md'), `not a SKILL.md: ${f}`);
    assert.ok(f.startsWith('plugins/saas-packs/clerk-pack/'), `outside plugin dir: ${f}`);
  }
});

test('compareVersion orders by major, then minor, then patch', () => {
  assert.ok(compareVersion(v('1.0.0'), v('0.9.9')) > 0);
  assert.ok(compareVersion(v('0.2.0'), v('0.1.9')) > 0);
  assert.ok(compareVersion(v('0.2.1'), v('0.2.0')) > 0);
  assert.equal(compareVersion(v('1.2.3'), v('1.2.3')), 0);
  assert.ok(compareVersion(v('1.2.3'), v('1.2.4')) < 0);
});

test('at base version → bump (first run on the PR)', () => {
  const d = bumpDecision(v('0.2.0'), v('0.2.0'));
  assert.equal(d.bump, true);
  assert.equal(d.skip, undefined);
});

test('already ahead of base → skip (idempotent: the loop-stopper)', () => {
  // Second synchronize event: local is 0.2.1, base is still 0.2.0.
  const d = bumpDecision(v('0.2.1'), v('0.2.0'));
  assert.ok(d.skip);
  assert.match(d.skip, /already bumped in this PR/);
  assert.equal(d.bump, undefined);
});

test('deliberate manual minor/major bump is not walked further', () => {
  // Author set 0.3.0 by hand; base is 0.2.5 → treated as "already ahead", skip.
  const d = bumpDecision(v('0.3.0'), v('0.2.5'));
  assert.ok(d.skip);
});

test('new plugin (absent on base) → skip, never bumped', () => {
  // base=null means the package.json does not exist on the PR base. Bumping it
  // would loop forever (base stays null every run), so it must skip.
  const d = bumpDecision(v('0.1.0'), null);
  assert.ok(d.skip);
  assert.match(d.skip, /new plugin/);
  assert.equal(d.bump, undefined);
});

test('a full two-run sequence converges (bump once, then no-op)', () => {
  const base = v('0.4.2');
  // Run 1: local == base → bump. Simulate applying it.
  const run1 = bumpDecision(v('0.4.2'), base);
  assert.equal(run1.bump, true);
  const afterBump = v('0.4.3');
  // Run 2: local is now ahead of the unchanged base → skip. No endless walk.
  const run2 = bumpDecision(afterBump, base);
  assert.ok(run2.skip);
});

// ---------------------------------------------------------------------------
// Display-surface helpers (2026-07-16 version-staleness fix)
// ---------------------------------------------------------------------------

test('bumpMinor bumps minor and resets patch', () => {
  assert.deepEqual(bumpMinor(v('1.4.7')), { major: 1, minor: 5, patch: 0 });
  assert.deepEqual(bumpMinor(v('2.0.0')), { major: 2, minor: 1, patch: 0 });
});

const CATALOG_FIXTURE = `{
  "plugins": [
    {
      "name": "alpha",
      "source": "./plugins/cat/alpha",
      "description": "has \\"version\\": \\"9.9.9\\" in prose",
      "version": "1.2.0"
    },
    {
      "name": "beta",
      "source": "./plugins/cat/beta",
      "version": "0.3.0"
    },
    {
      "name": "beta-dup",
      "source": "./plugins/cat/beta",
      "version": "0.3.0"
    }
  ]
}
`;

test('setCatalogEntryVersion edits only the anchored entry', () => {
  const res = setCatalogEntryVersion(CATALOG_FIXTURE, './plugins/cat/alpha', '1.3.0');
  assert.equal(res.old, '1.2.0');
  assert.ok(res.out.includes('"version": "1.3.0"'));
  // beta entries untouched
  assert.equal(res.out.match(/"version": "0\.3\.0"/g).length, 2);
  // valid JSON after edit
  assert.equal(JSON.parse(res.out).plugins[0].version, '1.3.0');
});

test('setCatalogEntryVersion patches every duplicate-source occurrence', () => {
  const res = setCatalogEntryVersion(CATALOG_FIXTURE, './plugins/cat/beta', '0.4.0');
  assert.equal(res.out.match(/"version": "0\.4\.0"/g).length, 2);
  assert.equal(JSON.parse(res.out).plugins[1].version, '0.4.0');
  assert.equal(JSON.parse(res.out).plugins[2].version, '0.4.0');
});

test('setCatalogEntryVersion returns null for an unknown source', () => {
  assert.equal(setCatalogEntryVersion(CATALOG_FIXTURE, './packages/cli', '1.0.0'), null);
});

test('editCatalogVersions batch-edits with old-value verification and dedupes duplicates', () => {
  const { out } = editCatalogVersions(CATALOG_FIXTURE, [
    { source: './plugins/cat/alpha', oldVersion: '1.2.0', newVersion: '1.9.0' },
    { source: './plugins/cat/beta', oldVersion: '0.3.0', newVersion: '0.5.0' },
    { source: './plugins/cat/beta', oldVersion: '0.3.0', newVersion: '0.5.0' },
  ]);
  const parsed = JSON.parse(out);
  assert.equal(parsed.plugins[0].version, '1.9.0');
  assert.equal(parsed.plugins[1].version, '0.5.0');
  assert.equal(parsed.plugins[2].version, '0.5.0');
});

test('editSkillFrontmatter replaces a top-level version', () => {
  const raw = '---\nname: x\nversion: 1.0.0\ntags: [a]\n---\n\n# Body version: 1.0.0 stays\n';
  const res = editSkillFrontmatter(raw, '1.7.0');
  assert.equal(res.old, '1.0.0');
  assert.ok(res.out.includes('\nversion: 1.7.0\n'));
  assert.ok(res.out.includes('# Body version: 1.0.0 stays'));
});

test('editSkillFrontmatter replaces a nested metadata.version and preserves quoting', () => {
  const raw = '---\nname: x\nmetadata:\n  author: y\n  version: "2.1.0"\n---\nbody\n';
  const res = editSkillFrontmatter(raw, '2.2.0');
  assert.equal(res.old, '2.1.0');
  assert.ok(res.out.includes('  version: "2.2.0"'));
});

test('editSkillFrontmatter skips files without a version field or frontmatter', () => {
  assert.ok(editSkillFrontmatter('# no frontmatter\n', '1.0.0').skipped);
  assert.ok(editSkillFrontmatter('---\nname: x\n---\nbody\n', '1.0.0').skipped);
});
