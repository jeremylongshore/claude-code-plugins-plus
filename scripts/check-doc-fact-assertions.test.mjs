import test from 'node:test';
import assert from 'node:assert/strict';
import {
  actualCiRequiredNeeds,
  compareCiRequired,
  documentedCiRequiredClaim,
  missingContexts,
  schemaClaims,
  validatorSchemaVersion,
} from './check-doc-fact-assertions.mjs';

const WF = `
jobs:
  ci-required:
    needs:
      - validate
      - verify
      - test
`;

test('workflow needs are extracted from the ci-required job', () => {
  assert.deepEqual(actualCiRequiredNeeds(WF), ['validate', 'verify', 'test']);
  assert.throws(() => actualCiRequiredNeeds('jobs: {}'), /no needs array/);
});

test('the prose enumeration parses count and names', () => {
  const claim = documentedCiRequiredClaim('… `needs:` all 3 gate jobs (validate, verify, test).');
  assert.equal(claim.count, 3);
  assert.deepEqual(claim.names, ['validate', 'verify', 'test']);
  assert.throws(() => documentedCiRequiredClaim('no anchor here'), /anchor moved/);
});

test('count and set mismatches are both reported', () => {
  const actual = ['validate', 'verify', 'test'];
  assert.deepEqual(compareCiRequired({ count: 3, names: actual }, actual), []);
  const wrong = compareCiRequired({ count: 2, names: ['validate', 'stale-job'] }, actual);
  assert.ok(wrong.some((p) => p.includes('count')));
  assert.ok(wrong.some((p) => p.includes('missing from prose: verify')));
  assert.ok(wrong.some((p) => p.includes('unknown job: stale-job')));
});

test('all three required contexts must be named', () => {
  assert.deepEqual(missingContexts('ci-required gitleaks skill-conform'), []);
  assert.deepEqual(missingContexts('ci-required + gitleaks are the two'), ['skill-conform']);
});

test('schema authority and claim surfaces parse', () => {
  assert.equal(validatorSchemaVersion('x\nSCHEMA_VERSION = "4.0.0"\ny'), '4.0.0');
  const claims = schemaClaims({
    claudeText: 'Validator (schema 4.0.0 — see changelog)',
    specText: 'CURRENT SCHEMA: 4.0.0',
    changelogText: '# log\n\n## [4.0.0] — 2026-08-16\n\n## [3.16.1] — old',
  });
  assert.deepEqual(
    claims.map((c) => c.version),
    ['4.0.0', '4.0.0', '4.0.0'],
  );
});

test('a missing claim surface is reported as null, never silently passed', () => {
  const claims = schemaClaims({ claudeText: 'no anchor', specText: 'none', changelogText: 'none' });
  assert.deepEqual(
    claims.map((c) => c.version),
    [null, null, null],
  );
});
