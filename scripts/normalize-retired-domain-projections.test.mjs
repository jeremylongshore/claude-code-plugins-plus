import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';

import { DEAD_DOMAIN, LIVE_DOMAIN } from './dead-domain-policy.mjs';
import { normalizeRetiredDomainProjections } from './normalize-retired-domain-projections.mjs';

function fixture() {
  const root = mkdtempSync(join(tmpdir(), 'retired-domain-projections-'));
  execFileSync('git', ['init', '-q'], { cwd: root });
  return root;
}

function put(root, path, value) {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, value);
  execFileSync('git', ['add', '--', path], { cwd: root });
}

test('normalizes only registered generated JSON containing the retired domain', () => {
  const root = fixture();
  const generated = [
    '000-docs/742-RA-DATA-epic-1-scorecard.json',
    'marketplace/src/content/plugins/example.json',
    'marketplace/src/data/catalog.json',
    'marketplace/src/data/readme-sections.json',
    'marketplace/src/data/skills-catalog.json',
    'marketplace/src/data/unified-search-index.json',
    'plugins/example/example/package.json',
  ];
  const clean = 'marketplace/src/data/clean.json';
  const source = 'docs/source.json';
  const mirror = 'plugins/community/mirror/package.json';
  for (const path of generated) {
    put(root, path, JSON.stringify({ url: `https://${DEAD_DOMAIN}` }));
  }
  put(root, clean, '{"stable":true}');
  put(root, source, JSON.stringify({ url: `https://${DEAD_DOMAIN}` }));
  put(
    root,
    'plugins/community/mirror/.source.json',
    JSON.stringify({
      synced_from: { repo: 'upstream/mirror', path: '/' },
    }),
  );
  put(root, mirror, JSON.stringify({ homepage: `https://${DEAD_DOMAIN}` }));

  assert.deepEqual(normalizeRetiredDomainProjections({ root }), generated);
  for (const path of generated) {
    assert.equal(JSON.parse(readFileSync(join(root, path))).url, `https://${LIVE_DOMAIN}`);
  }
  assert.equal(readFileSync(join(root, clean), 'utf8'), '{"stable":true}');
  assert.match(readFileSync(join(root, source), 'utf8'), new RegExp(DEAD_DOMAIN));
  assert.match(readFileSync(join(root, mirror), 'utf8'), new RegExp(DEAD_DOMAIN));
});

test('refuses a symlinked generated projection without modifying its target', () => {
  const root = fixture();
  const target = join(root, 'outside.json');
  const projection = 'marketplace/src/data/catalog.json';
  writeFileSync(target, JSON.stringify({ url: `https://${DEAD_DOMAIN}` }));
  mkdirSync(dirname(join(root, projection)), { recursive: true });
  symlinkSync(target, join(root, projection));
  execFileSync('git', ['add', '--', projection], { cwd: root });

  assert.throws(() => normalizeRetiredDomainProjections({ root }));
  assert.equal(JSON.parse(readFileSync(target, 'utf8')).url, `https://${DEAD_DOMAIN}`);
});
