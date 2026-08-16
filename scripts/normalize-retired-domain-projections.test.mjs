import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
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
  const generated = 'marketplace/src/data/catalog.json';
  const clean = 'marketplace/src/data/clean.json';
  const source = 'docs/source.json';
  put(root, generated, JSON.stringify({ url: `https://${DEAD_DOMAIN}` }));
  put(root, clean, '{"stable":true}');
  put(root, source, JSON.stringify({ url: `https://${DEAD_DOMAIN}` }));

  assert.deepEqual(normalizeRetiredDomainProjections({ root }), [generated]);
  assert.equal(JSON.parse(readFileSync(join(root, generated))).url, `https://${LIVE_DOMAIN}`);
  assert.equal(readFileSync(join(root, clean), 'utf8'), '{"stable":true}');
  assert.match(readFileSync(join(root, source), 'utf8'), new RegExp(DEAD_DOMAIN));
});
