import test from 'node:test';
import assert from 'node:assert/strict';
import { bindRuntimeVariables, resolveModelClass } from './claude-code-adapter.mjs';

test('every canonical model class resolves to a harness alias', () => {
  assert.equal(resolveModelClass('reasoning-high'), 'opus');
  assert.equal(resolveModelClass('balanced'), 'sonnet');
  assert.equal(resolveModelClass('fast'), 'haiku');
});

test('red run — an unresolvable tier errors, never silently substitutes', () => {
  for (const bad of ['claude-sonnet-4', 'sonnet', 'gpt-5', 'ultra', undefined]) {
    assert.throws(() => resolveModelClass(bad), /fail closed/i, String(bad));
  }
});

test('portable variables bind to the Claude-branded spellings', () => {
  assert.equal(
    bindRuntimeVariables('read ${SKILL_DIR}/references/x.md under ${PLUGIN_ROOT}'),
    'read ${CLAUDE_SKILL_DIR}/references/x.md under ${CLAUDE_PLUGIN_ROOT}',
  );
});

test('ordinary env interpolations pass through untouched', () => {
  assert.equal(
    bindRuntimeVariables('uses ${PLANE_API_KEY} at runtime'),
    'uses ${PLANE_API_KEY} at runtime',
  );
});

test('red run — harness-branded variables in canonical input are refused', () => {
  assert.throws(() => bindRuntimeVariables('read ${CLAUDE_SKILL_DIR}/x'), /harness-branded/);
});

test('red run — an unknown portable directory variable fails closed', () => {
  assert.throws(() => bindRuntimeVariables('read ${WORKSPACE_DIR}/x'), /unknown portable variable/);
});
