import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
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
  withIndexSnapshot,
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
    path: index === 0 ? 'plugins/example/SKILL.md' : `skills/.curated/example-${index}/SKILL.md`,
    warnings: 0,
  }));
  return {
    agents: `Agents validated: 1\nTotal files: 1\n✅ Fully compliant: 1\n📈 Compliance rate: 100.0%\n✅ All skills fully compliant! (standard tier)`,
    marketplace: `Skills validated: ${rows}\nCommands validated: 0\nAgents validated: 1\nTotal files: ${rows + 1}\n✅ Fully compliant: 1\n📈 Compliance rate: 33.3%\n❌ Validation FAILED with 1 errors (marketplace tier)`,
    skills,
  };
}

function fixture() {
  const root = mkdtempSync(join(tmpdir(), 'epic-1-measurement-'));
  const files = {
    '.gitignore': 'plugins/mirror/\n',
    '.claude-plugin/marketplace.extended.json': JSON.stringify({
      plugins: [{ name: 'alpha' }, { name: 'alpha' }, { name: 'beta' }],
    }),
    '.claude-plugin/marketplace.json': '{}',
    '000-docs/canonical.md': '# Canonical\n\n**Status:** AUTHORITATIVE\n',
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
    'skills/.curated/example-1/SKILL.md': '# curated skill\n',
    'sources.lock.json': JSON.stringify({ sources: { alpha: {} } }),
    'sources.yaml': 'sources:\n  - name: alpha\n',
    'STANDARDS.md':
      '## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Fixture | [canonical](000-docs/canonical.md) |\n',
  };
  for (const [path, contents] of Object.entries(files)) put(root, path, contents);
  execFileSync('git', ['init', '-q'], { cwd: root });
  execFileSync('git', ['add', '.'], { cwd: root });
  return root;
}

test('buildReport names cohorts and derives every governed row from tracked fixture evidence', () => {
  const root = fixture();
  const report = buildReport(root, evidence());
  assert.deepEqual(
    Object.keys(report.rows),
    Array.from({ length: 62 }, (_, index) => String(index + 1)),
  );
  assert.equal(report.rows[1].values.plugin_skill_files, 1);
  assert.equal(report.rows[1].values.plugin_agent_files, 1);
  assert.deepEqual(report.rows[2].values.duplicate_names, [{ count: 2, name: 'alpha' }]);
  assert.equal(report.rows[3].values.count, 0);
  assert.equal(report.rows[4].values.skill_rows.rows, 2);
  assert.equal(report.rows[5].values.rows, 2);
  assert.equal(report.rows[11].values.candidate_count, 2);
  assert.deepEqual(report.rows[11].values.mismatch_paths, ['plugins/example/assets/bad.png']);
  assert.equal(report.rows[12].values.missed_count, 1);
  assert.equal(report.rows[22].values.count_without_content_drift_gate, 0);
  assert.equal(report.rows[24].values.named_cohorts, 5);
  assert.equal(report.rows[25].values.count, 0);
  assert.equal(report.rows[26].values.without_valid_bound, 3);
  assert.equal(report.rows[1].reproduce, 'pnpm run measure:e1 --row=1 --stdout');
  assert.deepEqual(report.rows[27].values, {
    lock_keys: 1,
    lock_only: [],
    yaml_keys: 1,
    yaml_only: [],
    target_equal: true,
  });
});

test('validator parsers fail closed on malformed evidence and missing summaries', () => {
  assert.throws(() => parseSkillRows({}), /must be an array/);
  assert.throws(
    () => parseSkillRows([{ path: 'x', grade: 'A', errors: -1 }]),
    /invalid validator row/,
  );
  assert.throws(
    () => parseTerminalSummary('Total files: 1', 'marketplace'),
    /requires exactly one terminal result/,
  );
  assert.throws(
    () =>
      parseSkillRows([
        { errors: 0, grade: 'A', path: 'plugins/a/SKILL.md' },
        { errors: 0, grade: 'A', path: 'plugins/a/SKILL.md' },
      ]),
    /invalid validator row/,
  );
  assert.throws(() => parseSkillRows([{ unexpected: true }]), /unknown non-row record/);
  assert.equal(
    parseTerminalSummary(
      'Agents validated: 1\nTotal files: 1\nFully compliant: 1\nCompliance rate: 100.0%\nAll skills fully compliant! (marketplace tier)',
      'agents',
    ).error_total_all_validated_surfaces,
    0,
  );
  const warningOnly =
    'Agents validated: 1\nTotal files: 1\nFully compliant: 0\nCompliance rate: 0.0%\nValidation PASSED with 1 warnings (standard tier)';
  assert.equal(
    parseTerminalSummary({ output: warningOnly, status: 0 }, 'agents')
      .error_total_all_validated_surfaces,
    0,
  );
  assert.throws(
    () =>
      parseTerminalSummary(
        'Agents validated: 1\nTotal files: 1\nFully compliant: 0\nCompliance rate: 0.0%\nValidation FAILED with 0 errors (standard tier)',
        'agents',
      ),
    /cannot fail with zero errors/,
  );
  assert.throws(
    () => parseTerminalSummary({ output: warningOnly, status: 1 }, 'agents'),
    /contradicts its terminal result/,
  );
  assert.throws(
    () => parseTerminalSummary(`${warningOnly}\n${warningOnly}`, 'agents'),
    /exactly one Total files|exactly one terminal result/,
  );
});

