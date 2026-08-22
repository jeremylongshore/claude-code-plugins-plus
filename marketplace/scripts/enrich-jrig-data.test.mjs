import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import {
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const SOURCE = fileURLToPath(new URL('./enrich-jrig-data.mjs', import.meta.url));

test('missing Freshie DB deterministically replaces stale JRig projection', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'enrich-jrig-data-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));

  const script = join(root, 'marketplace', 'scripts', 'enrich-jrig-data.mjs');
  const output = join(root, 'marketplace', 'src', 'data', 'jrig-data.json');
  mkdirSync(dirname(script), { recursive: true });
  mkdirSync(dirname(output), { recursive: true });
  copyFileSync(SOURCE, script);
  writeFileSync(output, '{"stale":{"verified":true}}\n');

  const result = spawnSync(process.execPath, [script], {
    cwd: root,
    encoding: 'utf8',
  });

  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(JSON.parse(readFileSync(output, 'utf8')), {});
  assert.match(result.stderr, /Writing the untracked JRig projection as an empty map/);
});
