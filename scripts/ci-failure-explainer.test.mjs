/**
 * ci-failure-explainer.test.mjs
 *
 * Locks the deterministic CI-failure → contributor-fix catalog and the
 * marker-anchored, byte-stable comment renderer. Run:
 *   node --test scripts/ci-failure-explainer.test.mjs
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  explain,
  renderComment,
  summarize,
  SIGNATURE_CATALOG,
  MARKER_OPEN,
  MARKER_CLOSE,
} from './ci-failure-explainer.mjs';

const TS = '2026-07-22T00:00:00.000Z'; // fixed — explain() is pure given a timestamp

const idsFor = (checks) => explain(checks, TS).results.map((r) => r.id);

test('ERR_PNPM_OUTDATED_LOCKFILE → deps:lockfile-stale with the lockfile-only fix', () => {
  const r = explain(
    [{ name: 'eslint-check', text: 'ERR_PNPM_OUTDATED_LOCKFILE Cannot install' }],
    TS,
  ).results;
  assert.equal(r.length, 1);
  assert.equal(r[0].id, 'deps:lockfile-stale');
  assert.equal(r[0].severity, 'error');
  assert.match(r[0].details, /pnpm install --lockfile-only/);
});

test('markdownlint rule codes are extracted into the message', () => {
  const text = 'README.md:125 MD032/blanks-around-lists\nSKILL.md:5 MD022/blanks-around-headings';
  const r = explain([{ name: 'markdownlint', text }], TS).results;
  assert.equal(r[0].id, 'docs:markdownlint');
  assert.match(r[0].message, /MD022/);
  assert.match(r[0].message, /MD032/);
});

test('MISSING required document → docs:submission-missing naming the docs', () => {
  const text =
    'MISSING required document: plugins/mcp/x/docs/PRD.md\nMISSING required document: plugins/mcp/x/docs/ADR.md';
  const r = explain([{ name: 'check-submission-docs', text }], TS).results;
  assert.equal(r[0].id, 'docs:submission-missing');
  assert.match(r[0].message, /PRD\.md/);
  assert.match(r[0].message, /ADR\.md/);
  assert.match(r[0].details, /templates\/skill-docs/);
});

test('format-check → style:prettier; standalone eslint → lint:eslint', () => {
  assert.deepEqual(idsFor([{ name: 'format-check', text: 'not formatted' }]), ['style:prettier']);
  assert.deepEqual(idsFor([{ name: 'eslint-check', text: 'some eslint problem' }]), [
    'lint:eslint',
  ]);
});

test('validate check → validate:marketplace', () => {
  assert.deepEqual(idsFor([{ name: 'validate', text: 'exit code 1' }]), ['validate:marketplace']);
  assert.deepEqual(idsFor([{ name: 'x', text: 'validate-skills-schema.py ERROR' }]), [
    'validate:marketplace',
  ]);
});

test('unknown check falls through to a generic explanation with the log link', () => {
  const r = explain([{ name: 'mystery-gate', text: 'weird', url: 'https://gh/job/9' }], TS).results;
  assert.equal(r[0].id, 'check:mystery-gate');
  assert.match(r[0].details, /https:\/\/gh\/job\/9/);
});

test('duplicate signatures de-dupe by id (lockfile hit by two checks → one result)', () => {
  const r = explain(
    [
      { name: 'eslint-check', text: 'ERR_PNPM_OUTDATED_LOCKFILE' },
      { name: 'cli-smoke-tests', text: 'ERR_PNPM_OUTDATED_LOCKFILE' },
    ],
    TS,
  ).results;
  assert.equal(r.length, 1);
  assert.equal(r[0].id, 'deps:lockfile-stale');
});

test('the real #1101 failure set produces the expected distinct fixes', () => {
  const ids = idsFor([
    { name: 'eslint-check', text: 'ERR_PNPM_OUTDATED_LOCKFILE' },
    { name: 'cli-smoke-tests', text: 'ERR_PNPM_OUTDATED_LOCKFILE' },
    { name: 'markdownlint', text: 'MD022 MD032 MD047' },
    { name: 'check-submission-docs', text: 'MISSING required document: docs/PRD.md' },
    { name: 'validate', text: 'exit code 1' },
  ]);
  assert.deepEqual(
    new Set(ids),
    new Set([
      'deps:lockfile-stale',
      'docs:markdownlint',
      'docs:submission-missing',
      'validate:marketplace',
    ]),
  );
});

test('renderComment is marker-wrapped and byte-stable for the same input', () => {
  const checks = [{ name: 'markdownlint', text: 'MD022' }];
  const a = renderComment(explain(checks, TS));
  const b = renderComment(explain(checks, TS));
  assert.equal(a, b, 'same report must render byte-identical');
  assert.ok(a.startsWith(MARKER_OPEN), 'opens with the idempotence marker');
  assert.ok(a.trimEnd().endsWith(MARKER_CLOSE), 'closes with the marker');
  assert.match(a, /MD022/);
});

test('summarize counts severities', () => {
  const s = summarize([{ severity: 'error' }, { severity: 'error' }, { severity: 'pass' }]);
  assert.deepEqual(s, { total: 3, passed: 1, warnings: 0, errors: 2 });
});

test('every catalog entry has an id, appliesTo, and toResult returning a CheckResult', () => {
  for (const e of SIGNATURE_CATALOG) {
    assert.equal(typeof e.id, 'string');
    assert.equal(typeof e.appliesTo, 'function');
    const res = e.toResult('x', 'MD001 ERR_PNPM_OUTDATED_LOCKFILE MISSING required document: a/b');
    assert.equal(typeof res.id, 'string');
    assert.ok(['error', 'warning', 'pass'].includes(res.severity));
    assert.equal(typeof res.message, 'string');
  }
});
