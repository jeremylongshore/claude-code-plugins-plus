import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { openForUpdateOrCreate, readFileSnapshot, replaceOpenFile } from './sync-external.mjs';

function fixture() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'sync-external-file-io-'));
}

test('descriptor-bound update creates and then replaces the same regular file', (t) => {
  const root = fixture();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const target = path.join(root, 'nested', 'artifact.txt');

  const created = openForUpdateOrCreate(target);
  assert.equal(created.created, true);
  replaceOpenFile(created.fd, 'first\n', 0o644);
  fs.closeSync(created.fd);

  const updated = openForUpdateOrCreate(target);
  assert.equal(updated.created, false);
  assert.equal(fs.readFileSync(updated.fd, 'utf8'), 'first\n');
  replaceOpenFile(updated.fd, Buffer.from('second\n'), 0o755);
  fs.closeSync(updated.fd);

  const snapshot = readFileSnapshot(target);
  assert.equal(snapshot.content.toString('utf8'), 'second\n');
  assert.equal(snapshot.mode & 0o777, 0o755);
});

test('snapshot returns null for absence and rejects directories', (t) => {
  const root = fixture();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));

  assert.equal(readFileSnapshot(path.join(root, 'missing.txt')), null);
  assert.throws(() => readFileSnapshot(root), /must be a regular file/);
});
