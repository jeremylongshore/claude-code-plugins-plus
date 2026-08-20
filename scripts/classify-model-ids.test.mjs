import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  BEAD_ID,
  MODEL_FAMILY,
  classifyModelToken,
  claudeTokensOnLine,
  loadExclusions,
} from './lib/model-id-classifier.mjs';
import { unpinnedTrackedHandles } from './classify-model-ids.mjs';

test('the committed exclusion list pins every live bead handle', () => {
  const excl = loadExclusions();
  assert.ok(Array.isArray(excl.protected_handles));
  assert.ok(excl.protected_handles.length >= 300, 'the live handle census is in the hundreds');
  // the handles this program itself created must be present
  for (const h of ['claude-hz8f', 'claude-hedb', 'claude-t9s9', 'claude-4laa', 'claude-s03q']) {
    assert.ok(excl.protected_handles.includes(h), `${h} must be pinned`);
  }
  // and disjoint from model families by shape
  for (const h of excl.protected_handles) {
    assert.ok(BEAD_ID.test(h), `${h} must match the bead shape`);
    assert.ok(!MODEL_FAMILY.test(h), `${h} must never match a model family`);
  }
});

test('the committed exclusion list is sorted and duplicate-free', () => {
  const handles = loadExclusions().protected_handles;
  assert.deepEqual(handles, [...handles].sort(), 'handles must stay sorted');
  assert.equal(new Set(handles).size, handles.length, 'handles must be unique');
});

test('every bead handle referenced in the tracked tree is pinned (CI-reachable census)', () => {
  // The 2026-08 audit found the census could only drift-detect on boxes with
  // the untracked .beads/issues.jsonl — CI's green carried no signal, so
  // Epic 4's own epic bead (claude-or1m) landed in tracked AARs without a
  // pin and nothing went red. This leg scans a corpus CI CAN see: any
  // bead-handle-shaped token on a bead-context line in tracked files must
  // already be in the committed exclusion list.
  const missing = unpinnedTrackedHandles();
  assert.equal(
    missing.size,
    0,
    `unpinned handle(s) referenced in tracked files: ${[...missing]
      .map(([p, where]) => `${p} (${where})`)
      .join(', ')}`,
  );
});

test('the tracked-tree census actually detects — an empty pin set surfaces real handles', () => {
  // Guards the detection path itself: if the scan ever degenerates to
  // returning nothing (broken regex, broken git walk), the all-pinned
  // empty-result test above would still pass. With NO pins, the same scan
  // must surface the real handle population, including the one whose miss
  // motivated this gate.
  const found = unpinnedTrackedHandles(new Set());
  assert.ok(found.size >= 50, `expected a large unpinned census, got ${found.size}`);
  assert.ok(found.has('claude-or1m'), 'the Epic 4 epic handle must be detectable');
  assert.match(found.get('claude-or1m'), /^\S+:\d+$/, 'sightings carry file:line provenance');
});

test('bead handles are never rewritable — even on functional-looking lines', () => {
  for (const handle of ['claude-hz8f', 'claude-hedb.11', 'claude-t9s9.1', 'claude-4laa.1']) {
    assert.equal(classifyModelToken(handle, `model: ${handle}`), 'bead-id');
    assert.equal(classifyModelToken(handle, `--model ${handle}`), 'bead-id');
  }
});

test('the three sets are disjoint by construction', () => {
  const line = 'model: claude-sonnet-4 replaces claude-2.1; bead claude-hz8f.14 tracked it';
  const roles = claudeTokensOnLine(line).map((t) => [t, classifyModelToken(t, line)]);
  assert.deepEqual(roles, [
    ['claude-sonnet-4', 'functional'],
    ['claude-2.1', 'functional'],
    ['claude-hz8f.14', 'bead-id'],
  ]);
  const prose = 'the claude-3 era predated claude-fable-5';
  assert.deepEqual(
    claudeTokensOnLine(prose).map((t) => classifyModelToken(t, prose)),
    ['prose', 'prose'],
  );
});

test('the exclusion list stays regenerable from the live beads export', (t) => {
  // The beads workspace is deliberately untracked in this repo (local Dolt is
  // the authority; the JSONL is a machine-local export). CI checkouts have no
  // .beads/, so this leg is the LOCAL-workspace check: absent file → skip.
  // It is no longer the ONLY drift detector — the tracked-tree census above
  // runs everywhere, CI included.
  let raw;
  try {
    raw = readFileSync(new URL('../.beads/issues.jsonl', import.meta.url), 'utf-8');
  } catch {
    t.skip('no local beads export (CI checkout) — census verified at generation time');
    return;
  }
  const ids = new Set();
  for (const line of raw.split('\n')) {
    if (!line.trim()) continue;
    try {
      const id = JSON.parse(line).id ?? '';
      if (BEAD_ID.test(id)) ids.add(id.split('.')[0]);
    } catch {
      /* not a bead row */
    }
  }
  const pinned = new Set(loadExclusions().protected_handles);
  for (const id of ids) {
    assert.ok(pinned.has(id), `live handle ${id} missing from the committed exclusion list`);
  }
});
