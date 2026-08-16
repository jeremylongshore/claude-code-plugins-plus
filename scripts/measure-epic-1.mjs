#!/usr/bin/env node

/**
 * Deterministic measurement harness for blueprint 727, Epic 1.
 *
 * The package-level `measure:e1:check` command runs the resolver and harness
 * fixture suites before invoking this module's artifact drift check.
 */

import { spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, extname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import { buildExtendedScorecardRows } from './measure-epic-1-scorecard.mjs';

export const ARTIFACT_PATH = '000-docs/742-RA-DATA-epic-1-scorecard.json';
export const REQUIRED_README_METRIC_WRITER = 'scripts/generate-readme-toc.mjs';
const SCRIPT_PATH = 'scripts/measure-epic-1.mjs';
export const MEASUREMENT_INPUT_PATHS = [
  SCRIPT_PATH,
  'scripts/measure-epic-1-scorecard.mjs',
  'scripts/corpus-resolver.mjs',
  'scripts/plugin-provenance.mjs',
  'scripts/check-doc-authority.mjs',
];
const SCRIPT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const GRADES = new Set(['A', 'B', 'C', 'D', 'F']);
const CATALOGS = new Set([
  '.claude-plugin/marketplace.extended.json',
  '.claude-plugin/marketplace.json',
]);
const SIGNATURES = {
  '.pdf': [Buffer.from('%PDF-')],
  '.png': [Buffer.from('89504e470d0a1a0a', 'hex')],
  '.ttf': [Buffer.from('00010000', 'hex'), Buffer.from('true')],
  '.zip': [
    Buffer.from('504b0304', 'hex'),
    Buffer.from('504b0506', 'hex'),
    Buffer.from('504b0708', 'hex'),
  ],
};

function fail(message) {
  throw new Error(`epic-1-measurement: ${message}`);
}

function posix(path) {
  return path.split(sep).join('/');
}

function file(root, path) {
  const target = resolve(root, path);
  const rel = relative(root, target);
  if (rel.startsWith('..') || isAbsolute(rel)) fail(`path escapes repository: ${path}`);
  return target;
}

function text(root, path) {
  try {
    return readFileSync(file(root, path), 'utf8');
  } catch (error) {
    fail(`cannot read ${path}: ${error.message}`);
  }
}

function json(root, path) {
  try {
    return JSON.parse(text(root, path));
  } catch (error) {
    if (error.message.startsWith('epic-1-measurement:')) throw error;
    fail(`malformed JSON in ${path}: ${error.message}`);
  }
}

function run(root, command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) fail(`${command} failed to start: ${result.error.message}`);
  return result;
}

export function trackedPaths(root) {
  const treeResult = run(root, 'git', ['write-tree']);
  if (treeResult.status !== 0) fail(`git write-tree failed: ${treeResult.stderr.trim()}`);
  const tree = treeResult.stdout.trim();
  if (!/^[0-9a-f]{40,64}$/.test(tree)) fail('git write-tree returned an invalid object id');
  const result = run(root, 'git', ['ls-tree', '-r', '-z', '--name-only', tree]);
  if (result.status !== 0) fail(`git tree inventory failed: ${result.stderr.trim()}`);
  const paths = result.stdout.split('\0').filter(Boolean).map(posix).sort();
  if (paths.length === 0) fail('git inventory is empty');
  return paths;
}

export function matchesSignature(extension, bytes) {
  const signatures = SIGNATURES[extension.toLowerCase()];
  if (!signatures) fail(`unknown governed binary extension: ${extension}`);
  return signatures.some((signature) => bytes.subarray(0, signature.length).equals(signature));
}

