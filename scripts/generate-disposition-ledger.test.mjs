import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import {
  assertGradeCorpusParity,
  classifyArtifact,
  parseGrades,
} from './generate-disposition-ledger.mjs';

test('parseGrades rejects duplicate and unsafe inventory rows', () => {
  assert.throws(() => parseGrades('skill_path,grade,score\na,A,99\na,A,99\n'), /duplicate/);
  assert.throws(() => parseGrades('skill_path,grade,score\n../a,A,99\n'), /unsafe/);
});

test('parseGrades uses locale-independent code-point path order', () => {
  const rows = parseGrades('skill_path,grade,score\na,A,99\nB,A,99\n');
  assert.deepEqual(
    rows.map((row) => row.path),
    ['B/SKILL.md', 'a/SKILL.md'],
  );
});

test('graded-corpus parity refuses omitted and stale grade rows', () => {
  const root = mkdtempSync(path.join(os.tmpdir(), 'ledger-'));
  const current = { path: 'plugins/example/current/SKILL.md', grade: 'A', score: 99 };
  const stale = { path: 'plugins/example/stale/SKILL.md', grade: 'B', score: 88 };

  assert.doesNotThrow(() => assertGradeCorpusParity(root, [current], [current.path]));
  assert.throws(
    () =>
      assertGradeCorpusParity(root, [current], [current.path, 'plugins/example/omitted/SKILL.md']),
    /grades export omits 1 graded artifact\(s\): plugins\/example\/omitted\/SKILL\.md/,
  );
  assert.throws(
    () => assertGradeCorpusParity(root, [current, stale], [current.path]),
    /grades export contains 1 artifact\(s\) outside the graded corpus: plugins\/example\/stale\/SKILL\.md/,
  );
});

test('G0 canonical shell-substitution diagnostics win before all later facts', () => {
  const root = mkdtempSync(path.join(os.tmpdir(), 'ledger-'));
  mkdirSync(path.join(root, 'plugins/example/skill'), { recursive: true });
  writeFileSync(path.join(root, 'plugins/example/skill/SKILL.md'), '---\nname: x\n---\nbody\n');
  for (const value of ['$(whoami)', '`whoami`', '${UNGUARDED}']) {
    const result = classifyArtifact({
      root,
      row: { path: 'plugins/example/skill/SKILL.md', grade: 'A', score: 99 },
      validation: {
        errors: 1,
        error_details: [
          `[security] YAML field 'description' contains shell substitution (e.g. $(...), backticks, or \${VAR}) that will not evaluate: '${value}'`,
        ],
      },
    });
    assert.deepEqual(
      [result.gate, result.disposition, result.reason_codes],
      ['G0', 'QUARANTINE', ['SHELL_SUBSTITUTION']],
    );
  }
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

test('ledger diagnostics are serialized in deterministic order', () => {
  const root = mkdtempSync(path.join(os.tmpdir(), 'ledger-'));
  mkdirSync(path.join(root, 'plugins/example/skill'), { recursive: true });
  writeFileSync(path.join(root, 'plugins/example/skill/SKILL.md'), '---\nname: x\n---\nbody\n');
  const result = classifyArtifact({
    root,
    row: { path: 'plugins/example/skill/SKILL.md', grade: 'B', score: 82 },
    validation: {
      errors: [
        "[frontmatter] Missing required field: 'version' (marketplace)",
        "[frontmatter] Missing required field: 'author' (marketplace)",
      ],
    },
  });
  assert.deepEqual(result.diagnostics, [...result.diagnostics].sort());

  const numericResult = classifyArtifact({
    root,
    row: { path: 'plugins/example/skill/SKILL.md', grade: 'B', score: 82 },
    validation: {
      errors: 2,
      error_details: [
        "[frontmatter] Missing required field: 'version' (marketplace)",
        "[frontmatter] Missing required field: 'author' (marketplace)",
      ],
    },
  });
  assert.deepEqual(numericResult.diagnostics, [...numericResult.diagnostics].sort());
});
