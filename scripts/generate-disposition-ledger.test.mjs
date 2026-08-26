import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { classifyArtifact, parseGrades } from './generate-disposition-ledger.mjs';

test('parseGrades rejects duplicate and unsafe inventory rows', () => {
  assert.throws(() => parseGrades('skill_path,grade,score\na,A,99\na,A,99\n'), /duplicate/);
  assert.throws(() => parseGrades('skill_path,grade,score\n../a,A,99\n'), /unsafe/);
});

test('G0 shell substitution wins before all later facts', () => {
  const root = mkdtempSync(path.join(os.tmpdir(), 'ledger-'));
  mkdirSync(path.join(root, 'plugins/example/skill'), { recursive: true });
  writeFileSync(
    path.join(root, 'plugins/example/skill/SKILL.md'),
    '---\nname: x\nvalue: $(whoami)\n---\nbody\n',
  );
  const result = classifyArtifact({
    root,
    row: { path: 'plugins/example/skill/SKILL.md', grade: 'A', score: 99 },
    validation: { errors: 0, error_details: [] },
  });
  assert.deepEqual([result.gate, result.disposition], ['G0', 'QUARANTINE']);
});

test('structural failures auto-migrate and unknown failures require deep remediation', () => {
  const root = mkdtempSync(path.join(os.tmpdir(), 'ledger-'));
  mkdirSync(path.join(root, 'plugins/example/skill'), { recursive: true });
  writeFileSync(path.join(root, 'plugins/example/skill/SKILL.md'), '---\nname: x\n---\nbody\n');
  const row = { path: 'plugins/example/skill/SKILL.md', grade: 'B', score: 82 };
  const structural = classifyArtifact({
    root,
    row,
    validation: {
      errors: 1,
      error_details: ["[frontmatter] Missing required field: 'license' (marketplace)"],
    },
  });
  assert.deepEqual([structural.gate, structural.disposition], ['G5', 'AUTO-MIGRATE']);
  const deep = classifyArtifact({
    root,
    row,
    validation: { errors: 1, error_details: ['[body] invalid substantive claim'] },
  });
  assert.deepEqual([deep.gate, deep.disposition], ['G4', 'DEEP-REMEDIATE']);
});