export function parseSkillRows(value, options = {}) {
  if (!Array.isArray(value)) fail('validator JSON must be an array');
  const rows = value.filter((entry) => entry && typeof entry.path === 'string');
  const advisories = value.filter((entry) => !entry || typeof entry.path !== 'string');
  if (options.requireKernelShadow) {
    if (
      advisories.length !== 1 ||
      !advisories[0]?.kernel_shadow ||
      typeof advisories[0].kernel_shadow !== 'object'
    ) {
      fail('validator JSON must end with exactly one kernel_shadow advisory');
    }
  } else if (advisories.some((entry) => !entry?.kernel_shadow)) {
    fail('validator JSON contains an unknown non-row record');
  }
  if (rows.length === 0) fail('validator JSON contains no SKILL.md rows');
  const seen = new Set();
  const grades = Object.fromEntries([...GRADES].map((grade) => [grade, 0]));
  let errors = 0;
  let errorFiles = 0;
  let abFailing = 0;
  let aFailing = 0;
  let bFailing = 0;
  let aErrors = 0;
  let abErrors = 0;
  for (const row of rows) {
    if (
      !row.path.endsWith('/SKILL.md') ||
      seen.has(row.path) ||
      !GRADES.has(row.grade) ||
      !Number.isSafeInteger(row.errors) ||
      row.errors < 0
    ) {
      fail(`invalid validator row: ${row.path}`);
    }
    seen.add(row.path);
    grades[row.grade] += 1;
    errors += row.errors;
    if (row.errors > 0) errorFiles += 1;
    if ((row.grade === 'A' || row.grade === 'B') && row.errors > 0) {
      abFailing += 1;
      abErrors += row.errors;
      if (row.grade === 'A') {
        aFailing += 1;
        aErrors += row.errors;
      } else {
        bFailing += 1;
      }
    }
  }
  if (Object.values(grades).reduce((sum, count) => sum + count, 0) !== rows.length) {
    fail('grade totals do not equal graded rows');
  }
  return {
    ab_error_total: abErrors,
    ab_failing: abFailing,
    a_error_total: aErrors,
    a_failing: aFailing,
    b_failing: bFailing,
    error_files: errorFiles,
    error_total: errors,
    grade_distribution: grades,
    rows: rows.length,
  };
}

function summaryValue(output, label, valuePattern = '(\\d+)') {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const matches = [
    ...output.matchAll(new RegExp(`^[^\\n]*${escaped}:\\s*${valuePattern}\\s*$`, 'gm')),
  ];
  if (matches.length !== 1) fail(`validator summary requires exactly one ${label}`);
  return Number(matches[0][1]);
}

export function parseTerminalSummary(evidence, lane) {
  const output = typeof evidence === 'string' ? evidence : evidence?.output;
  const status = typeof evidence === 'string' ? undefined : evidence?.status;
  if (typeof output !== 'string') fail(`missing ${lane} terminal summary`);
  const totalFiles = summaryValue(output, 'Total files');
  const verdicts = [
    ...output.matchAll(/^.*Validation FAILED with\s+(\d+) errors .*$/gm),
    ...output.matchAll(/^.*Validation PASSED with\s+(\d+) warnings .*$/gm),
    ...output.matchAll(/^.*All skills fully compliant! .*$/gm),
  ];
  if (verdicts.length !== 1) fail('validator summary requires exactly one terminal result');
  const failure = output.match(/^.*Validation FAILED with\s+(\d+) errors .*$/m);
  const errors = failure ? Number(failure[1]) : 0;
  if (failure && errors === 0) fail('validator cannot fail with zero errors');
  const expectedStatus = failure ? 1 : 0;
  if (status !== undefined && status !== expectedStatus) {
    fail(`validator ${lane} exit ${status} contradicts its terminal result`);
  }
  if (lane === 'marketplace') {
    const skills = summaryValue(output, 'Skills validated');
    const commands = summaryValue(output, 'Commands validated');
    const agents = summaryValue(output, 'Agents validated');
    if (skills + commands + agents !== totalFiles) {
      fail('marketplace terminal denominator arithmetic is inconsistent');
    }
    return {
      error_total_all_validated_surfaces: errors,
      fully_compliant_surfaces: summaryValue(output, 'Fully compliant'),
      terminal_denominator: {
        agents,
        commands,
        files: totalFiles,
        label: 'skills_plus_commands_plus_agents_excluding_plugin_manifests',
        skills,
      },
      validator_reported_mixed_denominator_percent: summaryValue(
        output,
        'Compliance rate',
        '([\\d.]+)%',
      ),
    };
  }
  if (lane !== 'agents') fail(`unknown terminal lane: ${lane}`);
  const agents = summaryValue(output, 'Agents validated');
  if (agents !== totalFiles) fail('agent terminal denominator arithmetic is inconsistent');
  return {
    error_total_all_validated_surfaces: errors,
    fully_compliant_surfaces: summaryValue(output, 'Fully compliant'),
    terminal_denominator: {
      agents,
      files: totalFiles,
      label: 'agents_excluding_plugin_manifests',
    },
    validator_reported_mixed_denominator_percent: summaryValue(
      output,
      'Compliance rate',
      '([\\d.]+)%',
    ),
  };
}

