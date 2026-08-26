import assert from 'node:assert/strict';
import { test } from 'node:test';
import { evaluate } from './evaluate-launch-readiness.mjs';

const ordered = [
  'legal',
  'safety',
  'provenance',
  'evidence',
  'certification_independence',
  'quality',
  'owner_attestation',
];

function conditions(failed = {}) {
  return {
    schema_version: 'launch-conditions/v1',
    conditions: Object.fromEntries(
      ordered.map((id) => [
        id,
        {
          passed: !failed[id],
          reason_codes: failed[id] ? [`E-${id.toUpperCase()}-FAILED`] : [],
        },
      ]),
    ),
  };
}

test('requires every ordered condition and preserves decision hierarchy', () => {
  const result = evaluate(conditions({ legal: true, quality: true }), '2026-08-26T00:00:00.000Z');
  assert.equal(result.ready, false);
  assert.deepEqual(result.decision_hierarchy, ordered);
  assert.deepEqual(
    result.conditions.map((condition) => condition.id),
    ordered,
  );
  assert.equal(result.conditions[0].passed, false);
  assert.equal(result.conditions[5].passed, false);
});

test('only every passing condition produces readiness', () => {
  const result = evaluate(conditions(), '2026-08-26T00:00:00.000Z');
  assert.equal(result.ready, true);
});

test('fails closed on an incomplete or unreasoned condition set', () => {
  const incomplete = conditions();
  delete incomplete.conditions.quality;
  assert.throws(() => evaluate(incomplete), /exactly/);
  const unreasoned = conditions({ safety: true });
  unreasoned.conditions.safety.reason_codes = [];
  assert.throws(() => evaluate(unreasoned), /machine reason code/);
});
