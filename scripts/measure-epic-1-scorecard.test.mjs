import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';

import { buildExtendedScorecardRows } from './measure-epic-1-scorecard.mjs';

const EXPECTED_ROWS = [
  5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32,
  33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
  57, 58, 59, 60, 61, 62,
];

function put(root, path, value = '') {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, value);
}

function fixture() {
  const root = mkdtempSync(join(tmpdir(), 'epic-1-scorecard-'));
  const files = {
    '.github/dependabot.yml': 'version: 2\nupdates: []\n',
    '.github/workflows/publish-changed-packages.yml': `on:\n  workflow_run:\n    workflows: ['Validate Plugins']\njobs:\n  preflight:\n    steps:\n      - run: node scripts/npm-publication-preflight.mjs\n  publish:\n    environment: npm-production\n    steps:\n      - run: node scripts/publish-candidate-report.mjs && npm publish\n`,
    '.github/workflows/validate-plugins.yml': `on:\n  pull_request:\n  push:\n    branches: [main]\njobs:\n  validate:\n    steps:\n      - run: python3 scripts/validate-skills-schema.py --marketplace\n      - run: python3 -m unittest tests.test_prose_anchors\n  ci-required:\n    needs:\n      - validate\n`,
    '.gitleaks.toml': "[allowlist]\npaths = ['''(?i).*/README\\.md$''']\nregexes = []\n",
    '.claude-plugin/marketplace.extended.json': JSON.stringify({
      plugins: [
        { name: 'example', source: './plugins/example' },
        { name: 'local', source: './plugins/local' },
      ],
    }),
    '000-docs/000-INDEX.md': '- [canonical.md](canonical.md)\n',
    '000-docs/canonical.md': '# Canonical\n\n**Status:** AUTHORITATIVE\n',
    'CLAUDE.md': 'Validator (schema 4.0.0 — governed)\n',
    'STANDARDS.md':
      '## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Fixture | [canonical](000-docs/canonical.md) |\n',
    'freshie/grade-histogram.json': JSON.stringify({ total: 2 }),
    'freshie/scripts/dolt-sync.py':
      'def acquire_lock():\n fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\ndef refuse_if_server_running():\n return ".dolt/sql-server.lock"\n',
    'marketplace/scripts/generate-alpha.mjs':
      "writeFileSync('marketplace/src/data/alpha.json', '{}')\n",
    'marketplace/src/data/alpha.json': '{}',
    'marketplace/src/data/jrig-data.json': JSON.stringify({ plugin: { verified: true } }),
    'package.json': JSON.stringify({
      devDependencies: {
        '@intentsolutions/audit-harness': '^1.0.0',
        '@intentsolutions/core': '1.0.0',
        '@intentsolutions/jrig-cli': '1.0.0',
      },
    }),
    'plugins/example/.source.json': JSON.stringify({
      synced_from: { repo: 'owner/repo', path: '/' },
    }),
    'plugins/example/LICENSE': 'fixture license\n',
    'plugins/example/package.json': JSON.stringify({ name: '@scope/example', private: true }),
    'plugins/example/skills/one/SKILL.md': `---\nname: one\nallowed-tools: Read\ncompatibility: Harness A\n---\nhttps://docs.anthropic.com\n`,
    'plugins/local/skills/two/SKILL.md': `---\nname: two\nallowed-tools: >-\n  Read Write\ncompatibility: Harness B\n---\nclaudecodeplugins.io\n`,
    'scripts/npm-publication-preflight.mjs': 'export const required = true;\n',
    'scripts/plugin-provenance.mjs':
      "export const SOURCE_FILE = '.source.json';\nexport function resolvePluginProvenance() {}\n",
    'scripts/publish-candidate-report.mjs':
      "import { resolvePluginProvenance } from './plugin-provenance.mjs';\nexport const report = resolvePluginProvenance;\n",
    'scripts/readme-metrics.mjs':
      "const catalog = '.claude-plugin/marketplace.extended.json'; const skillCount = 1; const agentCount = 1; writeFileSync('README.md', String(catalog) + skillCount + agentCount);\n",
    'scripts/validate-skills-schema.py': 'SCHEMA_VERSION = "4.0.0"\n',
    'sources.lock.json': JSON.stringify({ sources: { example: {} } }),
    'sources.yaml': 'sources:\n  - name: example\n',
    'tests/test_dolt_sync.py': 'def test_single_writer_lock():\n pass\n',
  };
  for (const [path, value] of Object.entries(files)) put(root, path, value);
  return { root, paths: Object.keys(files).sort() };
}

