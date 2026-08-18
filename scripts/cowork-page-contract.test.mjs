import { readFileSync } from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';

const page = readFileSync('marketplace/src/pages/cowork.astro', 'utf8');
const grid = readFileSync('marketplace/src/components/CoworkGrid.astro', 'utf8');
const validator = readFileSync('marketplace/scripts/validate-cowork-downloads.mjs', 'utf8');

test('Cowork page has no invented totals or guessed download paths', () => {
  assert.doesNotMatch(page, /\|\|\s*(?:300|1300|18)\b/);
  assert.doesNotMatch(page, /claude-code-plugins-all\.zip/);
  assert.doesNotMatch(page, /catch\s*\{/);
  assert.match(page, /manifest\.bundles\.length/);
  assert.match(page, /Cowork-packaged skills/);
});

test('Cowork grid consumes producer fields and has no loading fallback', () => {
  assert.doesNotMatch(grid, /Loading\.\.\./);
  assert.doesNotMatch(grid, /plugin\.skillCount|plugin\.commandCount/);
  assert.match(grid, /plugin\.skills/);
  assert.match(grid, /plugin\.commands/);
});

test('download validation uses the canonical checksum field', () => {
  assert.match(validator, /verifyCoworkChecksum/);
  assert.doesNotMatch(validator, /\.sha256\b/);
  assert.doesNotMatch(validator, /sort\(\(\) => Math\.random/);
});
