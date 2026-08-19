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

test('the exclusion list stays regenerable from the live beads export', () => {
  const ids = new Set();
  for (const line of readFileSync(
    new URL('../.beads/issues.jsonl', import.meta.url),
    'utf-8',
  ).split('\n')) {
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