function input(fixtureValue) {
  return {
    ...fixtureValue,
    agentSummary: { agents: 1, compliance_percent: 100, errors: 0 },
    marketplaceSummary: { errors: 1 },
    skillRows: [
      {
        errors: 1,
        grade: 'A',
        path: 'plugins/example/skills/one/SKILL.md',
        score: 90,
      },
      {
        errors: 0,
        grade: 'B',
        path: 'plugins/local/skills/two/SKILL.md',
        score: 80,
      },
    ],
    skillSummary: { rows: 2 },
  };
}

test('emits the exact extended numbered row set in deterministic order and shape', () => {
  const rows = buildExtendedScorecardRows(input(fixture()));
  assert.deepEqual(Object.keys(rows).map(Number), EXPECTED_ROWS);
  for (const number of EXPECTED_ROWS) {
    assert.deepEqual(Object.keys(rows[number]).slice(0, 6), [
      'status',
      'cohort',
      'dimension',
      'reproduce',
      'source',
      'values',
    ]);
    assert.equal(rows[number].reproduce, `pnpm run measure:e1 --row=${number} --stdout`);
  }
  const again = buildExtendedScorecardRows(input(fixture()));
  const firstWithoutRootSpecificData = JSON.stringify(rows);
  assert.equal(JSON.stringify(again), firstWithoutRootSpecificData);
});

test('discovers additional generated artifacts and README count writers dynamically', () => {
  const base = fixture();
  let rows = buildExtendedScorecardRows(input(base));
  assert.deepEqual(
    rows[22].values.artifacts.map((entry) => entry.path),
    ['marketplace/src/data/alpha.json'],
  );
  assert.deepEqual(rows[25].values.writers, ['scripts/readme-metrics.mjs']);

  put(
    base.root,
    'scripts/generate-third.mjs',
    "const catalog = 'marketplace.extended.json'; const skillCount = 3; const agents = 1; writeFileSync('marketplace/src/data/third.json', '{}'); writeFileSync('README.md', String(catalog) + skillCount + agents);\n",
  );
  put(base.root, 'marketplace/src/data/third.json', '{}');
  base.paths.push('marketplace/src/data/third.json', 'scripts/generate-third.mjs');
  rows = buildExtendedScorecardRows(input(base));
  assert.deepEqual(
    rows[22].values.artifacts.map((entry) => entry.path),
    ['marketplace/src/data/alpha.json', 'marketplace/src/data/third.json'],
  );
  assert.deepEqual(rows[25].values.writers, [
    'scripts/generate-third.mjs',
    'scripts/readme-metrics.mjs',
  ]);
});

test('requires call-bound production evidence and excludes measurement instrumentation', () => {
  const base = fixture();
  put(
    base.root,
    'scripts/measure-epic-1-scorecard.mjs',
    "const totalSkills = 99; const agents = 99; const catalog = 'marketplace.extended.json'; writeFileSync('README.md', 'alpha.json');\n",
  );
  put(
    base.root,
    'scripts/unrelated-writer.mjs',
    "const mentioned = 'alpha.json'; writeFileSync('README.md', mentioned);\n",
  );
  put(
    base.root,
    'packages/example/readme-writer.test.mjs',
    "const catalog = 'marketplace.extended.json'; const skills = 1; const agents = 1; writeFileSync('README.md', String(catalog) + skills + agents);\n",
  );
  put(base.root, 'plugins/mirrored/.source.json', '{"source":"upstream"}\n');
  put(
    base.root,
    'plugins/mirrored/readme-writer.mjs',
    "const catalog = 'marketplace.extended.json'; const skills = 1; const agents = 1; writeFileSync('README.md', String(catalog) + skills + agents);\n",
  );
  base.paths.push(
    'packages/example/readme-writer.test.mjs',
    'plugins/mirrored/.source.json',
    'plugins/mirrored/readme-writer.mjs',
    'scripts/measure-epic-1-scorecard.mjs',
    'scripts/unrelated-writer.mjs',
  );

  const rows = buildExtendedScorecardRows(input(base));
  assert.deepEqual(rows[22].values.artifacts[0].producers, [
    'marketplace/scripts/generate-alpha.mjs',
  ]);
  assert.deepEqual(rows[25].values.writers, ['scripts/readme-metrics.mjs']);
});

