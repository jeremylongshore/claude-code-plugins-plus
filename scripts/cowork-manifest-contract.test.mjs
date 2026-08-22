import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

import { verifyCoworkChecksum } from './cowork-manifest-contract.mjs';

function fixture() {
  const root = mkdtempSync(join(tmpdir(), 'cowork-manifest-'));
  const filePath = join(root, 'fixture.zip');
  const bytes = Buffer.from('deterministic cowork fixture');
  writeFileSync(filePath, bytes);
  const checksum = createHash('sha256').update(bytes).digest('hex');
  return { root, filePath, checksum };
}

test('accepts the producer checksum field for an exact file', () => {
  const { root, filePath, checksum } = fixture();
  try {
    assert.equal(verifyCoworkChecksum(filePath, { checksum }, 'plugin').ok, true);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('refuses a missing checksum instead of treating it as unverified success', () => {
  const { root, filePath } = fixture();
  try {
    const result = verifyCoworkChecksum(filePath, {}, 'plugin');
    assert.equal(result.ok, false);
    assert.match(result.reason, /missing a valid checksum/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('refuses a sha256 alias and requires the canonical checksum field', () => {
  const { root, filePath, checksum } = fixture();
  try {
    const result = verifyCoworkChecksum(filePath, { sha256: checksum }, 'plugin');
    assert.equal(result.ok, false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('refuses a checksum mismatch', () => {
  const { root, filePath } = fixture();
  try {
    const result = verifyCoworkChecksum(filePath, { checksum: '0'.repeat(64) }, 'plugin');
    assert.equal(result.ok, false);
    assert.match(result.reason, /checksum mismatch/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
