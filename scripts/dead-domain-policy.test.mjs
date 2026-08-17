import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';

import {
  DEAD_DOMAIN,
  LIVE_DOMAIN,
  VERIFIED_CONTACT_EMAIL,
  classifyDomainPath,
  domainPolicyAllows,
  normalizeDeadDomainValue,
  scanDeadDomainPolicy,
} from './dead-domain-policy.mjs';

function fixture() {
  return mkdtempSync(join(tmpdir(), 'dead-domain-policy-'));
}

function put(root, path, value = '') {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, value);
  return target;
}

function sourceRecord() {
  return JSON.stringify({ synced_from: { repo: 'owner/repo', path: '/' } });
}

function frozenRecord() {
  return `<!-- doc-class: frozen -->\n\n> **SUPERSEDED–FROZEN (fixture).** Retained.\n\n${DEAD_DOMAIN}\n`;
}

function evidence(path, content) {
  return new Map([[path, createHash('sha256').update(content).digest('hex')]]);
}

test('red proof: an actionable first-party reference is refused until replaced', () => {
  const root = fixture();
  put(root, 'docs/live.md', `https://${DEAD_DOMAIN}/install\n`);
  let report = scanDeadDomainPolicy({ root, paths: ['docs/live.md'] });
  assert.equal(report.actionable.occurrences, 1, 'RED: the pre-gate tree is publishable-looking');
  assert.equal(domainPolicyAllows(report), false);

  put(root, 'docs/live.md', `https://${LIVE_DOMAIN}/install\n`);
  report = scanDeadDomainPolicy({ root, paths: ['docs/live.md'] });
  assert.equal(report.actionable.occurrences, 0);
  assert.equal(domainPolicyAllows(report), true);
});

test('mixed-case retired-domain content cannot bypass the policy', () => {
  const root = fixture();
  put(root, 'README.md', `https://${['ClaudeCode', 'Plugins.IO'].join('')}`);
  const report = scanDeadDomainPolicy({ root, paths: ['README.md'] });
  assert.equal(report.first_party_source.occurrences, 1);
  assert.equal(domainPolicyAllows(report), false);
});

test('generator normalization replaces every casing in nested string values', () => {
  const value = normalizeDeadDomainValue({
    url: `https://${['ClaudeCode', 'Plugins.IO'].join('')}`,
    nested: [`plugins@${DEAD_DOMAIN}`, `Mattyp <mattyp@${DEAD_DOMAIN}>`, 7],
    author: { name: 'Mattyp', email: `mattyp@${DEAD_DOMAIN}` },
  });
  assert.deepEqual(value, {
    url: `https://${LIVE_DOMAIN}`,
    nested: [VERIFIED_CONTACT_EMAIL, 'Mattyp', 7],
    author: { name: 'Mattyp' },
  });
});

test('frozen records and valid provenance mirrors are retained and enumerated', () => {
  const root = fixture();
  const frozenPath = '000-docs/6767-h-SPEC-DR-STND-claude-code-extensions-master.md';
  const frozen = frozenRecord();
  put(root, frozenPath, frozen);
  put(root, 'plugins/mirror/.source.json', sourceRecord());
  put(root, 'plugins/mirror/README.md', DEAD_DOMAIN);
  const report = scanDeadDomainPolicy({
    root,
    paths: [frozenPath, 'plugins/mirror/.source.json', 'plugins/mirror/README.md'],
    retainedEvidence: evidence(frozenPath, frozen),
  });
  assert.deepEqual(report.frozen_record.paths, [frozenPath]);
  assert.deepEqual(report.provenance_mirror.paths, ['plugins/mirror/README.md']);
  assert.equal(report.actionable.occurrences, 0);
  assert.equal(domainPolicyAllows(report), true);
});