function validatorEvidence(root) {
  const invocations = [
    ['skills', ['scripts/validate-skills-schema.py', '--marketplace', '--skills-only', '--json']],
    ['marketplace', ['scripts/validate-skills-schema.py', '--marketplace']],
    ['agents', ['scripts/validate-skills-schema.py', '--standard', '--agents-only']],
  ];
  const evidence = {};
  for (const [name, args] of invocations) {
    const result = run(root, 'python3', args);
    if (![0, 1].includes(result.status)) fail(`validator ${name} exited ${result.status}`);
    if (/VALIDATION SUMMARY|Validation (?:FAILED|PASSED)/.test(result.stderr)) {
      fail(`validator ${name} emitted protocol text on stderr`);
    }
    if (name === 'skills') {
      try {
        evidence.skills = JSON.parse(result.stdout);
        evidence.skillsStatus = result.status;
        evidence.requireKernelShadow = true;
      } catch (error) {
        fail(`malformed validator JSON: ${error.message}`);
      }
    } else {
      evidence[name] = { output: result.stdout, status: result.status };
    }
  }
  return evidence;
}

export function withIndexSnapshot(root, callback) {
  const repository = resolve(root);
  const snapshot = mkdtempSync(join(tmpdir(), 'epic-1-measurement-index-'));
  const archive = `${snapshot}.tar`;
  try {
    const treeResult = run(repository, 'git', ['write-tree']);
    if (treeResult.status !== 0) fail(`git write-tree failed: ${treeResult.stderr.trim()}`);
    const tree = treeResult.stdout.trim();
    if (!/^[0-9a-f]{40,64}$/.test(tree)) fail('git write-tree returned an invalid object id');

    const inventoryResult = run(repository, 'git', ['ls-tree', '-r', '-z', '--name-only', tree]);
    if (inventoryResult.status !== 0) {
      fail(`git tree inventory failed: ${inventoryResult.stderr.trim()}`);
    }
    const paths = inventoryResult.stdout.split('\0').filter(Boolean).map(posix).sort();
    if (paths.length === 0) fail('git tree inventory is empty');

    const archiveResult = run(repository, 'git', [
      'archive',
      '--format=tar',
      `--output=${archive}`,
      tree,
    ]);
    if (archiveResult.status !== 0) fail(`cannot archive Git tree: ${archiveResult.stderr.trim()}`);
    const extractResult = run(repository, 'tar', ['-xf', archive, '-C', snapshot]);
    if (extractResult.status !== 0) fail(`cannot extract Git tree: ${extractResult.stderr.trim()}`);
    return callback({ paths, root: snapshot, tree });
  } finally {
    rmSync(archive, { force: true });
    rmSync(snapshot, { force: true, recursive: true });
  }
}

function binaryAssets(root, paths) {
  const candidates = paths.filter((path) => Object.hasOwn(SIGNATURES, extname(path).toLowerCase()));
  const mismatches = [];
  for (const path of candidates) {
    let bytes;
    try {
      bytes = readFileSync(file(root, path));
    } catch (error) {
      fail(`cannot read binary candidate ${path}: ${error.message}`);
    }
    if (!matchesSignature(extname(path), bytes)) mismatches.push(path);
  }
  return { candidates, mismatches };
}

