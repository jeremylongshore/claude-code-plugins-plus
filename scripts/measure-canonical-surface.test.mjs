import test from 'node:test';
import assert from 'node:assert/strict';
import { classifyModelToken, classifyPath } from './measure-canonical-surface.mjs';

test('bead handles are protected — never functional or prose', () => {
  // the three shapes the blueprint names, plus live handles from this program
  for (const handle of [
    'claude-hz8f',
    'claude-hedb.11',
    'claude-t9s9.1',
    'claude-4laa.1',
    'claude-5awj.6',
  ]) {
    assert.equal(
      classifyModelToken(handle, `model: ${handle}`),
      'bead-id',
      `${handle} must stay in the protected class even on a functional-looking line`,
    );
  }
});

test('real model ids classify functional on config lines, prose elsewhere', () => {
  assert.equal(classifyModelToken('claude-sonnet-4', 'model: claude-sonnet-4'), 'functional');
  assert.equal(classifyModelToken('claude-3-5-haiku', '"model": "claude-3-5-haiku"'), 'functional');
  assert.equal(classifyModelToken('claude-opus-4-1', '--model claude-opus-4-1'), 'functional');
  assert.equal(
    classifyModelToken('claude-fable-5', 'Fable is faster than claude-fable-5 predecessors.'),
    'prose',
  );
  assert.equal(classifyModelToken('claude-2.1', 'the claude-2.1 era'), 'prose');
});

test('surface class: mirror beats generated beats first-party', () => {
  const mirrors = ['plugins/design/uizze'];
  assert.equal(classifyPath('plugins/design/uizze/README.md', mirrors), 'mirror');
  assert.equal(classifyPath('marketplace/src/data/skills-index.json', mirrors), 'generated');
  assert.equal(classifyPath('skills/.curated/x/SKILL.md', mirrors), 'generated');
  assert.equal(classifyPath('plugins/devops/foo/SKILL.md', mirrors), 'first-party');
  assert.equal(classifyPath('000-docs/742-RA-DATA-epic-1-scorecard.json', mirrors), 'generated');
});
