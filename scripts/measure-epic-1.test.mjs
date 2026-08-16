import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';

import {
  artifactMatches,
  buildReport,
  matchesSignature,
  parseSkillRows,
  parseTerminalSummary,
  stableJson,
  trackedPaths,
} from './measure-epic-1.mjs';

function put(root, path, contents = '') {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, contents);
}

function evidence(rows = 2) {
  const skills = Array.from({ length: rows }, (_, index) => ({
    errors: index === 0 ? 1 : 0,
    grade: index === 0 ? 'A' : 'B',
    path: `plugins/example/skills/s${index}/SKILL.md`,
    warnings: 0,
  }));
  return {
    agents: `Agents validated: 1\nTotal files: 1\n✅ Fully compliant: 1\n📈 Compliance rate: 100.0%\n❌ Validation FAILED with 0 errors (standard tier)`,
    marketplace: `Skills validated: ${rows}\nCommands validated: 0\nAgents validated: 1\nTotal files: ${rows + 1}\n✅ Fully compliant: 1\n📈 Compliance rate: 33.3%\n❌ Validation FAILED with 1 errors (marketplace tier)`,
    skills,
  };
}

function fixture() {
  const root = mkdtempSync(join(tmpdir(), 'epic-1-measurement-'));
  const files = {
    '.claude-plugin/marketplace.extended.json': JSON.stringify({
      plugins: [{ name: 'alpha' }, { name: 'alpha' }, { name: 'beta' }],
    }),
    '.claude-plugin/marketplace.json': '{}',
    'freshie/grade-histogram.json': JSON.stringify({ total: 7 }),
    'freshie/scripts/promote-to-curated.py': 'return b"\\0" in fh.read(8192)\n',
    'marketplace/src/data/catalog.json': '{}',
    'marketplace/src/data/github-stats.json': JSON.stringify({ generatedAt: 'historical' }),
    'marketplace/src/data/jrig-data.json': '{}',
    'marketplace/src/data/npm-stats.json': JSON.stringify({ generatedAt: 'historical' }),
    'marketplace/src/data/readme-sections.json': '{}',
    'marketplace/src/data/skills-catalog.json': '{}',
    'marketplace/src/data/skills-index.json': JSON.stringify({ count: 8 }),
    'marketplace/src/data/skills-stats.json': JSON.stringify({ generatedAt: 'historical' }),
    'marketplace/src/data/unified-search-index.json': JSON.stringify({ stats: { totalSkills: 9 } }),
    'plugins/example/agents/a.md': '# agent\n',
    'plugins/example/assets/bad.png': 'plain text placeholder',
    'plugins/example/assets/good.png': Buffer.from('89504e470d0a1a0a00000000', 'hex'),
    'plugins/example/SKILL.md': '# skill\n',
    'scripts/generate-readme-toc.mjs': 'const README = "README.md"; const skills = 1;',
    'scripts/update-metrics.mjs': 'const README = "README.md"; const skillCount = 1;',
    'skills/.curated/MANIFEST.json': JSON.stringify({ count: 6 }),
    'sources.lock.json': JSON.stringify({ sources: { alpha: {} } }),
    'sources.yaml': 'sources:\n  - name: alpha\n',
  };
  for (const [path, contents] of Object.entries(files)) put(root, path, contents);
  execFileSync('git', ['init', '-q'], { cwd: root });
  execFileSync('git', ['add', '.'], { cwd: root });
  return root;
}

