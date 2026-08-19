import test from 'node:test';
import assert from 'node:assert/strict';
import { REGISTERED_ADAPTERS, unbackedClaims } from './check-portability-claims.mjs';

test('the registered adapter set is exactly the generated-artifact set', () => {
  assert.deepEqual([...REGISTERED_ADAPTERS], ['claude-code']);
});

test('the four historical claim strings all resolve to unbacked harnesses', () => {
  assert.deepEqual(
    unbackedClaims('Designed for Claude Code, also compatible with Codex and OpenClaw'),
    ['codex', 'openclaw'],
  );
  assert.deepEqual(unbackedClaims('Designed for Claude Code, also compatible with Codex'), [
    'codex',
  ]);
  assert.deepEqual(unbackedClaims('Designed for Claude Code, also compatible with Cursor'), [
    'cursor',
  ]);
  assert.deepEqual(
    unbackedClaims('Designed for Claude Code, also compatible with Cursor, Windsurf, Aider'),
    ['cursor', 'windsurf', 'aider'],
  );
});

test('the honest claim passes', () => {
  assert.deepEqual(unbackedClaims('Designed for Claude Code'), []);
  assert.deepEqual(unbackedClaims('Declared adapters: Claude Code.'), []);
});

test('red run — a fresh unbacked claim in any phrasing is caught', () => {
  assert.ok(unbackedClaims('Works great on Gemini CLI too').includes('gemini-cli'));
  assert.ok(unbackedClaims('Copilot-ready').includes('copilot'));
  assert.ok(unbackedClaims('cline compatible').includes('cline'));
});
