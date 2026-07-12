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

import { parseVersion, compareVersion, bumpDecision } from './auto-bump-changed-plugins.mjs';

const v = (s) => parseVersion(s);

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
