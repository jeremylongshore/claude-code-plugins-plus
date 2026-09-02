import assert from 'node:assert/strict';
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

const installer = new URL('../ops/install-security-headers.sh', import.meta.url).pathname;
const source = new URL('../ops/tonsofskills-security-headers.caddy', import.meta.url).pathname;

function fixture(mainText = 'example.invalid {\n    import security-headers\n}\n') {
  const directory = mkdtempSync(join(tmpdir(), 'security-header-install-'));
  const target = join(directory, 'security-headers.caddy');
  const main = join(directory, 'Caddyfile');
  const bin = join(directory, 'bin');
  const caddy = join(bin, 'caddy');
  mkdirSync(bin);
  writeFileSync(caddy, '#!/usr/bin/env sh\n[ "$1" = "adapt" ]\n');
  chmodSync(caddy, 0o755);
  writeFileSync(main, mainText);
  return { directory, target, main, bin };
}

function check(paths) {
  return spawnSync(
    'bash',
    [installer, '--check', source, paths.target, paths.main, 'example.invalid {'],
    {
      encoding: 'utf8',
      env: { ...process.env, PATH: `${paths.bin}:${process.env.PATH}` },
    },
  );
}

test('installer validates an exact candidate without touching live files', () => {
  const paths = fixture();
  try {
    const before = readFileSync(paths.main, 'utf8');
    const result = check(paths);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /candidate valid; sha256=[0-9a-f]{64}/);
    assert.equal(readFileSync(paths.main, 'utf8'), before);
    assert.equal(readFileSync(source, 'utf8').includes('Content-Security-Policy'), true);
  } finally {
    rmSync(paths.directory, { recursive: true, force: true });
  }
});

test('installer refuses ambiguous site anchors', () => {
  const paths = fixture(
    'one.invalid {\n    import security-headers\n}\ntwo.invalid {\n    import security-headers\n}\n',
  );
  try {
    const result = check(paths);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /expected one site block/);
  } finally {
    rmSync(paths.directory, { recursive: true, force: true });
  }
});

test('installer is idempotent when the exact import already exists', () => {
  const paths = fixture();
  try {
    writeFileSync(
      paths.main,
      `example.invalid {\n    import security-headers\n    import ${paths.target}\n}\n`,
    );
    const result = check(paths);
    assert.equal(result.status, 0, result.stderr);
  } finally {
    rmSync(paths.directory, { recursive: true, force: true });
  }
});
