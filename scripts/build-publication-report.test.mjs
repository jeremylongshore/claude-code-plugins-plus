import assert from 'node:assert/strict';
import test from 'node:test';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { buildReport } from './build-publication-report.mjs';
test('refuses publication/package identity mismatch', () => {
  const dir = mkdtempSync(join(tmpdir(), 'publication-report-'));
  writeFileSync(join(dir, 'package.json'), JSON.stringify({ name: 'actual', version: '1.0.0' }));
  assert.throws(
    () =>
      buildReport([{ channel: 'npm', name: 'claimed', package_path: dir }], {
        sbomDir: join(dir, 'sboms'),
      }),
    /does not match/,
  );
});
