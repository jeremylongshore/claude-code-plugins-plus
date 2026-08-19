import test from 'node:test';
import assert from 'node:assert/strict';
import { isCanonicalLayer, scanCanonicalText } from './check-canonical-vendor-literals.mjs';

test('canonical-layer scoping: cards and canonical dirs in; adapters and v0 docs out', () => {
  assert.ok(isCanonicalLayer('plugins/x/p/skill-card.yaml'));
  assert.ok(isCanonicalLayer('plugins/x/p/canonical/body.md'));
  assert.ok(!isCanonicalLayer('scripts/adapters/claude-code-adapter.mjs'));
  assert.ok(!isCanonicalLayer('schemas/canonical/v0/skill-contract.schema.json'));
  assert.ok(!isCanonicalLayer('plugins/x/p/skills/a/SKILL.md'));
});

test('red runs — each of the five vendor-literal classes is refused', () => {
  const cases = [
    ['model_class: balanced\nmodel: claude-sonnet-4\n', 'model-literal'],
    ['read ${CLAUDE_SKILL_DIR}/x\n', 'harness-variable'],
    ['uses mcp__plane__create_issue\n', 'mcp-spelling'],
    ['allow Bash(jq:*)\n', 'tool-scoping'],
    ['disallowedTools:\n', 'denylist-field'],
    ['disallowed-tools: rm\n', 'denylist-field'],
  ];
  for (const [text, kind] of cases) {
    const v = scanCanonicalText('plugins/x/p/skill-card.yaml', text);
    assert.ok(
      v.some((x) => x.kind === kind),
      `${JSON.stringify(text)} must trip ${kind}`,
    );
  }
});

test('clean canonical text passes; bead handles stay protected', () => {
  const clean = [
    'id: plane',
    'model_class: balanced',
    'capabilities:',
    '  - filesystem.read',
    '  - shell.exec: { commands: [jq] }',
    'intent: tracked by bead claude-t9s9.7',
    'uses ${SKILL_DIR}/references/x.md and ${PLANE_API_KEY}',
  ].join('\n');
  assert.deepEqual(scanCanonicalText('plugins/x/p/skill-card.yaml', clean), []);
});

test('prose model mentions are still violations in canonical files — only bead handles pass', () => {
  const v = scanCanonicalText('plugins/x/p/skill-card.yaml', 'faster than claude-fable-5\n');
  assert.equal(v.length, 1);
  assert.equal(v[0].kind, 'model-literal');
});