function promotionDetector(root, mismatches) {
  const sourcePath = 'freshie/scripts/promote-to-curated.py';
  const source = text(root, sourcePath);
  // Pin the exact detector semantics. Any refactor must deliberately update this
  // measurement instead of silently changing what row 12 counts.
  if (!/b["']\\0["']\s+in\s+fh\.read\(8192\)/.test(source)) {
    fail('unknown promotion binary-detector shape');
  }
  const excluded = [];
  const missed = [];
  for (const path of mismatches) {
    const prefix = readFileSync(file(root, path)).subarray(0, 8192);
    (prefix.includes(0) ? excluded : missed).push(path);
  }
  return { excluded, missed, prefix_bytes: 8192, strategy: 'nul_prefix' };
}

function catalogMeasurement(root, paths) {
  const catalog = json(root, '.claude-plugin/marketplace.extended.json');
  if (!Array.isArray(catalog.plugins)) fail('catalog plugins must be an array');
  const names = catalog.plugins.map((plugin, index) => {
    if (!plugin || typeof plugin.name !== 'string' || !plugin.name)
      fail(`catalog plugin ${index} lacks name`);
    return plugin.name;
  });
  const counts = new Map();
  for (const name of names) counts.set(name, (counts.get(name) ?? 0) + 1);
  const duplicateNames = [...counts]
    .filter(([, count]) => count > 1)
    .map(([name, count]) => ({ count, name }))
    .sort((a, b) => a.name.localeCompare(b.name));
  const shadows = paths.filter(
    (path) =>
      path.startsWith('.claude-plugin/marketplace') &&
      path.includes('.json') &&
      !CATALOGS.has(path),
  );
  return { duplicateNames, entries: names.length, names: counts.size, shadows };
}

const ROW_SOURCES = {
  1: 'git write-tree + git ls-tree over the exact index tree',
  2: '.claude-plugin/marketplace.extended.json',
  3: 'git tree inventory under .claude-plugin/',
  4: 'scripts/validate-skills-schema.py JSON and terminal protocols',
  11: 'Git tree bytes matched against the per-extension signature registry',
  12: 'freshie/scripts/promote-to-curated.py detector semantics applied to row 11 mismatches',
};

function row(dimension, cohort, values, id, targetStatus = 'informational') {
  const source = ROW_SOURCES[id];
  if (!source) fail(`row ${id} lacks a source identifier`);
  return {
    cohort,
    dimension,
    reproduce: `pnpm run measure:e1 --row=${id} --stdout`,
    source,
    status: 'measured',
    target_status: targetStatus,
    values,
  };
}

export function assertReadmeMetricWriterContract(readmeWriterRow) {
  const writers = readmeWriterRow?.values?.writers;
  if (
    !Array.isArray(writers) ||
    writers.length !== 1 ||
    writers[0] !== REQUIRED_README_METRIC_WRITER
  ) {
    const observed = Array.isArray(writers) ? writers.join(', ') || '(none)' : '(malformed)';
    fail(
      `README metric writer contract requires only ${REQUIRED_README_METRIC_WRITER}; observed ${observed}`,
    );
  }
}

export function buildReport(root, suppliedEvidence, suppliedPaths) {
  const repository = resolve(root);
  const paths = suppliedPaths ?? trackedPaths(repository);
  const evidence = suppliedEvidence ?? validatorEvidence(repository);
  const skills = parseSkillRows(evidence.skills, {
    requireKernelShadow: evidence.requireKernelShadow === true,
  });
  if (evidence.skillsStatus !== undefined && evidence.skillsStatus !== 0) {
    fail(`validator skills JSON exited ${evidence.skillsStatus}`);
  }
  const marketplace = parseTerminalSummary(evidence.marketplace, 'marketplace');
  const agents = parseTerminalSummary(evidence.agents, 'agents');
  if (marketplace.terminal_denominator.skills !== skills.rows) {
    fail('marketplace and SKILL-row counts disagree');
  }
  marketplace.validated_plugin_manifests = paths.filter((path) =>
    /\/\.claude-plugin\/plugin\.json$/.test(path),
  ).length;

  const pluginSkills = paths.filter((path) => /^plugins\/.+\/SKILL\.md$/.test(path)).length;
  const pluginAgents = paths.filter((path) => /^plugins\/.+\/agents\/[^/]+\.md$/.test(path)).length;
  const catalog = catalogMeasurement(repository, paths);
  const assets = binaryAssets(repository, paths);
  const detector = promotionDetector(repository, assets.mismatches);
  const extendedRows = buildExtendedScorecardRows({
    agentSummary: {
      agents: agents.terminal_denominator.agents,
      compliance_percent: agents.validator_reported_mixed_denominator_percent,
      errors: agents.error_total_all_validated_surfaces,
    },
    marketplaceSummary: {
      errors: marketplace.error_total_all_validated_surfaces,
    },
    paths,
    root: repository,
    skillRows: evidence.skills.filter((entry) => entry && typeof entry.path === 'string'),
    skillSummary: skills,
  });
  assertReadmeMetricWriterContract(extendedRows[25]);

  return {
    blueprint: '727',
    cohorts: {
      agent_files_plugin_surface: 'tracked Markdown files directly beneath plugins/**/agents/',
      agent_lane_validator: 'files reported by validate-skills-schema.py --standard --agents-only',
      graded_artifacts:
        'unique SKILL.md rows from --marketplace --skills-only --json in the exact Git index tree',
      marketplace_terminal:
        'errors and fully-compliant counts may include plugin manifests; Total files excludes them and equals skills + commands + agents',
      plugin_skills: 'tracked plugins/**/SKILL.md files',
      tracked_tree: 'git ls-tree over one immutable git write-tree object',
    },
    graded_artifact_cohort: {
      cohort: 'graded_artifacts',
      reproduce: 'pnpm run measure:e1 --row=graded_artifact_cohort --stdout',
      source: 'scripts/validate-skills-schema.py --marketplace --skills-only --json',
      status: 'measured',
      values: skills,
    },
    rows: {
      1: row(
        'Tracked files, plugin SKILL.md, and plugin agent files',
        'tracked_tree',
        {
          plugin_agent_files: pluginAgents,
          raw_tracked_plugin_skill_files: pluginSkills,
          tracked_files: paths.length,
        },
        1,
      ),
      2: row(
        'Catalog entries versus distinct names',
        'canonical extended catalog',
        {
          duplicate_names: catalog.duplicateNames,
          entries: catalog.entries,
          distinct_names: catalog.names,
        },
        2,
        catalog.entries === catalog.names ? 'pass' : 'fail',
      ),
      3: row(
        'Tracked stale catalog shadows',
        'tracked .claude-plugin catalog-shaped files',
        {
          count: catalog.shadows.length,
          paths: catalog.shadows,
        },
        3,
        catalog.shadows.length === 0 ? 'pass' : 'fail',
      ),
      4: row(
        'Marketplace-tier errors and compliance',
        'three named validator cohorts; never interchangeable',
        {
          agent_lane: agents,
          marketplace_terminal: marketplace,
          skill_rows: skills,
        },
        4,
      ),
      11: row(
        'Binary-extension assets versus magic bytes',
        'tracked .png/.pdf/.zip/.ttf files',
        {
          candidate_count: assets.candidates.length,
          mismatch_count: assets.mismatches.length,
          mismatch_paths: assets.mismatches,
        },
        11,
        assets.mismatches.length === 0 ? 'pass' : 'fail',
      ),
      12: row(
        'Binary detector in the promotion path',
        'row 11 mismatches evaluated by promote-to-curated semantics',
        {
          detector: detector.strategy,
          excluded_count: detector.excluded.length,
          missed_count: detector.missed.length,
          missed_paths: detector.missed,
          prefix_bytes: detector.prefix_bytes,
        },
        12,
        detector.strategy === 'magic_bytes' ? 'pass' : 'fail',
      ),
      ...extendedRows,
    },
    schema_version: 2,
  };
}

export function stableJson(value) {
  const seen = new WeakSet();
  function sort(item) {
    if (typeof item === 'number' && !Number.isFinite(item)) fail('non-finite number in output');
    if (['undefined', 'function', 'symbol', 'bigint'].includes(typeof item)) {
      fail(`unsupported ${typeof item} in output`);
    }
    if (Array.isArray(item)) {
      if (Object.keys(item).length !== item.length) fail('sparse array in output');
      if (seen.has(item)) fail('cycle in output');
      seen.add(item);
      const result = item.map(sort);
      seen.delete(item);
      return result;
    }
    if (item && typeof item === 'object') {
      if (
        Object.getPrototypeOf(item) !== Object.prototype &&
        Object.getPrototypeOf(item) !== null
      ) {
        fail('non-plain object in output');
      }
      if (seen.has(item)) fail('cycle in output');
      seen.add(item);
      const result = Object.fromEntries(
        Object.keys(item)
          .sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))
          .map((key) => [key, sort(item[key])]),
      );
      seen.delete(item);
      return result;
    }
    return item;
  }
  const raw = `${JSON.stringify(sort(value), null, 2)}\n`;
  const formatted = spawnSync(
    join(SCRIPT_ROOT, 'node_modules/.bin/prettier'),
    ['--parser', 'json'],
    {
      cwd: SCRIPT_ROOT,
      encoding: 'utf8',
      input: raw,
      maxBuffer: 64 * 1024 * 1024,
    },
  );
  if (formatted.error || formatted.status !== 0) {
    fail(`Prettier JSON formatting failed: ${formatted.error?.message ?? formatted.stderr.trim()}`);
  }
  const rendered = formatted.stdout;
  if (/"(?:captured_at|generated_at|hostname|cwd|head)"\s*:/.test(rendered)) {
    fail('nondeterministic metadata entered output');
  }
  return rendered;
}

