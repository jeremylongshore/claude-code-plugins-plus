#!/usr/bin/env node

/**
 * Canonical skill-corpus resolver.
 *
 * Every caller receives sorted repository-relative SKILL.md paths. Production
 * resolution uses Git's tracked tree so ignored or untracked local files cannot
 * change published counts. Tests may inject an explicit path inventory.
 */

import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { resolvePluginProvenance } from './plugin-provenance.mjs';

export const CORPUS_COHORTS = Object.freeze([
  'marketplace-visible',
  'graded',
  'first-party',
  'curated-mirror',
  'curriculum',
]);

const EXCLUDED_GRADED_SEGMENTS = new Set([
  '.curated',
  '.experimental',
  '.git',
  '.venv',
  '000-docs',
  '002-workspaces',
  '010-archive',
  '__pycache__',
  'archive',
  'backup',
  'backups',
  'node_modules',
]);

function fail(message) {
  throw new Error(`corpus-resolver: ${message}`);
}

function toPosix(value) {
  return value.split(path.sep).join('/');
}

function normalizePath(value) {
  if (typeof value !== 'string' || value.length === 0 || value.includes('\0')) {
    fail('path inventory contains an invalid entry');
  }
  const normalized = path.posix.normalize(value.replaceAll('\\', '/').replace(/^\.\//, ''));
  if (normalized === '..' || normalized.startsWith('../') || path.posix.isAbsolute(normalized)) {
    fail(`path escapes repository: ${value}`);
  }
  return normalized;
}

function trackedPaths(root) {
  if (!fs.existsSync(path.join(root, '.git'))) return filesystemPaths(root);
  try {
    return execFileSync('git', ['ls-files', '-z'], {
      cwd: root,
      encoding: 'utf8',
      maxBuffer: 128 * 1024 * 1024,
    })
      .split('\0')
      .filter(Boolean);
  } catch (error) {
    fail(`cannot read tracked tree: ${error instanceof Error ? error.message : String(error)}`);
  }
}

function filesystemPaths(root) {
  const output = [];
  const walk = (directory) => {
    let entries;
    try {
      entries = fs.readdirSync(directory, { withFileTypes: true });
    } catch (error) {
      fail(
        `cannot read ${toPosix(path.relative(root, directory))}: ${error instanceof Error ? error.message : String(error)}`,
      );
    }
    for (const entry of entries) {
      if (entry.name === '.git' || entry.name === 'node_modules') continue;
      const absolute = path.join(directory, entry.name);
      if (entry.isSymbolicLink())
        fail(`symbolic link is not a corpus authority: ${toPosix(path.relative(root, absolute))}`);
      if (entry.isDirectory()) walk(absolute);
      else if (entry.isFile()) output.push(toPosix(path.relative(root, absolute)));
    }
  };
  walk(root);
  return output;
}

function skillPaths(paths) {
  return [...new Set(paths.map(normalizePath).filter((entry) => entry.endsWith('/SKILL.md')))].sort(
    (left, right) => left.localeCompare(right),
  );
}

function readCatalog(root) {
  const catalogPath = path.join(root, '.claude-plugin', 'marketplace.extended.json');
  let catalog;
  try {
    catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
  } catch (error) {
    fail(
      `cannot read marketplace catalog: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
  if (!Array.isArray(catalog?.plugins)) fail('marketplace catalog has no plugins array');

  const names = new Set();
  const roots = new Set();
  for (const [index, plugin] of catalog.plugins.entries()) {
    if (typeof plugin?.name !== 'string' || plugin.name.length === 0) {
      fail(`catalog plugin ${index} has no name`);
    }
    names.add(plugin.name);
    if (typeof plugin.source !== 'string') fail(`catalog plugin ${index} has no source path`);
    const source = normalizePath(plugin.source);
    if (!source.startsWith('plugins/')) {
      fail(`catalog plugin ${index} source is outside plugins/: ${plugin.source}`);
    }
    roots.add(source.replace(/\/$/, ''));
  }
  return { names, roots };
}

function isPluginSkill(entry) {
  return entry.startsWith('plugins/');
}

function isCurriculumSkill(entry) {
  if (!entry.startsWith('skills/')) return false;
  const segments = entry.split('/');
  return (
    /^\d{2}-/.test(segments[1] ?? '') && !segments.some((segment) => segment === '.experimental')
  );
}

function isLegacySkill(entry) {
  return entry.startsWith('003-skills/') && entry.endsWith('/SKILL.md');
}

function isGradedSkill(entry) {
  if (!isPluginSkill(entry) && !isCurriculumSkill(entry) && !isLegacySkill(entry)) return false;
  const segments = entry.split('/');
  if (segments.some((segment) => EXCLUDED_GRADED_SEGMENTS.has(segment))) return false;
  if (segments.some((segment) => segment.startsWith('skills-backup-'))) return false;

  if (isCurriculumSkill(entry) || isLegacySkill(entry)) return true;
  const atPluginRoot = /^plugins\/[^/]+\/[^/]+\/SKILL\.md$/.test(entry);
  const inSkillDirectory = /\/skills\/[^/]+\/SKILL\.md$/.test(entry);
  return atPluginRoot || inSkillDirectory;
}

function marketplacePluginName(entry, root) {
  const segments = entry.split('/');
  let current = path.dirname(path.join(root, entry));
  for (let depth = 0; depth < 10 && current.startsWith(root); depth += 1) {
    const manifest = path.join(current, '.claude-plugin', 'plugin.json');
    if (fs.existsSync(manifest)) {
      const relative = toPosix(path.relative(root, current));
      const parts = relative.split('/');
      const skillsIndex = parts.indexOf('skills');
      if (skillsIndex < 0 || skillsIndex === parts.length - 1) {
        let value;
        try {
          value = JSON.parse(fs.readFileSync(manifest, 'utf8'));
        } catch (error) {
          fail(
            `cannot read plugin manifest ${relative}/.claude-plugin/plugin.json: ${error instanceof Error ? error.message : String(error)}`,
          );
        }
        return typeof value?.name === 'string' && value.name.length > 0
          ? value.name
          : path.basename(current);
      }
    }
    if (current === root) break;
    current = path.dirname(current);
  }
  const skillsIndex = segments.indexOf('skills');
  if (skillsIndex >= 2) return segments[skillsIndex - 1];
  return segments.length >= 3 ? segments[2] : null;
}

function marketplaceVisible(entries, root) {
  const catalog = readCatalog(root);
  return entries.filter((entry) => {
    if (!isPluginSkill(entry)) return false;
    const segments = entry.split('/');
    if (segments.some((segment) => segment.startsWith('.'))) return false;
    const pluginName = marketplacePluginName(entry, root);
    return pluginName !== null && catalog.names.has(pluginName);
  });
}

function firstParty(entries, root) {
  const output = [];
  for (const entry of entries.filter(isPluginSkill)) {
    const result = resolvePluginProvenance(path.posix.dirname(entry), { root });
    if (result.status === 'refused') {
      fail(`${result.reasonCode} while resolving ${entry}`);
    }
    if (result.status === 'first-party') output.push(entry);
  }
  return output;
}

function curatedMirror(entries, root, inventory) {
  const files = entries.filter((entry) => entry.startsWith('skills/.curated/'));
  if (!inventory.includes('skills/.curated/MANIFEST.json')) return files;

  let manifest;
  try {
    manifest = JSON.parse(
      fs.readFileSync(path.join(root, 'skills', '.curated', 'MANIFEST.json'), 'utf8'),
    );
  } catch (error) {
    fail(`cannot read curated manifest: ${error instanceof Error ? error.message : String(error)}`);
  }
  if (!Array.isArray(manifest?.skills) || manifest.count !== manifest.skills.length) {
    fail('curated manifest count contradicts its skill rows');
  }
  const declared = manifest.skills.map((entry, index) => {
    if (typeof entry?.curated_name !== 'string' || entry.curated_name.length === 0) {
      fail(`curated manifest row ${index} has no curated_name`);
    }
    return `skills/.curated/${entry.curated_name}/SKILL.md`;
  });
  const declaredSet = new Set(declared);
  const fileSet = new Set(files);
  if (
    declaredSet.size !== declared.length ||
    declaredSet.size !== fileSet.size ||
    declared.some((entry) => !fileSet.has(entry))
  ) {
    fail('curated manifest membership contradicts the tracked curated-mirror cohort');
  }
  return files;
}

export function resolveCorpus(cohort, { root = process.cwd(), paths } = {}) {
  if (!CORPUS_COHORTS.includes(cohort)) {
    fail(`unknown cohort ${JSON.stringify(cohort)}; expected ${CORPUS_COHORTS.join(', ')}`);
  }
  let rootPath;
  try {
    rootPath = fs.realpathSync(path.resolve(root));
  } catch (error) {
    fail(
      `cannot resolve repository root: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
  const inventory = (paths ?? trackedPaths(rootPath)).map(normalizePath);
  const entries = skillPaths(inventory);

  switch (cohort) {
    case 'marketplace-visible':
      return marketplaceVisible(entries, rootPath);
    case 'graded':
      return entries.filter(isGradedSkill);
    case 'first-party':
      return firstParty(entries, rootPath);
    case 'curated-mirror':
      return curatedMirror(entries, rootPath, inventory);
    case 'curriculum':
      return entries.filter(isCurriculumSkill);
    default:
      fail(`unreachable cohort ${cohort}`);
  }
}

function parseCli(argv) {
  const options = { cohort: null, root: process.cwd() };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === '--cohort') options.cohort = argv[++index];
    else if (argument.startsWith('--cohort=')) options.cohort = argument.slice('--cohort='.length);
    else if (argument === '--root') options.root = argv[++index];
    else if (argument.startsWith('--root=')) options.root = argument.slice('--root='.length);
    else if (argument !== '--json') fail(`unknown argument ${argument}`);
  }
  if (!options.cohort) fail('--cohort is required');
  return options;
}

const invokedPath = process.argv[1] ? path.resolve(process.argv[1]) : null;
if (invokedPath === fileURLToPath(import.meta.url)) {
  try {
    const options = parseCli(process.argv.slice(2));
    const files = resolveCorpus(options.cohort, { root: options.root });
    process.stdout.write(
      `${JSON.stringify({ cohort: options.cohort, count: files.length, files })}\n`,
    );
  } catch (error) {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  }
}
