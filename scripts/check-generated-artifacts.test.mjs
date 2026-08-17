import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const CHECKER = fileURLToPath(new URL('./check-generated-artifacts.mjs', import.meta.url));

function fixture() {
  const root = mkdtempSync(join(tmpdir(), 'generated-artifacts-'));
  execFileSync('git', ['init', '-q'], { cwd: root });
  return root;
}

function run(root) {
  return spawnSync(process.execPath, [CHECKER], {
    cwd: root,
    encoding: 'utf8',
  });
}

test('untracked marketplace build projections are accepted', (t) => {
  const root = fixture();
  t.after(() => rmSync(root, { recursive: true, force: true }));

  for (const name of ['jrig-data.json', 'readme-sections.json']) {
    const path = join(root, 'marketplace', 'src', 'data', name);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, '{}\n');
  }

  const result = run(root);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /0 tracked/);
});

for (const name of ['jrig-data.json', 'readme-sections.json']) {
  test(`tracked ${name} is refused`, (t) => {
    const root = fixture();
    t.after(() => rmSync(root, { recursive: true, force: true }));
    const relative = `marketplace/src/data/${name}`;
    const path = join(root, relative);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, '{}\n');
    execFileSync('git', ['add', relative], { cwd: root });

    const result = run(root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, new RegExp(`${name.replace('.', '\\.')}`));
    assert.match(result.stderr, /GENERATED projection/);
  });
}

test('Git enumeration failure refuses instead of passing an empty set', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'generated-artifacts-no-git-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));

  const result = run(root);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /refuses to pass without Git evidence/);
});
