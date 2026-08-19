import { test } from 'node:test';
import { equal, ok, match } from 'node:assert/strict';
import { analyzeSkill } from './check-denylist-degradation.mjs';

const skill = (fields) => `---\nname: probe\n${fields}\n---\n\n# Probe\n`;

test('a skill without a denylist is out of scope', () => {
  const result = analyzeSkill(
    'plugins/x/skills/p/SKILL.md',
    skill('compatibility: Works with Codex'),
  );
  equal(result.denylist, false);
  equal(result.issues.length, 0);
});

test('denylist plus the truthful claude-code claim passes', () => {
  const result = analyzeSkill(
    'plugins/x/skills/p/SKILL.md',
    skill('disallowed-tools: Bash(rm:*)\ncompatibility: Designed for Claude Code'),
  );
  equal(result.denylist, true);
  equal(result.issues.length, 0);
});

test('denylist plus a foreign-harness claim is silent drop and fails', () => {
  const result = analyzeSkill(
    'plugins/x/skills/p/SKILL.md',
    skill('disallowed-tools: Bash(rm:*)\ncompatibility: Claude Code and Codex'),
  );
  equal(result.issues.length, 1);
  match(result.issues[0], /silent drop/);
});

test('every non-claude-code harness in the registry is caught', () => {
  for (const name of ['codex', 'cursor', 'windsurf', 'aider', 'cline']) {
    const result = analyzeSkill(
      'plugins/x/skills/p/SKILL.md',
      skill(`disallowed-tools: Bash(rm:*)\ncompatibility: Also great on ${name}`),
    );
    ok(result.issues.length >= 1, name);
  }
});
