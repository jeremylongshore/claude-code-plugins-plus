import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';

import { validateRepository } from './validate-greptile-config.mjs';

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'greptile-config-test-'));
  fs.mkdirSync(path.join(root, '.greptile'), { recursive: true });
  fs.writeFileSync(path.join(root, 'ARCHITECTURE.md'), '# Architecture\n');
  fs.writeFileSync(
    path.join(root, '.greptile', 'config.json'),
    JSON.stringify({
      strictness: 2,
      context: { repos: ['acme/contracts'] },
      rules: [
        {
          id: 'root-rule',
          rule: 'Reject changes that violate the architecture contract.',
          severity: 'high',
        },
      ],
    }),
  );
  fs.writeFileSync(
    path.join(root, '.greptile', 'files.json'),
    JSON.stringify({ files: [{ path: 'ARCHITECTURE.md', scope: ['src/**'] }] }),
  );
  return root;
}

test('accepts valid root and nested cascading configuration', () => {
  const root = fixture();
  fs.mkdirSync(path.join(root, 'src', '.greptile'), { recursive: true });
  fs.writeFileSync(
    path.join(root, 'src', '.greptile', 'config.json'),
    JSON.stringify({
      rules: [{ id: 'source-rule', rule: 'Every source mutation must validate its exact target.' }],
    }),
  );
  const result = validateRepository(root);
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.stats, { configDirs: 2, rules: 2, files: 1 });
});

test('rejects duplicate rule ids across cascading configs', () => {
  const root = fixture();
  fs.mkdirSync(path.join(root, 'src', '.greptile'), { recursive: true });
  fs.writeFileSync(
    path.join(root, 'src', '.greptile', 'config.json'),
    JSON.stringify({
      rules: [{ id: 'root-rule', rule: 'This duplicate must be rejected across the repository.' }],
    }),
  );
  const { errors } = validateRepository(root);
  assert.ok(errors.some((error) => error.includes('duplicate rule id root-rule')));
});

test('rejects invalid severity and parent-relative scopes', () => {
  const root = fixture();
  const configPath = path.join(root, '.greptile', 'config.json');
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  config.rules[0].severity = 'critical';
  config.rules[0].scope = ['../secrets/**'];
  fs.writeFileSync(configPath, JSON.stringify(config));
  const { errors } = validateRepository(root);
  assert.ok(errors.some((error) => error.includes('severity must be low, medium, or high')));
  assert.ok(errors.some((error) => error.includes('parent-directory patterns are not allowed')));
});

test('rejects missing context files and malformed repository names', () => {
  const root = fixture();
  const configPath = path.join(root, '.greptile', 'config.json');
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  config.context.repos = ['missing-owner-separator'];
  fs.writeFileSync(configPath, JSON.stringify(config));
  fs.writeFileSync(
    path.join(root, '.greptile', 'files.json'),
    JSON.stringify({ files: [{ path: 'MISSING.md' }] }),
  );
  const { errors } = validateRepository(root);
  assert.ok(errors.some((error) => error.includes('invalid owner/repo value')));
  assert.ok(errors.some((error) => error.includes('referenced file does not exist')));
});
