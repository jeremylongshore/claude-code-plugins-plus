import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const script = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  'check-certification-separation.mjs',
);

function record(overrides = {}) {
  return {
    artifact_path: 'plugins/example/skills/example/SKILL.md',
    signing_identity:
      'https://github.com/acme/marketplace/.github/workflows/certify.yml@refs/heads/main',
    pr_author_identity: 'octocat',
    producing_identity: 'ci://evaluation-runner',
    ...overrides,
  };
}

function write(payload) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'certification-identities-'));
  const file = path.join(dir, 'identities.json');
  fs.writeFileSync(file, JSON.stringify(payload));
  return file;
}

function invoke(payload) {
  return spawnSync(process.execPath, [script, '--records', write(payload)], {
    encoding: 'utf8',
  });
}

test('accepts a bundle signer independent from both author and producer', () => {
  const result = invoke({ schema_version: 'certification-identities/v1', records: [record()] });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /certification separation: OK \(1 record\(s\)\)/);
});

test('refuses a signer that is the PR author', () => {
  const result = invoke({
    schema_version: 'certification-identities/v1',
    records: [record({ signing_identity: 'octocat' })],
  });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /E-CERTIFIER-IS-PR-AUTHOR/);
});

test('refuses a signer that is the producing identity', () => {
  const result = invoke({
    schema_version: 'certification-identities/v1',
    records: [record({ signing_identity: 'ci://evaluation-runner' })],
  });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /E-CERTIFIER-IS-PRODUCER/);
});

test('refuses missing or malformed identity records', () => {
  const result = invoke({ schema_version: 'certification-identities/v1', records: [{}] });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /missing artifact_path/);
});

test('exports the verifier for CI-side evidence adapters', async () => {
  const verifier = await import('./check-certification-separation.mjs');
  assert.deepEqual(
    verifier.validateRecords({ schema_version: 'certification-identities/v1', records: [] }),
    [],
  );
  assert.throws(
    () => verifier.validateRecords({ schema_version: 'wrong', records: [] }),
    /schema_version/,
  );
});
