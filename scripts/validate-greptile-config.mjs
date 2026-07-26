#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const CONFIG_DIR = '.greptile';
const SKIP_DIRS = new Set(['.git', 'node_modules', 'dist', 'build', 'coverage', '.astro']);
const FILTER_ARRAY_FIELDS = [
  'labels',
  'disabledLabels',
  'includeAuthors',
  'excludeAuthors',
  'includeBranches',
  'excludeBranches',
  'commentTypes',
  'disabledRules',
];

function readJson(file, errors) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (error) {
    errors.push(`${file}: invalid JSON (${error.message})`);
    return null;
  }
}

function validateStringArray(value, label, errors) {
  if (!Array.isArray(value) || value.some((item) => typeof item !== 'string' || !item.trim())) {
    errors.push(`${label}: expected an array of non-empty strings`);
  }
}

function validateScopes(scope, label, errors) {
  validateStringArray(scope, label, errors);
  if (Array.isArray(scope) && scope.some((pattern) => pattern.includes('../'))) {
    errors.push(`${label}: parent-directory patterns are not allowed`);
  }
}

function findGreptileDirs(repoRoot) {
  const found = [];

  function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (!entry.isDirectory() || SKIP_DIRS.has(entry.name)) continue;
      const child = path.join(dir, entry.name);
      if (entry.name === CONFIG_DIR) {
        found.push(child);
      } else {
        walk(child);
      }
    }
  }

  walk(repoRoot);
  return found.sort();
}

function validateConfig(configPath, config, globalRuleIds, errors, stats) {
  if (!config || typeof config !== 'object' || Array.isArray(config)) {
    errors.push(`${configPath}: top level must be an object`);
    return;
  }

  for (const field of FILTER_ARRAY_FIELDS) {
    if (field in config) validateStringArray(config[field], `${configPath}:${field}`, errors);
  }

  if ('strictness' in config && ![1, 2, 3].includes(config.strictness)) {
    errors.push(`${configPath}:strictness must be 1, 2, or 3`);
  }

  if ('ignorePatterns' in config && typeof config.ignorePatterns !== 'string') {
    errors.push(`${configPath}:ignorePatterns must be a newline-separated string`);
  }

  if (config.context?.repos !== undefined) {
    validateStringArray(config.context.repos, `${configPath}:context.repos`, errors);
    const repos = config.context.repos;
    if (Array.isArray(repos)) {
      if (new Set(repos).size !== repos.length) {
        errors.push(`${configPath}:context.repos contains duplicates`);
      }
      for (const repo of repos) {
        if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo)) {
          errors.push(
            `${configPath}:context.repos has invalid owner/repo value ${JSON.stringify(repo)}`,
          );
        }
      }
    }
  }

  if (config.rules === undefined) return;
  if (!Array.isArray(config.rules)) {
    errors.push(`${configPath}:rules must be an array`);
    return;
  }

  for (const [index, rule] of config.rules.entries()) {
    const label = `${configPath}:rules[${index}]`;
    if (!rule || typeof rule !== 'object' || Array.isArray(rule)) {
      errors.push(`${label}: expected an object`);
      continue;
    }
    if (typeof rule.id !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(rule.id)) {
      errors.push(`${label}: id must be stable lowercase kebab-case`);
    } else if (globalRuleIds.has(rule.id)) {
      errors.push(`${label}: duplicate rule id ${rule.id}`);
    } else {
      globalRuleIds.add(rule.id);
    }
    if (typeof rule.rule !== 'string' || rule.rule.trim().length < 20) {
      errors.push(`${label}: rule must be a specific non-empty instruction`);
    }
    if (rule.severity !== undefined && !['low', 'medium', 'high'].includes(rule.severity)) {
      errors.push(`${label}: severity must be low, medium, or high`);
    }
    if (rule.scope !== undefined) validateScopes(rule.scope, `${label}:scope`, errors);
    if (rule.enabled !== undefined && typeof rule.enabled !== 'boolean') {
      errors.push(`${label}: enabled must be boolean`);
    }
    stats.rules += 1;
  }
}

function validateFiles(filesPath, data, errors, stats) {
  if (!data || typeof data !== 'object' || !Array.isArray(data.files)) {
    errors.push(`${filesPath}: expected an object with a files array`);
    return;
  }
  const scopeRoot = path.dirname(path.dirname(filesPath));
  for (const [index, item] of data.files.entries()) {
    const label = `${filesPath}:files[${index}]`;
    if (!item || typeof item !== 'object' || Array.isArray(item)) {
      errors.push(`${label}: expected an object`);
      continue;
    }
    if (typeof item.path !== 'string' || !item.path.trim() || item.path.includes('../')) {
      errors.push(`${label}: path must be a non-empty local path without ../`);
    } else if (!fs.existsSync(path.resolve(scopeRoot, item.path))) {
      errors.push(`${label}: referenced file does not exist: ${item.path}`);
    }
    if (item.description !== undefined && typeof item.description !== 'string') {
      errors.push(`${label}: description must be a string`);
    }
    if (item.scope !== undefined) validateScopes(item.scope, `${label}:scope`, errors);
    stats.files += 1;
  }
}

export function validateRepository(repoRoot) {
  const root = path.resolve(repoRoot);
  const errors = [];
  const stats = { configDirs: 0, rules: 0, files: 0 };
  const globalRuleIds = new Set();
  const rootConfig = path.join(root, CONFIG_DIR, 'config.json');

  if (!fs.existsSync(rootConfig)) {
    errors.push(`${rootConfig}: root Greptile config is required`);
  }

  for (const greptileDir of findGreptileDirs(root)) {
    stats.configDirs += 1;
    const configPath = path.join(greptileDir, 'config.json');
    const filesPath = path.join(greptileDir, 'files.json');
    const rulesPath = path.join(greptileDir, 'rules.md');

    if (fs.existsSync(configPath)) {
      validateConfig(configPath, readJson(configPath, errors), globalRuleIds, errors, stats);
    }
    if (fs.existsSync(filesPath)) {
      validateFiles(filesPath, readJson(filesPath, errors), errors, stats);
    }
    if (fs.existsSync(rulesPath) && !fs.readFileSync(rulesPath, 'utf8').trim()) {
      errors.push(`${rulesPath}: rules.md must not be empty`);
    }
  }

  return { errors, stats };
}

function main() {
  const repoRoot = process.argv[2]
    ? path.resolve(process.argv[2])
    : path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
  const { errors, stats } = validateRepository(repoRoot);
  if (errors.length) {
    for (const error of errors) console.error(`greptile-config: ${error}`);
    console.error(
      `greptile-config: FAIL (${errors.length} error${errors.length === 1 ? '' : 's'})`,
    );
    process.exitCode = 1;
    return;
  }
  console.log(
    `greptile-config: OK (${stats.configDirs} config dirs, ${stats.rules} rules, ${stats.files} context files)`,
  );
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
