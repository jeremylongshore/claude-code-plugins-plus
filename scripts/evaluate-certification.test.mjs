import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const script = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  'evaluate-certification.mjs',
);

function write(dir, name, value) {
  const target = path.join(dir, name);
  fs.writeFileSync(target, JSON.stringify(value, null, 2));
  return target;
}

function inputs(dir, overrides = {}) {
  const artifact = 'plugins/example/skills/example/SKILL.md';
  return {
    validator: write(dir, 'validator.json', {
      artifacts: [
        {
          path: artifact,
          errors: 0,
          gates: Object.fromEntries(Array.from({ length: 10 }, (_, i) => [`G${i + 1}`, true])),
        },
      ],
      ...overrides.validator,
    }),
    scanner: write(dir, 'scanner.json', { findings: [], ...overrides.scanner }),
    ledger: write(dir, 'ledger.json', {
      records: [
        {
          artifact_path: artifact,
          evidence_class: 'E3',
          artifact_uri: 'artifact.json',
          artifact_sha256: 'a'.repeat(64),
          baseline_delta: -1,
          recorded_by_identity: 'ci',
          producing_identity: 'lab',
          provenance_hash: 'b'.repeat(64),
        },
      ],
      ...overrides.ledger,
    }),
    dispositions: write(dir, 'dispositions.json', {
      artifacts: [{ path: artifact, disposition: 'CERTIFY' }],
      ...overrides.dispositions,
    }),
    artifact,
  };
}

function run(args) {
  return execFileSync(process.execPath, [script, ...args], { encoding: 'utf8' });
}

test('machine facts produce a per-artifact certified verdict and compatible counts', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'certification-'));
  const source = inputs(dir);
  const out = path.join(dir, 'certification-report.json');
  run([
    '--validator',
    source.validator,
    '--scanner',
    source.scanner,
    '--ledger',
    source.ledger,
    '--dispositions',
    source.dispositions,
    '--out',
    out,
  ]);
  const report = JSON.parse(fs.readFileSync(out, 'utf8'));
  assert.equal(report.schema_version, 'certification-report/v1');
  assert.equal(report.certified, 1);
  assert.equal(report.pending, 0);
  assert.deepEqual(report.artifacts[0], {
    path: source.artifact,
    verdict: 'CERTIFIED',
    evidence_class: 'E3',
    reason_codes: [],
  });
});

test('failed validator, REFUSE, missing ledger, and non-certify disposition stay machine-visible', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'certification-'));
  const source = inputs(dir, {
    validator: {
      artifacts: [
        { path: 'plugins/example/skills/example/SKILL.md', errors: 2, gates: { G1: true } },
      ],
    },
    scanner: { findings: [{ path: 'plugins/example/skills/example/SKILL.md', class: 'REFUSE' }] },
    ledger: { records: [] },
    dispositions: {
      artifacts: [{ path: 'plugins/example/skills/example/SKILL.md', disposition: 'QUARANTINE' }],
    },
  });
  const out = path.join(dir, 'certification-report.json');
  run([
    '--validator',
    source.validator,
    '--scanner',
    source.scanner,
    '--ledger',
    source.ledger,
    '--dispositions',
    source.dispositions,
    '--out',
    out,
  ]);
  const [artifact] = JSON.parse(fs.readFileSync(out, 'utf8')).artifacts;
  assert.equal(artifact.verdict, 'NOT-CERTIFIED');
  assert.equal(artifact.evidence_class, 'E0');
  assert.ok(artifact.reason_codes.includes('G1-VALIDATOR-ERRORS'));
  assert.ok(artifact.reason_codes.includes('G2-REFUSE'));
  assert.ok(artifact.reason_codes.includes('D-DISPOSITION-NOT-CERTIFY'));
  assert.ok(artifact.reason_codes.includes('E-EVIDENCE-MISSING'));
  assert.ok(artifact.reason_codes.includes('G10-UNSATISFIED'));
});

test('removing each required input emits NOT-CERTIFIED with E-EVIDENCE-UNAVAILABLE', () => {
  for (const removed of ['validator', 'scanner', 'ledger', 'dispositions']) {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'certification-'));
    const source = inputs(dir);
    fs.rmSync(source[removed]);
    const out = path.join(dir, 'certification-report.json');
    run([
      '--validator',
      source.validator,
      '--scanner',
      source.scanner,
      '--ledger',
      source.ledger,
      '--dispositions',
      source.dispositions,
      '--out',
      out,
    ]);
    const report = JSON.parse(fs.readFileSync(out, 'utf8'));
    assert.equal(report.verdict, 'NOT-CERTIFIED', removed);
    assert.deepEqual(report.reason_codes, ['E-EVIDENCE-UNAVAILABLE'], removed);
    assert.equal(report.input_failures[0].label, removed);
    assert.equal(report.input_failures[0].code, 'MISSING_OR_UNREADABLE');
  }
});

test('unreadable and stale input emit E-EVIDENCE-UNAVAILABLE', () => {
  for (const mode of ['unreadable', 'stale']) {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'certification-'));
    const source = inputs(dir);
    if (mode === 'unreadable') {
      fs.rmSync(source.scanner);
      fs.mkdirSync(source.scanner);
    } else {
      const stale = new Date(Date.now() - 2 * 60 * 60 * 1000);
      fs.utimesSync(source.ledger, stale, stale);
    }
    const out = path.join(dir, 'certification-report.json');
    run([
      '--validator',
      source.validator,
      '--scanner',
      source.scanner,
      '--ledger',
      source.ledger,
      '--dispositions',
      source.dispositions,
      '--out',
      out,
      '--max-age-hours',
      '1',
    ]);
    const report = JSON.parse(fs.readFileSync(out, 'utf8'));
    assert.equal(report.verdict, 'NOT-CERTIFIED', mode);
    assert.ok(report.reason_codes.includes('E-EVIDENCE-UNAVAILABLE'), mode);
    assert.equal(report.input_failures.length, 1, mode);
  }
});
