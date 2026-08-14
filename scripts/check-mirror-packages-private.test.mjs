import { deepEqual, equal } from 'node:assert/strict';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { test } from 'node:test';
import { scanMirrorPackages } from './check-mirror-packages-private.mjs';

function fixture(privateValue) {
  const root = mkdtempSync(join(tmpdir(), 'mirror-private-'));
  const plugin = join(root, 'plugins', 'fixture', 'example');
  mkdirSync(plugin, { recursive: true });
  writeFileSync(join(plugin, '.source.json'), '{"source":"upstream/example"}\n');
  writeFileSync(
    join(plugin, 'package.json'),
    JSON.stringify({ name: '@example/mirror', private: privateValue }),
  );
  return root;
}

test('machine-provenance package passes only when private is true', () => {
  const root = fixture(true);
  try {
    const result = scanMirrorPackages(root);
    equal(result.markerCount, 1);
    equal(result.packageCount, 1);
    deepEqual(result.violations, []);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('machine-provenance package is reported when publishable', () => {
  const root = fixture(false);
  try {
    const result = scanMirrorPackages(root);
    equal(result.violations.length, 1);
    equal(result.violations[0].name, '@example/mirror');
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