test('counts only producer-integrated workflow checks as artifact drift gates', () => {
  const base = fixture();
  put(
    base.root,
    'scripts/consumer-check.mjs',
    "const input = 'alpha.json'; const check = process.argv.includes('--check'); console.log(input, check, 'drift');\n",
  );
  put(
    base.root,
    '.github/workflows/consumer-check.yml',
    'jobs:\n  check:\n    steps:\n      - run: node scripts/consumer-check.mjs --check\n',
  );
  base.paths.push('scripts/consumer-check.mjs', '.github/workflows/consumer-check.yml');
  let artifact = buildExtendedScorecardRows(input(base))[22].values.artifacts[0];
  assert.equal(artifact.content_drift_gate, false);
  assert.deepEqual(artifact.wired_checkers, []);

  put(
    base.root,
    'marketplace/scripts/generate-alpha.mjs',
    "const target = 'marketplace/src/data/alpha.json'; const check = process.argv.includes('--check'); const current = readFileSync(target, 'utf8'); const rendered = '{}'; if (check && current !== rendered) process.exit(1); writeFileSync(target, rendered);\n",
  );
  put(
    base.root,
    '.github/workflows/alpha-check.yml',
    'jobs:\n  check:\n    steps:\n      - run: node marketplace/scripts/generate-alpha.mjs --check\n',
  );
  base.paths.push('.github/workflows/alpha-check.yml');
  artifact = buildExtendedScorecardRows(input(base))[22].values.artifacts[0];
  assert.equal(artifact.content_drift_gate, true);
  assert.deepEqual(artifact.wired_checkers, ['marketplace/scripts/generate-alpha.mjs']);
});

test('normalizes absolute validator paths into the tracked Git cohort', () => {
  const base = fixture();
  const values = input(base);
  values.skillRows = values.skillRows.map((entry) => ({
    ...entry,
    path: join(base.root, entry.path),
  }));
  const row = buildExtendedScorecardRows(values)[5];
  assert.equal(row.values.rows, 2);
  assert.deepEqual(row.values.grade_distribution, { A: 1, B: 1, C: 0, D: 0, F: 0 });
});

test('measures the merged provenance boundary, ci-required needs, and STANDARDS authority table', () => {
  const base = fixture();
  put(
    base.root,
    '.github/workflows/cli-publish.yml',
    "jobs:\n  publish:\n    environment: npm-production\n    steps:\n      - run: node scripts/npm-publication-preflight.mjs && npm publish\n        working-directory: packages/cli\n      - run: echo '@claude-code-plugins/ccp https://github.com/example/claude-code-plugins/tree/main/packages/cli'\n",
  );
  base.paths.push('.github/workflows/cli-publish.yml');
  const rows = buildExtendedScorecardRows(input(base));
  assert.equal(rows[31].values.publisher_provenance_boundary, true);
  assert.deepEqual(rows[31].values.mirror_capable_publishers, [
    '.github/workflows/publish-changed-packages.yml',
  ]);
  assert.deepEqual(rows[41].values.actual_needs, ['validate']);
  assert.equal(rows[43].values.declared, 1);
  assert.deepEqual(rows[43].values.authority_links, ['000-docs/canonical.md']);
});

