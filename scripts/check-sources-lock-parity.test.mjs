import test from 'node:test';
import assert from 'node:assert/strict';
import { compareKeySets, loadKeySets } from './check-sources-lock-parity.mjs';

test('equal key sets pass', () => {
  const r = compareKeySets(['a', 'b'], ['b', 'a']);
  assert.equal(r.ok, true);
  assert.deepEqual(r.unlocked, []);
  assert.deepEqual(r.orphaned, []);
});

test('a registered-but-unlocked source fails in the unlocked direction', () => {
  const r = compareKeySets(['a', 'b', 'uizze'], ['a', 'b']);
  assert.equal(r.ok, false);
  assert.deepEqual(r.unlocked, ['uizze']);
  assert.deepEqual(r.orphaned, []);
});

test('a locked-but-unregistered source fails in the orphaned direction', () => {
  const r = compareKeySets(['a'], ['a', 'ghost']);
  assert.equal(r.ok, false);
  assert.deepEqual(r.unlocked, []);
  assert.deepEqual(r.orphaned, ['ghost']);
});

test('both directions report simultaneously, sorted', () => {
  const r = compareKeySets(['z-new', 'a-new', 'kept'], ['kept', 'z-gone', 'a-gone']);
  assert.deepEqual(r.unlocked, ['a-new', 'z-new']);
  assert.deepEqual(r.orphaned, ['a-gone', 'z-gone']);
});

test('the tracked registry and lockfile are currently at parity', () => {
  const { registryNames, lockNames } = loadKeySets();
  const r = compareKeySets(registryNames, lockNames);
  assert.deepEqual(r.unlocked, [], 'registered sources missing a lock baseline');
  assert.deepEqual(r.orphaned, [], 'lock entries with no registration');
  assert.equal(registryNames.length, lockNames.length);
});
