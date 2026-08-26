import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const directory = path.dirname(fileURLToPath(import.meta.url));
const emitter = path.join(directory, 'emit-evidence.ts');

function run(args) {
  return spawnSync(process.execPath, ['--experimental-strip-types', emitter, ...args], {
    cwd: path.resolve(directory, '../..'),
    encoding: 'utf8',
  });
}

function report(artifacts) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'certification-report-'));
  const file = path.join(dir, 'certification-report.json');
  fs.writeFileSync(file, JSON.stringify({ schema_version: 'certification-report/v1', artifacts }));
  return { dir, file };
}

test('emits a kernel-valid gate-result row for each certification verdict', () => {
  const input = report([
    {
      path: 'plugins/example/skills/one/SKILL.md',
      verdict: 'CERTIFIED',
      evidence_class: 'E3',
      reason_codes: [],
    },
    {
      path: 'plugins/example/skills/two/SKILL.md',
      verdict: 'NOT-CERTIFIED',
      evidence_class: 'E0',
      reason_codes: ['G2-REFUSE'],
    },
  ]);
  const output = path.join(input.dir, 'evidence');
  const result = run([
    '--out',
    output,
    '--certification-report',
    input.file,
    '--certification-only',
  ]);
  assert.equal(result.status, 0, result.stderr);
  const first = JSON.parse(fs.readFileSync(path.join(output, 'gate-result-0.json'), 'utf8'));
  const second = JSON.parse(fs.readFileSync(path.join(output, 'gate-result-1.json'), 'utf8'));
  assert.equal(first.gate_decision, 'pass');
  assert.equal(first.metadata.artifact_path, 'plugins/example/skills/one/SKILL.md');
  assert.equal(second.gate_decision, 'fail');
  assert.deepEqual(second.gate_reasons, ['G2-REFUSE']);
  assert.match(second.input_hash, /^sha256:[a-f0-9]{64}$/);
});

test('refuses a malformed certification report instead of omitting its evidence', () => {
  const input = report([{ path: 'plugins/example/skills/one/SKILL.md', verdict: 'CERTIFIED' }]);
  const result = run([
    '--out',
    path.join(input.dir, 'evidence'),
    '--certification-report',
    input.file,
    '--certification-only',
  ]);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /invalid certification report/);
});
