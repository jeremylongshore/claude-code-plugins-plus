import assert from 'node:assert/strict';
import test from 'node:test';
import { readRegistry, validateRegistry } from './validate-harness-registry.mjs';

test('the checked-in harness registry satisfies its support-claim contract', () => {
  assert.deepEqual(validateRegistry(readRegistry()), []);
});

test('red run: a non-verified harness cannot make a public support claim', () => {
  const registry = readRegistry();
  registry.harnesses[1].publicSupport = true;
  assert.match(
    validateRegistry(registry).join('\n'),
    /publicSupport requires verified-native evidence/,
  );
});

test('red run: a native extension cannot masquerade as a portable project skill', () => {
  const registry = readRegistry();
  const omarchy = registry.harnesses.find((harness) => harness.id === 'omarchy');
  omarchy.projectPath = '.omarchy/skills';
  assert.match(
    validateRegistry(registry).join('\n'),
    /native extensions must not declare a portable project path/,
  );
});