test('the byte-pinned 6767 anchor manifest remains a frozen projection', () => {
  const root = fixture();
  const path = 'tests/fixtures/prose-anchors/expected-output.json';
  const content = JSON.stringify({ title: `Marketplace (${DEAD_DOMAIN}) Safety Contract` });
  put(root, path, content);

  let report = scanDeadDomainPolicy({
    root,
    paths: [path],
    retainedEvidence: evidence(path, content),
  });
  assert.deepEqual(report.frozen_record.paths, [path]);
  assert.equal(report.frozen_record.occurrences, 1);
  assert.equal(domainPolicyAllows(report), true);

  put(root, path, `${content}\n`);
  report = scanDeadDomainPolicy({
    root,
    paths: [path],
    retainedEvidence: evidence(path, content),
  });
  assert.equal(report.refused[0].reasonCode, 'FROZEN_RECORD_BYTE_DRIFT');
  assert.equal(domainPolicyAllows(report), false);
});

test('a new 6767-shaped file cannot self-register as frozen', () => {
  const root = fixture();
  const injected = ['000-docs/6767-z-', 'injected.md'].join('');
  put(root, injected, DEAD_DOMAIN);
  const report = scanDeadDomainPolicy({ root, paths: [injected] });
  assert.deepEqual(report.first_party_source.paths, [injected]);
  assert.equal(domainPolicyAllows(report), false);
});

test('an exact frozen path without its governed marker fails closed', () => {
  const root = fixture();
  const path = '000-docs/6767-a-SPEC-DR-STND-claude-code-plugins-standard.md';
  const content = DEAD_DOMAIN;
  put(root, path, content);
  const report = scanDeadDomainPolicy({
    root,
    paths: [path],
    retainedEvidence: evidence(path, content),
  });
  assert.equal(report.refused[0].reasonCode, 'INVALID_FROZEN_RECORD_MARKER');
});

test('generated projections remain actionable but are classified separately', () => {
  const root = fixture();
  put(root, 'marketplace/src/data/catalog.json', JSON.stringify({ url: DEAD_DOMAIN }));
  put(root, 'marketplace/src/content/plugins/example.json', JSON.stringify({ url: DEAD_DOMAIN }));
  put(root, 'plugins/example/example/package.json', JSON.stringify({ homepage: DEAD_DOMAIN }));
  put(root, 'skills/.curated/example/SKILL.md', DEAD_DOMAIN);
  const report = scanDeadDomainPolicy({
    root,
    paths: [
      'marketplace/src/data/catalog.json',
      'marketplace/src/content/plugins/example.json',
      'plugins/example/example/package.json',
      'skills/.curated/example/SKILL.md',
    ],
  });
  assert.equal(report.generated_projection.files, 4);
  assert.equal(report.actionable.occurrences, 4);
  assert.equal(domainPolicyAllows(report), false);
});

test('point-in-time Freshie exports are retained as historical evidence', () => {
  const root = fixture();
  const path = 'freshie/exports/run-1/plugin_values.json';
  const content = JSON.stringify({ value: DEAD_DOMAIN });
  put(root, path, content);
  const report = scanDeadDomainPolicy({
    root,
    paths: [path],
    retainedEvidence: evidence(path, content),
  });
  assert.equal(report.historical_snapshot.occurrences, 1);
  assert.equal(report.actionable.occurrences, 0);
  assert.equal(domainPolicyAllows(report), true);
});

test('new snapshots and modified frozen evidence fail closed', () => {
  const root = fixture();
  const frozenPath = '000-docs/6767-h-SPEC-DR-STND-claude-code-extensions-master.md';
  const original = frozenRecord();
  put(root, frozenPath, `${original}modified\n`);
  const injected = 'freshie/exports/run-999/plugin_values.json';
  put(root, injected, JSON.stringify({ value: DEAD_DOMAIN }));

  const report = scanDeadDomainPolicy({
    root,
    paths: [frozenPath, injected],
    retainedEvidence: evidence(frozenPath, original),
  });
  assert.deepEqual(
    report.refused.map((row) => row.reasonCode),
    ['FROZEN_RECORD_BYTE_DRIFT', 'UNREGISTERED_HISTORICAL_SNAPSHOT'],
  );
  assert.equal(domainPolicyAllows(report), false);
});