test('Git-index snapshots exclude untracked and unstaged working-tree contamination', () => {
  const root = fixture();
  const before = withIndexSnapshot(root, ({ paths, root: snapshot }) =>
    buildReport(snapshot, evidence(), paths),
  );
  put(root, 'plugins/mirror/untracked/SKILL.md', '# ignored working-tree row\n');
  put(root, 'sources.yaml', 'sources:\n  - name: contaminated\n');
  assert.doesNotThrow(() =>
    execFileSync('git', ['check-ignore', '-q', 'plugins/mirror/untracked/SKILL.md'], { cwd: root }),
  );
  const after = withIndexSnapshot(root, ({ paths, root: snapshot }) => {
    assert.equal(existsSync(join(snapshot, 'plugins/mirror/untracked/SKILL.md')), false);
    assert.equal(
      readFileSync(join(snapshot, 'sources.yaml'), 'utf8'),
      'sources:\n  - name: alpha\n',
    );
    return buildReport(snapshot, evidence(), paths);
  });
  assert.deepEqual(after, before);
});

test('Git-index snapshots measure staged bytes and ignore a later unstaged edit', () => {
  const root = fixture();
  put(root, 'sources.yaml', 'sources:\n  - name: beta\n');
  execFileSync('git', ['add', 'sources.yaml'], { cwd: root });
  put(root, 'sources.yaml', 'sources:\n  - name: contaminated\n');
  withIndexSnapshot(root, ({ root: snapshot }) => {
    assert.equal(
      readFileSync(join(snapshot, 'sources.yaml'), 'utf8'),
      'sources:\n  - name: beta\n',
    );
  });
});

test('Git-index snapshots expose the staged artifact rather than a matching worktree replacement', () => {
  const root = fixture();
  put(root, '000-docs/742-RA-DATA-epic-1-scorecard.json', '{"state":"stale"}\n');
  execFileSync('git', ['add', '000-docs/742-RA-DATA-epic-1-scorecard.json'], { cwd: root });
  put(root, '000-docs/742-RA-DATA-epic-1-scorecard.json', '{"state":"working-copy"}\n');
  withIndexSnapshot(root, ({ root: snapshot }) => {
    assert.equal(
      readFileSync(join(snapshot, '000-docs/742-RA-DATA-epic-1-scorecard.json'), 'utf8'),
      '{"state":"stale"}\n',
    );
  });
});

test('grade arithmetic derives a 3679 cohort rather than preserving historical 3678', () => {
  const rows = Array.from({ length: 3679 }, (_, index) => ({
    errors: 0,
    grade: index === 0 ? 'A' : 'B',
    path: `plugins/example/skills/skill-${index}/SKILL.md`,
  }));
  const result = parseSkillRows(rows);
  assert.equal(result.rows, 3679);
  assert.notEqual(result.rows, 3678);
  assert.equal(
    Object.values(result.grade_distribution).reduce((sum, count) => sum + count, 0),
    3679,
  );
});

test('signature registry accepts genuine bytes, exposes counterfeits, and refuses unknown types', () => {
  assert.equal(matchesSignature('.png', Buffer.from('89504e470d0a1a0a', 'hex')), true);
  assert.equal(matchesSignature('.zip', Buffer.from('504b0304', 'hex')), true);
  assert.equal(matchesSignature('.ttf', Buffer.from('typ1')), false);
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
  const duplicateReport = buildReport(duplicateSource, evidence());
  assert.equal(duplicateReport.rows[27].status, 'undefined');
  assert.equal(duplicateReport.rows[27].values, null);

  const unknownDetector = fixture();
  put(unknownDetector, 'freshie/scripts/promote-to-curated.py', 'return False\n');
  assert.throws(
    () => buildReport(unknownDetector, evidence()),
    /unknown promotion binary-detector shape/,
  );
});

test('stable output excludes runtime metadata and byte comparison catches one-value drift', () => {
  const rendered = stableJson({ rows: { 1: { values: { count: 2 } } }, schema_version: 1 });
  assert.match(stableJson({ values: ['one', 'two'] }), /"values": \["one", "two"\]/);
  assert.equal(rendered.endsWith('\n'), true);
  assert.equal(rendered.includes(tmpdir()), false);
  assert.equal(rendered.includes('captured_at'), false);
  assert.equal(artifactMatches(rendered, rendered), true);
  assert.equal(artifactMatches(rendered.replace('2', '3'), rendered), false);
  assert.throws(() => stableJson({ generated_at: 'now' }), /nondeterministic metadata/);
  assert.throws(() => stableJson({ value: Number.NaN }), /non-finite number/);
  assert.throws(() => stableJson({ value: undefined }), /unsupported undefined/);
  const shared = { count: 1 };
  assert.doesNotThrow(() => stableJson({ first: shared, second: shared }));
  const cycle = {};
  cycle.self = cycle;
  assert.throws(() => stableJson(cycle), /cycle in output/);
});
