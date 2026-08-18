import test from 'node:test';
import assert from 'node:assert/strict';
import { classifyEnvValue, scanMcpConfig } from './check-mcp-plaintext-creds.mjs';

test('known live prefixes are violations', () => {
  for (const v of [
    'apik_Maaaaaaaaaaaaaaaaaaaaaaaa',
    'sk-proj-abcdefabcdef',
    'ghp_16charsofstuffhere',
    'github_pat_11ABC',
    'xoxb-1234-5678',
    'AKIAIOSFODNN7EXAMPLE7',
    'glpat-xxxxxxxxxxxxxxxxxxxx1',
  ]) {
    assert.match(classifyEnvValue(v) ?? '', /prefix/, `${v.slice(0, 6)}… must be flagged`);
  }
});

test('placeholders and interpolations pass', () => {
  for (const v of [
    '${WHOP_API_KEY}',
    '<your-api-key-here>',
    'YOUR_API_KEY_HERE',
    'REPLACE_WITH_YOUR_KEY',
    'CHANGEME',
    'PLACEHOLDER_VALUE_123',
    '',
    'short',
  ]) {
    assert.equal(classifyEnvValue(v), null, `${v || '(empty)'} must pass`);
  }
});

test('long opaque non-placeholder values fail closed', () => {
  assert.match(classifyEnvValue('a1b2c3d4e5f6g7h8i9j0k1l2') ?? '', /opaque/);
  // sentences with spaces are configuration, not secrets
  assert.equal(classifyEnvValue('this is a long description value'), null);
});

test('scanMcpConfig names the server and key', () => {
  const violations = scanMcpConfig({
    mcpServers: {
      good: { command: 'scripts/sops-env', args: ['npx', 'server'] },
      bad: { command: 'npx', env: { API_KEY: 'apik_Mliveliveliveliveliveli' } },
    },
  });
  assert.equal(violations.length, 1);
  assert.match(violations[0], /server "bad" env API_KEY/);
  assert.match(violations[0], /sops-env/);
});

test('empty or env-free configs pass', () => {
  assert.deepEqual(scanMcpConfig({}), []);
  assert.deepEqual(scanMcpConfig({ mcpServers: { a: { command: 'x' } } }), []);
});