test('fails closed on malformed ci-required needs', () => {
  const base = fixture();
  put(
    base.root,
    '.github/workflows/validate-plugins.yml',
    'jobs:\n  ci-required:\n    needs: [validate, validate]\n',
  );
  const row = buildExtendedScorecardRows(input(base))[41];
  assert.equal(row.status, 'undefined');
  assert.equal(row.values, null);
  assert.equal(row.reason_code, 'MALFORMED_CI_REQUIRED_NEEDS');
});

test('does not let scorecard instrumentation increase link-debt rows', () => {
  const base = fixture();
  put(
    base.root,
    '000-docs/742-RA-DATA-epic-1-scorecard.json',
    JSON.stringify({ dimensions: ['docs.anthropic.com', 'claudecodeplugins.io'] }),
  );
  put(
    base.root,
    'scripts/measure-epic-1-scorecard.test.mjs',
    "const fixtures = ['docs.anthropic.com', 'claudecodeplugins.io'];\n",
  );
  base.paths.push(
    '000-docs/742-RA-DATA-epic-1-scorecard.json',
    'scripts/measure-epic-1-scorecard.test.mjs',
  );
  const rows = buildExtendedScorecardRows(input(base));
  assert.equal(rows[20].measured_proxy.occurrences, 1);
  assert.equal(rows[21].values.actionable.occurrences, 1);
  assert.equal(rows[20].source.includes('scripts/measure-epic-1-scorecard.test.mjs'), false);
  assert.equal(rows[21].source.includes('scripts/measure-epic-1-scorecard.test.mjs'), false);
});

test('unresolved rows fail closed with null values rather than fabricated zeroes', () => {
  const rows = buildExtendedScorecardRows(input(fixture()));
  for (const number of [
    7, 8, 9, 15, 16, 17, 18, 19, 23, 29, 36, 49, 50, 51, 52, 53, 54, 55, 58, 60, 61, 62,
  ]) {
    assert.equal(rows[number].values, null, `row ${number}`);
    assert.match(rows[number].reason_code, /^[A-Z][A-Z0-9_]+$/);
    assert.ok(rows[number].required_inputs.length > 0);
  }
});

test('measurements follow fixture inputs and do not preserve historical blueprint numbers', () => {
  const base = fixture();
  const first = buildExtendedScorecardRows(input(base));
  assert.equal(first[5].values.rows, 2);
  assert.equal(first[28].values.provenance_marked_mirrors, 1);

  put(
    base.root,
    'plugins/local/skills/three/SKILL.md',
    '---\nname: three\nallowed-tools: Read\ncompatibility: Harness C\n---\n',
  );
  base.paths.push('plugins/local/skills/three/SKILL.md');
  const changed = input(base);
  changed.skillRows.push({
    errors: 0,
    grade: 'C',
    path: 'plugins/local/skills/three/SKILL.md',
    score: 70,
  });
  const second = buildExtendedScorecardRows(changed);
  assert.equal(second[5].values.rows, 3);
  assert.notDeepEqual(second[5].values, first[5].values);

  const source = JSON.stringify(second);
  for (const stale of ['22962', '3680', '3679', '3678', '7687', '7433', '1454', '14041']) {
    assert.equal(source.includes(stale), false, `stale blueprint snapshot ${stale}`);
  }
});

test('rejects path traversal and ignores untracked validator rows', () => {
  const base = fixture();
  const values = input(base);
  values.skillRows.push({ errors: 0, grade: 'A', path: 'plugins/untracked/SKILL.md', score: 100 });
  assert.equal(buildExtendedScorecardRows(values)[5].values.rows, 2);
  assert.throws(
    () => buildExtendedScorecardRows({ ...values, paths: [...base.paths, '../escape'] }),
    /escapes repository/,
  );
});

test('scorecard corpus counts reject a supplied SKILL.md symlink', () => {
  const base = fixture();
  const linked = 'plugins/local/skills/linked/SKILL.md';
  mkdirSync(dirname(join(base.root, linked)), { recursive: true });
  symlinkSync(join(base.root, 'plugins/local/skills/two/SKILL.md'), join(base.root, linked));
  assert.throws(
    () => buildExtendedScorecardRows(input({ ...base, paths: [...base.paths, linked] })),
    /symbolic link is not a corpus authority/,
  );
});
