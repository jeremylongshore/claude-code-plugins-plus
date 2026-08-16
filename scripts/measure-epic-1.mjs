#!/usr/bin/env node

/** Deterministic measurement harness for blueprint 727, Epic 1. */

import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, extname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

export const ARTIFACT_PATH = '000-docs/742-RA-DATA-epic-1-scorecard.json';
const SCRIPT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const GRADES = new Set(['A', 'B', 'C', 'D', 'F']);
const CATALOGS = new Set([
  '.claude-plugin/marketplace.extended.json',
  '.claude-plugin/marketplace.json',
]);
const GOVERNED_GENERATED = [
  'marketplace/src/data/catalog.json',
  'marketplace/src/data/jrig-data.json',
  'marketplace/src/data/readme-sections.json',
  'marketplace/src/data/skills-catalog.json',
  'marketplace/src/data/skills-index.json',
  'marketplace/src/data/unified-search-index.json',
];
const README_COUNT_WRITERS = ['scripts/generate-readme-toc.mjs', 'scripts/update-metrics.mjs'];
const PUBLIC_STATS = [
  'marketplace/src/data/github-stats.json',
  'marketplace/src/data/npm-stats.json',
  'marketplace/src/data/skills-stats.json',
];
const SIGNATURES = {
  '.pdf': [Buffer.from('%PDF-')],
  '.png': [Buffer.from('89504e470d0a1a0a', 'hex')],
  '.ttf': [Buffer.from('00010000', 'hex'), Buffer.from('true'), Buffer.from('typ1')],
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
  const result = run(root, 'git', ['ls-files', '-z']);
  if (result.status !== 0) fail(`git inventory failed: ${result.stderr.trim()}`);
  const paths = result.stdout.split('\0').filter(Boolean).map(posix).sort();
  if (paths.length === 0) fail('git inventory is empty');
  return paths;
}

export function matchesSignature(extension, bytes) {
  const signatures = SIGNATURES[extension.toLowerCase()];
  if (!signatures) fail(`unknown governed binary extension: ${extension}`);
  return signatures.some((signature) => bytes.subarray(0, signature.length).equals(signature));
}

