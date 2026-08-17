import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const WORKFLOW = readFileSync(`${ROOT}/.github/workflows/validate-plugins.yml`, 'utf8');

function jobBlock(name) {
  const marker = `  ${name}:\n`;
  const start = WORKFLOW.indexOf(marker);
  assert.notEqual(start, -1, `missing workflow job ${name}`);
  const rest = WORKFLOW.slice(start + marker.length);
  const next = rest.search(/^ {2}[a-zA-Z0-9_-]+:\n/m);
  return rest.slice(0, next === -1 ? undefined : next);
}

test('generated content drift job is unconditional, credential-free, and exact', () => {
  const block = jobBlock('generated-content-drift');
  assert.doesNotMatch(block, /^ {4}if:/m);
  assert.doesNotMatch(block, /\b(?:paths|paths-ignore):/);
  assert.doesNotMatch(block, /continue-on-error|\|\|\s*true|secrets\./);
  assert.match(block, /permissions:\n {6}contents: read/);
  assert.match(block, /persist-credentials: false/);
  assert.match(block, /timeout-minutes: 10/);
  assert.match(block, /npm ci --ignore-scripts/);
  assert.match(block, /node marketplace\/scripts\/discover-skills\.mjs --level=metadata --check/);
  assert.doesNotMatch(block, /(?:npm|pnpm)\s+(?:publish|pack)|git\s+(?:tag|push)/);
});

test('generated content drift is aggregated exactly once without a new context', () => {
  const aggregate = jobBlock('ci-required');
  assert.equal(
    [...aggregate.matchAll(/^ {6}- generated-content-drift$/gm)].length,
    1,
    'ci-required must depend on generated-content-drift exactly once',
  );
  assert.match(aggregate, /^ {4}name: ci-required$/m);
});

test('Validate Plugins remains an every-PR workflow with no path filter', () => {
  const trigger = WORKFLOW.slice(0, WORKFLOW.indexOf('\njobs:'));
  assert.match(trigger, /^ {2}pull_request:$/m);
  assert.doesNotMatch(trigger, /\b(?:paths|paths-ignore):/);
});
