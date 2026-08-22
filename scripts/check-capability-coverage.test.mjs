import test from 'node:test';
import assert from 'node:assert/strict';
import { parseToken, parseTokenList, splitTokenList } from './lib/tool-token-parser.mjs';
import { coverageForFrontmatter } from './check-capability-coverage.mjs';

test('the parser classifies every corpus token shape', () => {
  assert.deepEqual(parseToken('Read'), { kind: 'builtin', name: 'Read', scope: null, raw: 'Read' });
  assert.deepEqual(parseToken('Bash(jq:*, date:*)'), {
    kind: 'builtin',
    name: 'Bash',
    scope: ['jq:*', 'date:*'],
    raw: 'Bash(jq:*, date:*)',
  });
  assert.deepEqual(parseToken('mcp__plane__create_issue'), {
    kind: 'mcp',
    name: 'plane',
    tool: 'create_issue',
    raw: 'mcp__plane__create_issue',
  });
  assert.equal(parseToken('mcp__plane').tool, null);
  assert.deepEqual(parseToken('triage:fetch_mentions'), {
    kind: 'namespaced',
    name: 'triage',
    tool: 'fetch_mentions',
    raw: 'triage:fetch_mentions',
  });
  assert.equal(parseToken('tweet_explore').kind, 'unknown');
  assert.equal(parseToken('Read Glob Grep Bash').kind, 'unknown');
});

test('commas inside Bash scopes never split the token', () => {
  const tokens = splitTokenList('Read, Bash(git add:*, git commit:*), Write');
  assert.deepEqual(tokens, ['Read', 'Bash(git add:*, git commit:*)', 'Write']);
  assert.equal(parseTokenList('Read, Bash(a,b)').length, 2);
});

test('YAML list values flatten through the same parser', () => {
  const tokens = parseTokenList(['Read', 'Bash(npm:*)', 'mcp__x__y']);
  assert.deepEqual(
    tokens.map((t) => t.kind),
    ['builtin', 'builtin', 'mcp'],
  );
});

test('red run — an unmapped builtin is uncovered', () => {
  const { uncovered } = coverageForFrontmatter({ 'allowed-tools': 'Read, FutureTool' });
  assert.equal(uncovered.length, 1);
  assert.match(uncovered[0].why, /FutureTool/);
});

test('red run — an unknown token without a disposition is uncovered', () => {
  const { uncovered } = coverageForFrontmatter({ tools: ['completely_novel_thing'] });
  assert.equal(uncovered.length, 1);
  assert.match(uncovered[0].why, /no disposition/);
});

test('dispositioned mirror shapes and shape-mapped kinds are covered', () => {
  const { uncovered, counts } = coverageForFrontmatter({
    'allowed-tools': ['tweet_explore', 'triage:lookup_oncall', 'mcp__plane__query', 'Bash(jq:*)'],
  });
  assert.deepEqual(uncovered, []);
  assert.equal(counts.tolerated, 1);
  assert.equal(counts.namespaced, 1);
  assert.equal(counts.mcp, 1);
  assert.equal(counts.builtin, 1);
});

test('all four tool fields are swept, skills and agents alike', () => {
  const fm = {
    'allowed-tools': 'Read',
    'disallowed-tools': 'Write',
    tools: ['Grep'],
    disallowedTools: ['Bash(rm:*)'],
  };
  const { uncovered, counts } = coverageForFrontmatter(fm);
  assert.deepEqual(uncovered, []);
  assert.equal(counts.builtin, 4);
});
