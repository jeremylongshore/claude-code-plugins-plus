/* global process */

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

test('emits one content-bound signed-ready row per completed publication', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'publication-report-'));
  const file = path.join(dir, 'publication-report.json');
  fs.writeFileSync(
    file,
    JSON.stringify({
      schema_version: 'publication-report/v1',
      publications: [
        {
          channel: 'npm',
          name: '@intentsolutionsio/example',
          version: '1.2.3',
          release_tag: '@intentsolutionsio/example@1.2.3',
          artifact_digest: `sha256:${'a'.repeat(64)}`,
          sbom_digest: `sha256:${'b'.repeat(64)}`,
          sbom_format: 'CycloneDX',
        },
        {
          channel: 'mcp-registry',
          name: 'project-health-auditor',
          version: '1.0.0',
          sbom_digest: `sha256:${'c'.repeat(64)}`,
          sbom_format: 'CycloneDX',
        },
      ],
    }),
  );
  const output = path.join(dir, 'evidence');
  const result = run(['--out', output, '--publication-report', file, '--publication-only']);
  assert.equal(result.status, 0, result.stderr);
  const first = JSON.parse(fs.readFileSync(path.join(output, 'gate-result-0.json'), 'utf8'));
  const second = JSON.parse(fs.readFileSync(path.join(output, 'gate-result-1.json'), 'utf8'));
  assert.equal(first.gate_decision, 'pass');
  assert.equal(first.metadata.channel, 'npm');
  assert.equal(first.metadata.artifact_digest, `sha256:${'a'.repeat(64)}`);
  assert.equal(second.metadata.channel, 'mcp-registry');
});

test('refuses a publication report that is only a publish candidate', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'publication-report-'));
  const file = path.join(dir, 'publication-report.json');
  fs.writeFileSync(
    file,
    JSON.stringify({ schema_version: 'publication-report/v1', publications: [] }),
  );
  const result = run([
    '--out',
    path.join(dir, 'evidence'),
    '--publication-report',
    file,
    '--publication-only',
  ]);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /non-empty publications/);
});

test('emits exactly the three completed protected-branch contexts', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'required-checks-'));
  const file = path.join(dir, 'checks.json');
  fs.writeFileSync(
    file,
    JSON.stringify({
      check_runs: [
        { name: 'ci-required', status: 'completed', conclusion: 'success' },
        { name: 'gitleaks', status: 'completed', conclusion: 'success' },
        { name: 'skill-conform', status: 'completed', conclusion: 'success' },
      ],
    }),
  );
  const output = path.join(dir, 'evidence');
  const result = run([
    '--out',
    output,
    '--required-checks-report',
    file,
    '--publication-only',
    '--publication-report',
    (() => {
      const publication = path.join(dir, 'publication.json');
      fs.writeFileSync(
        publication,
        JSON.stringify({
          schema_version: 'publication-report/v1',
          publications: [
            {
              channel: 'npm',
              name: 'x',
              sbom_digest: `sha256:${'d'.repeat(64)}`,
              sbom_format: 'CycloneDX',
            },
          ],
        }),
      );
      return publication;
    })(),
  ]);
  assert.equal(result.status, 0, result.stderr);
  const rows = fs.readdirSync(output).filter((name) => name.startsWith('gate-result-'));
  assert.equal(rows.length, 4);
});

test('refuses an incomplete protected-branch check report', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'required-checks-'));
  const file = path.join(dir, 'checks.json');
  fs.writeFileSync(
    file,
    JSON.stringify({
      check_runs: [{ name: 'ci-required', status: 'completed', conclusion: 'success' }],
    }),
  );
  const result = run([
    '--out',
    path.join(dir, 'evidence'),
    '--required-checks-report',
    file,
    '--publication-only',
    '--publication-report',
    (() => {
      const publication = path.join(dir, 'publication.json');
      fs.writeFileSync(
        publication,
        JSON.stringify({
          schema_version: 'publication-report/v1',
          publications: [
            {
              channel: 'npm',
              name: 'x',
              sbom_digest: `sha256:${'d'.repeat(64)}`,
              sbom_format: 'CycloneDX',
            },
          ],
        }),
      );
      return publication;
    })(),
  ]);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /must appear exactly once/);
});