test('byte-pinned retained evidence is checked even without the retired domain', () => {
  const root = fixture();
  const path = 'freshie/exports/run-1/plugin_fields.json';
  put(root, path, '{"state":"changed"}');
  const report = scanDeadDomainPolicy({
    root,
    paths: [path],
    retainedEvidence: evidence(path, '{"state":"original"}'),
  });
  assert.equal(report.refused[0].reasonCode, 'HISTORICAL_SNAPSHOT_BYTE_DRIFT');
  assert.equal(domainPolicyAllows(report), false);
});

test('nested provenance applies, while a sibling marker creates no false positive', () => {
  const root = fixture();
  put(root, 'plugins/nested/.source.json', sourceRecord());
  put(root, 'plugins/nested/skill/README.md', DEAD_DOMAIN);
  put(root, 'plugins/sibling/.source.json', sourceRecord());
  put(root, 'plugins/first-party/README.md', DEAD_DOMAIN);
  const report = scanDeadDomainPolicy({
    root,
    paths: [
      'plugins/nested/.source.json',
      'plugins/nested/skill/README.md',
      'plugins/sibling/.source.json',
      'plugins/first-party/README.md',
    ],
  });
  assert.deepEqual(report.provenance_mirror.paths, ['plugins/nested/skill/README.md']);
  assert.deepEqual(report.first_party_source.paths, ['plugins/first-party/README.md']);
});

test('malformed and non-regular provenance fail closed', () => {
  const malformedRoot = fixture();
  put(malformedRoot, 'plugins/bad/.source.json', '{bad-json');
  put(malformedRoot, 'plugins/bad/README.md', DEAD_DOMAIN);
  const malformed = scanDeadDomainPolicy({
    root: malformedRoot,
    paths: ['plugins/bad/.source.json', 'plugins/bad/README.md'],
  });
  assert.equal(malformed.refused[0].reasonCode, 'MALFORMED_SOURCE_RECORD');
  assert.equal(domainPolicyAllows(malformed), false);

  const nonRegularRoot = fixture();
  mkdirSync(join(nonRegularRoot, 'plugins/non-regular/.source.json'), { recursive: true });
  put(nonRegularRoot, 'plugins/non-regular/README.md', DEAD_DOMAIN);
  const nonRegular = scanDeadDomainPolicy({
    root: nonRegularRoot,
    paths: ['plugins/non-regular/README.md'],
  });
  assert.equal(nonRegular.refused[0].reasonCode, 'SOURCE_RECORD_NOT_REGULAR');
  assert.equal(domainPolicyAllows(nonRegular), false);
});

test('all tracked bytes are searched, including extensions the old allowlist missed', () => {
  const root = fixture();
  put(root, 'assets/logo.svg', `<text>${DEAD_DOMAIN}</text>`);
  const report = scanDeadDomainPolicy({ root, paths: ['assets/logo.svg'] });
  assert.equal(report.actionable.occurrences, 1, 'RED: the former extension allowlist missed SVG');
  assert.equal(domainPolicyAllows(report), false);
});

test('measurement outputs are governed generated projections, never exempt', () => {
  const root = fixture();
  put(root, '000-docs/742-RA-DATA-epic-1-scorecard.json', JSON.stringify({ value: DEAD_DOMAIN }));
  const report = scanDeadDomainPolicy({
    root,
    paths: ['000-docs/742-RA-DATA-epic-1-scorecard.json'],
  });
  assert.equal(report.generated_projection.occurrences, 1);
  assert.equal(domainPolicyAllows(report), false);
});

test('unmerged index entries and tracked symlinks are refused before reads', () => {
  const root = fixture();
  const report = scanDeadDomainPolicy({
    root,
    paths: [
      { mode: '100644', path: 'conflict.md', stage: 2 },
      { mode: '120000', path: 'link.md', stage: 0 },
    ],
  });
  assert.deepEqual(
    report.refused.map((row) => row.reasonCode),
    ['UNRESOLVED_INDEX_ENTRY', 'TRACKED_SYMLINK'],
  );
});

test('path traversal is refused before filesystem access', () => {
  const result = classifyDomainPath('../outside.md', { root: fixture() });
  assert.equal(result.category, 'refused');
  assert.equal(result.reasonCode, 'PATH_TRAVERSAL');
});