export function parseSkillRows(value) {
  if (!Array.isArray(value)) fail('validator JSON must be an array');
  const rows = value.filter((entry) => entry && typeof entry.path === 'string');
  if (rows.length === 0) fail('validator JSON contains no SKILL.md rows');
  const grades = Object.fromEntries([...GRADES].map((grade) => [grade, 0]));
  let errors = 0;
  let errorFiles = 0;
  let abFailing = 0;
  let aFailing = 0;
  let bFailing = 0;
  let aErrors = 0;
  let abErrors = 0;
  for (const row of rows) {
    if (!GRADES.has(row.grade) || !Number.isInteger(row.errors) || row.errors < 0) {
      fail(`invalid validator row: ${row.path}`);
    }
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

function requiredNumber(output, pattern, label) {
  const match = output.match(pattern);
  if (!match) fail(`validator summary missing ${label}`);
  return Number(match[1]);
}

export function parseTerminalSummary(output, lane) {
  if (typeof output !== 'string') fail(`missing ${lane} terminal summary`);
  const totalFiles = requiredNumber(output, /Total files:\s*(\d+)/, 'total files');
  const errors = requiredNumber(output, /Validation FAILED with\s+(\d+) errors/, 'error total');
  if (lane === 'marketplace') {
    return {
      agents: requiredNumber(output, /Agents validated:\s*(\d+)/, 'agents'),
      commands: requiredNumber(output, /Commands validated:\s*(\d+)/, 'commands'),
      compliance_percent: Number(
        output.match(/Compliance rate:\s*([\d.]+)%/)?.[1] ??
          fail('validator summary missing compliance'),
      ),
      errors,
      fully_compliant: requiredNumber(output, /Fully compliant:\s*(\d+)/, 'fully compliant'),
      skills: requiredNumber(output, /Skills validated:\s*(\d+)/, 'skills'),
      total_files: totalFiles,
    };
  }
  return {
    agents: requiredNumber(output, /Agents validated:\s*(\d+)/, 'agents'),
    compliance_percent: Number(
      output.match(/Compliance rate:\s*([\d.]+)%/)?.[1] ??
        fail('validator summary missing compliance'),
    ),
    errors,
    total_files: totalFiles,
  };
}

function validatorEvidence(root) {
  const invocations = [
    ['skills', ['scripts/validate-skills-schema.py', '--marketplace', '--skills-only', '--json']],
    ['marketplace', ['scripts/validate-skills-schema.py', '--marketplace']],
    ['agents', ['scripts/validate-skills-schema.py', '--agents-only']],
  ];
  const evidence = {};
  for (const [name, args] of invocations) {
    const result = run(root, 'python3', args);
    if (![0, 1].includes(result.status)) fail(`validator ${name} exited ${result.status}`);
    const output = `${result.stdout}${result.stderr}`;
    if (name === 'skills') {
      try {
        evidence.skills = JSON.parse(result.stdout);
      } catch (error) {
        fail(`malformed validator JSON: ${error.message}`);
      }
    } else {
      evidence[name] = output;
    }
  }
  return evidence;
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

function sourceMeasurement(root) {
  let document;
  try {
    document = yaml.load(text(root, 'sources.yaml'));
  } catch (error) {
    fail(`malformed YAML in sources.yaml: ${error.message}`);
  }
  if (!document || !Array.isArray(document.sources)) fail('sources.yaml sources must be an array');
  const names = document.sources.map((source, index) => {
    if (!source || typeof source.name !== 'string' || !source.name)
      fail(`source ${index} lacks name`);
    return source.name;
  });
  if (new Set(names).size !== names.length) fail('sources.yaml contains duplicate source names');
  const lock = json(root, 'sources.lock.json');
  if (!lock.sources || Array.isArray(lock.sources) || typeof lock.sources !== 'object') {
    fail('sources.lock.json sources must be an object');
  }
  const yamlKeys = [...names].sort();
  const lockKeys = Object.keys(lock.sources).sort();
  return {
    lock_keys: lockKeys.length,
    lock_only: lockKeys.filter((name) => !names.includes(name)),
    yaml_keys: yamlKeys.length,
    yaml_only: yamlKeys.filter((name) => !lockKeys.includes(name)),
  };
}

function countValue(value, label) {
  if (!Number.isInteger(value) || value < 0) fail(`invalid count in ${label}`);
  return value;
}

function row(dimension, cohort, values, id) {
  return {
    cohort,
    dimension,
    reproduce: `pnpm run measure:e1 -- --row=${id} --stdout`,
    values,
  };
}

export function buildReport(root, suppliedEvidence) {
  const repository = resolve(root);
  const paths = trackedPaths(repository);
  const evidence = suppliedEvidence ?? validatorEvidence(repository);
  const skills = parseSkillRows(evidence.skills);
  const marketplace = parseTerminalSummary(evidence.marketplace, 'marketplace');
  const agents = parseTerminalSummary(evidence.agents, 'agents');
  if (marketplace.skills !== skills.rows) fail('marketplace and SKILL-row counts disagree');

  const pluginSkills = paths.filter((path) => /^plugins\/.+\/SKILL\.md$/.test(path)).length;
  const pluginAgents = paths.filter((path) => /^plugins\/.+\/agents\/[^/]+\.md$/.test(path)).length;
  const catalog = catalogMeasurement(repository, paths);
  const assets = binaryAssets(repository, paths);
  const detector = promotionDetector(repository, assets.mismatches);
  const generated = GOVERNED_GENERATED.map((path) => ({
    content_drift_gate: false,
    path,
    tracked: paths.includes(path),
  }));
  const freshie = json(repository, 'freshie/grade-histogram.json');
  const skillsIndex = json(repository, 'marketplace/src/data/skills-index.json');
  const unified = json(repository, 'marketplace/src/data/unified-search-index.json');
  const curated = json(repository, 'skills/.curated/MANIFEST.json');
  const writerDetails = README_COUNT_WRITERS.map((path) => {
    const source = text(repository, path);
    return {
      path,
      tracked: paths.includes(path),
      writes_readme_counts: /README/i.test(source) && /skill/i.test(source),
    };
  });
  if (writerDetails.some((entry) => !entry.tracked || !entry.writes_readme_counts)) {
    fail('README count-writer registry is stale');
  }
  const stats = PUBLIC_STATS.map((path) => {
    const value = json(repository, path);
    return { has_max_age_hours: Number.isFinite(value.max_age_hours), path };
  });
  const sources = sourceMeasurement(repository);

  return {
    blueprint: '727',
    cohorts: {
      agent_files_plugin_surface: 'tracked Markdown files directly beneath plugins/**/agents/',
      agent_lane_validator: 'files reported by validate-skills-schema.py --agents-only',
      graded_artifacts: 'path-bearing SKILL.md rows from --marketplace --skills-only --json',
      marketplace_terminal:
        'SKILL.md, command, agent, and plugin.json surfaces in --marketplace terminal summary',
      plugin_skills: 'tracked plugins/**/SKILL.md files',
      tracked_tree: 'git ls-files at the measured checkout',
    },
    graded_artifact_cohort: {
      cohort: 'graded_artifacts',
      reproduce: 'pnpm run measure:e1 -- --row=graded_artifact_cohort --stdout',
      values: skills,
    },
    rows: {
      1: row(
        'Tracked files, plugin SKILL.md, and plugin agent files',
        'tracked_tree',
        {
          plugin_agent_files: pluginAgents,
          plugin_skill_files: pluginSkills,
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
      ),
      3: row(
        'Tracked stale catalog shadows',
        'tracked .claude-plugin catalog-shaped files',
        {
          count: catalog.shadows.length,
          paths: catalog.shadows,
        },
        3,
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
      ),
      22: row(
        'Tracked generated artifacts without content drift gates',
        'six marketplace/src/data artifacts named by blueprint 727',
        {
          artifacts: generated,
          count: generated.filter((entry) => entry.tracked && !entry.content_drift_gate).length,
        },
        22,
      ),
      24: row(
        'Published answers to how many skills',
        'five separately named publication surfaces',
        {
          curated_manifest: countValue(curated.count ?? curated.skills?.length, 'curated manifest'),
          freshie_export: countValue(freshie.total, 'Freshie export'),
          plugin_source: pluginSkills,
          skills_index: countValue(skillsIndex.count ?? skillsIndex.skills?.length, 'skills index'),
          unified_search_index: countValue(unified.stats?.totalSkills, 'unified search index'),
        },
        24,
      ),
      25: row(
        'README metric writers',
        'tracked scripts that rewrite README skill/plugin/agent counts',
        {
          count: writerDetails.length,
          writers: writerDetails,
        },
        25,
      ),
      26: row(
        'Public stats without a freshness bound',
        'three rendered marketplace stats artifacts',
        {
          artifacts: stats,
          count: stats.filter((entry) => !entry.has_max_age_hours).length,
        },
        26,
      ),
      27: row(
        'sources.yaml versus sources.lock.json keys',
        'source names versus lock object keys',
        sources,
        27,
      ),
    },
    schema_version: 1,
  };
}

export function stableJson(value) {
  function sort(item) {
    if (Array.isArray(item)) return item.map(sort);
    if (item && typeof item === 'object') {
      return Object.fromEntries(
        Object.keys(item)
          .sort()
          .map((key) => [key, sort(item[key])]),
      );
    }
    return item;
  }
  const rendered = `${JSON.stringify(sort(value), null, 2)}\n`;
  if (/"(?:captured_at|generated_at|hostname|cwd|head)"\s*:/.test(rendered)) {
    fail('nondeterministic metadata entered output');
  }
  return rendered;
}

export function artifactMatches(actual, expected) {
  return actual === expected;
}

function parseArgs(argv) {
  const options = { check: false, root: SCRIPT_ROOT, row: null, stdout: false };
  for (const arg of argv) {
    if (arg === '--check') options.check = true;
    else if (arg === '--stdout') options.stdout = true;
    else if (arg.startsWith('--row=')) options.row = arg.slice(6);
    else if (arg.startsWith('--root=')) options.root = resolve(arg.slice(7));
    else fail(`unknown argument: ${arg}`);
  }
  if (options.row && !options.stdout) fail('--row requires --stdout');
  if (options.check && options.stdout) fail('--check and --stdout are mutually exclusive');
  return options;
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  const report = buildReport(options.root);
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
    if (!existsSync(artifact) || !artifactMatches(readFileSync(artifact, 'utf8'), rendered)) {
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
