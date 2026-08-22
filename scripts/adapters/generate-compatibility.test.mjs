import test from 'node:test';
import assert from 'node:assert/strict';
import {
  GENERATED_PREFIX,
  generateCompatibility,
  isGeneratedCompatibility,
} from './generate-compatibility.mjs';

const CARD = {
  adapters: ['claude-code'],
  requires: { services: [{ kind: 'mcp', name: 'plane', env: ['PLANE_API_KEY'] }] },
  unsupported: [
    {
      capability: 'user.prompt',
      adapter: 'codex',
      reason: 'no primitive',
      degradation: 'fail-closed',
    },
  ],
};

test('the projection is deterministic and carries every declared fact', () => {
  const s = generateCompatibility(CARD);
  assert.equal(
    s,
    'Declared adapters: Claude Code. Requires: mcp plane (PLANE_API_KEY). Unsupported: user.prompt on codex (fail-closed).',
  );
  assert.equal(generateCompatibility(JSON.parse(JSON.stringify(CARD))), s);
});

test('a minimal card projects the adapter list alone', () => {
  assert.equal(
    generateCompatibility({ adapters: ['claude-code'] }),
    'Declared adapters: Claude Code.',
  );
});

test('an omitted degradation projects the fail-closed default', () => {
  const s = generateCompatibility({
    adapters: ['claude-code'],
    unsupported: [{ capability: 'user.prompt', adapter: 'codex', reason: 'r' }],
  });
  assert.match(s, /user\.prompt on codex \(fail-closed\)/);
});

test('red run — no adapters, no projection', () => {
  assert.throws(() => generateCompatibility({ adapters: [] }), /adapters/);
  assert.throws(() => generateCompatibility({}), /adapters/);
});

test('generated strings are recognizable by prefix; legacy prose is not', () => {
  assert.ok(isGeneratedCompatibility(`${GENERATED_PREFIX} Claude Code.`));
  assert.ok(!isGeneratedCompatibility('Designed for Claude Code'));
  assert.ok(!isGeneratedCompatibility('Works with Codex and OpenClaw'));
});
