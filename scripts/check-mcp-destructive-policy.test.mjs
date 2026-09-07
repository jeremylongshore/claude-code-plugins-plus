import { test } from 'node:test';
import { equal, deepEqual, ok } from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { analyzeRegistry, trackedPluginDirs } from './check-mcp-destructive-policy.mjs';

const entry = (policy, extra = {}) => ({
  policy,
  enforcing_artifact: 'package.json', // any path that exists at repo root
  rationale: 'because.',
  ...extra,
});

test('tracked dirs includes the source-backed a2a-client plugin', () => {
  const dirs = trackedPluginDirs();
  ok(dirs.has('dolt-mcp-vcs'));
  ok(dirs.has('a2a-client'), 'a2a-client is a tracked source-backed plugin');
});

test('an undeclared tracked plugin fails', () => {
  const issues = analyzeRegistry({ policies: {} }, new Set(['some-plugin']));
  deepEqual(
    issues.map((issue) => issue.code),
    ['UNDECLARED_PLUGIN'],
  );
});

test('an orphan entry fails', () => {
  const issues = analyzeRegistry({ policies: { ghost: entry('permit') } }, new Set());
  deepEqual(
    issues.map((issue) => issue.code),
    ['ORPHAN_ENTRY'],
  );
});

test('an invalid policy value fails', () => {
  const issues = analyzeRegistry({ policies: { p: entry('allow-everything') } }, new Set(['p']));
  deepEqual(
    issues.map((issue) => issue.code),
    ['INVALID_POLICY'],
  );
});

test('a refuse declaration without a refusal test fails', () => {
  const issues = analyzeRegistry({ policies: { p: entry('refuse') } }, new Set(['p']));
  deepEqual(
    issues.map((issue) => issue.code),
    ['MISSING_REFUSAL_TEST'],
  );
});

test('a recommend-only declaration with a real test passes analysis', () => {
  const issues = analyzeRegistry(
    { policies: { p: entry('recommend-only', { refusal_test: 'tests/test_dolt_mcp_guard.py' }) } },
    new Set(['p']),
  );
  deepEqual(issues, []);
});

test('a missing enforcing artifact fails', () => {
  const issues = analyzeRegistry(
    { policies: { p: entry('permit', { enforcing_artifact: 'no/such/file.ts' }) } },
    new Set(['p']),
  );
  deepEqual(
    issues.map((issue) => issue.code),
    ['MISSING_ARTIFACT'],
  );
});

test('the live registry covers exactly the tracked plugin set', () => {
  const registry = JSON.parse(
    readFileSync(new URL('../plugins/mcp/destructive-policies.json', import.meta.url), 'utf8'),
  );
  const issues = analyzeRegistry(registry, trackedPluginDirs());
  deepEqual(issues, []);
  equal(Object.keys(registry.policies).length >= 14, true);
});