export function artifactMatches(actual, expected) {
  return actual === expected;
}

export function assertMeasurementInputsIndexed(
  worktreeRoot,
  snapshotRoot,
  paths = MEASUREMENT_INPUT_PATHS,
) {
  for (const path of paths) {
    if (text(snapshotRoot, path) !== text(worktreeRoot, path)) {
      fail(`${path} differs from the Git index; stage or restore it before measuring`);
    }
  }
}

function parseArgs(argv) {
  const options = { check: false, root: SCRIPT_ROOT, row: null, stdout: false };
  for (const arg of argv) {
    if (arg === '--check') options.check = true;
    else if (arg === '--stdout') options.stdout = true;
    else if (arg.startsWith('--row=')) {
      const value = arg.slice(6);
      if (value !== 'graded_artifact_cohort' && !/^(?:[1-9]|[1-5]\d|6[0-2])$/.test(value)) {
        fail(`unknown row: ${value || '(empty)'}`);
      }
      options.row = value;
    } else if (arg.startsWith('--root=')) {
      const value = arg.slice(7);
      if (!value) fail('--root requires a path');
      options.root = resolve(value);
    } else fail(`unknown argument: ${arg}`);
  }
  if (options.row && !options.stdout) fail('--row requires --stdout');
  if (options.check && options.stdout) fail('--check and --stdout are mutually exclusive');
  return options;
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  const indexed = withIndexSnapshot(options.root, (snapshot) => {
    assertMeasurementInputsIndexed(options.root, snapshot.root);
    return {
      artifact: existsSync(file(snapshot.root, ARTIFACT_PATH))
        ? readFileSync(file(snapshot.root, ARTIFACT_PATH), 'utf8')
        : null,
      report: buildReport(snapshot.root, undefined, snapshot.paths),
    };
  });
  const report = indexed.report;
  let selected = report;
  if (options.row) {
    selected =
      options.row === 'graded_artifact_cohort'
        ? report.graded_artifact_cohort
        : report.rows[options.row];
    if (!selected) fail(`unknown row: ${options.row}`);
  }
  const rendered = stableJson(selected);
  if (options.stdout) {
    process.stdout.write(rendered);
    return;
  }
  const artifact = file(options.root, ARTIFACT_PATH);
  if (options.check) {
    if (indexed.artifact === null || !artifactMatches(indexed.artifact, rendered)) {
      console.error(`epic-1-measurement: DRIFT (${ARTIFACT_PATH})`);
      process.exitCode = 1;
      return;
    }
    console.log(`epic-1-measurement: OK (${ARTIFACT_PATH})`);
    return;
  }
  writeFileSync(artifact, rendered);
  console.log(`epic-1-measurement: generated (${ARTIFACT_PATH})`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    main();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
