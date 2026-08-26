import assert from 'node:assert/strict';
import { test } from 'node:test';
import { sweep } from './sweep-certification-expiry.mjs';

function report(artifact) {
  return { schema_version: 'certification-report/v1', artifacts: [artifact] };
}

const certified = {
  path: 'plugins/example/skills/example/SKILL.md',
  verdict: 'CERTIFIED',
  evidence_class: 'E3',
  reason_codes: [],
  issued_at: '2026-08-20T00:00:00.000Z',
  ttl_hours: 24,
};

test('demotes expired certifications and reports the delta', () => {
  const result = sweep(report(certified), '2026-08-22T00:00:00.000Z');
  assert.equal(result.certified, 0);
  assert.equal(result.delta.expired_demoted, 1);
  assert.ok(result.artifacts[0].reason_codes.includes('E-CERTIFICATION-EXPIRED'));
});

test('retains unexpired certifications for rendering', () => {
  const result = sweep(report(certified), '2026-08-20T12:00:00.000Z');
  assert.equal(result.certified, 1);
  assert.equal(result.delta.expired_demoted, 0);
  assert.equal(result.artifacts[0].expires_at, '2026-08-21T00:00:00.000Z');
});

test('fails closed when a claimed certification omits a clock', () => {
  const missingTtl = { ...certified };
  delete missingTtl.ttl_hours;
  assert.throws(() => sweep(report(missingTtl), '2026-08-20T00:00:00.000Z'), /ttl_hours/);
});