test('buildReport names cohorts and derives every governed row from tracked fixture evidence', () => {
  const root = fixture();
  const report = buildReport(root, evidence());
  assert.deepEqual(Object.keys(report.rows), [
    '1',
    '2',
    '3',
    '4',
    '11',
    '12',
    '22',
    '24',
    '25',
    '26',
    '27',
  ]);
  assert.equal(report.rows[1].values.plugin_skill_files, 1);
  assert.equal(report.rows[1].values.plugin_agent_files, 1);
  assert.deepEqual(report.rows[2].values.duplicate_names, [{ count: 2, name: 'alpha' }]);
  assert.equal(report.rows[3].values.count, 0);
  assert.equal(report.rows[4].values.skill_rows.rows, 2);
  assert.equal(report.rows[11].values.candidate_count, 2);
  assert.deepEqual(report.rows[11].values.mismatch_paths, ['plugins/example/assets/bad.png']);
  assert.equal(report.rows[12].values.missed_count, 1);
  assert.equal(report.rows[22].values.count, 6);
  assert.deepEqual(report.rows[24].values, {
    curated_manifest: 6,
    freshie_export: 7,
    plugin_source: 1,
    skills_index: 8,
    unified_search_index: 9,
  });
  assert.equal(report.rows[25].values.count, 2);
  assert.equal(report.rows[26].values.count, 3);
  assert.deepEqual(report.rows[27].values, {
    lock_keys: 1,
    lock_only: [],
    yaml_keys: 1,
    yaml_only: [],
  });
});

test('validator parsers fail closed on malformed evidence and missing summaries', () => {
  assert.throws(() => parseSkillRows({}), /must be an array/);
  assert.throws(
    () => parseSkillRows([{ path: 'x', grade: 'A', errors: -1 }]),
    /invalid validator row/,
  );
  assert.throws(() => parseTerminalSummary('Total files: 1', 'marketplace'), /missing error total/);
});

test('grade arithmetic derives the current 3680 cohort rather than preserving historical 3679', () => {
  const rows = Array.from({ length: 3680 }, (_, index) => ({
    errors: 0,
    grade: index === 0 ? 'A' : 'B',
    path: `skill-${index}`,
  }));
  const result = parseSkillRows(rows);
  assert.equal(result.rows, 3680);
  assert.notEqual(result.rows, 3679);
  assert.equal(
    Object.values(result.grade_distribution).reduce((sum, count) => sum + count, 0),
    3680,
  );
});

test('signature registry accepts genuine bytes, exposes counterfeits, and refuses unknown types', () => {
  assert.equal(matchesSignature('.png', Buffer.from('89504e470d0a1a0a', 'hex')), true);
  assert.equal(matchesSignature('.zip', Buffer.from('504b0304', 'hex')), true);
  assert.equal(matchesSignature('.pdf', Buffer.from('plain text')), false);
  assert.throws(
    () => matchesSignature('.exe', Buffer.alloc(4)),
    /unknown governed binary extension/,
  );
});

test('Git, catalog, source, and detector contradictions fail closed', () => {
  const empty = mkdtempSync(join(tmpdir(), 'epic-1-empty-'));
  execFileSync('git', ['init', '-q'], { cwd: empty });
  assert.throws(() => trackedPaths(empty), /inventory is empty/);

  const duplicateSource = fixture();
  put(duplicateSource, 'sources.yaml', 'sources:\n  - name: alpha\n  - name: alpha\n');
  assert.throws(() => buildReport(duplicateSource, evidence()), /duplicate source names/);

  const unknownDetector = fixture();
  put(unknownDetector, 'freshie/scripts/promote-to-curated.py', 'return False\n');
  assert.throws(
    () => buildReport(unknownDetector, evidence()),
    /unknown promotion binary-detector shape/,
  );
});

test('stable output excludes runtime metadata and byte comparison catches one-value drift', () => {
  const rendered = stableJson({ rows: { 1: { values: { count: 2 } } }, schema_version: 1 });
  assert.equal(rendered.endsWith('\n'), true);
  assert.equal(rendered.includes(tmpdir()), false);
  assert.equal(rendered.includes('captured_at'), false);
  assert.equal(artifactMatches(rendered, rendered), true);
  assert.equal(artifactMatches(rendered.replace('2', '3'), rendered), false);
  assert.throws(() => stableJson({ generated_at: 'now' }), /nondeterministic metadata/);
});
