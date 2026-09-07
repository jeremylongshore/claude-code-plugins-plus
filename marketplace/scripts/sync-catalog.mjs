#!/usr/bin/env node

/**
 * Render marketplace/src/data/catalog.json from canonical catalog and skill
 * projection inputs. The tracked output is never an input.
 */

import { readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, isAbsolute, join, posix } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

import {
  assertGeneratedContentCurrent,
} from '../../scripts/check-generated-artifacts.mjs';
import { normalizeDeadDomainValue } from '../../scripts/dead-domain-policy.mjs';

const require = createRequire(import.meta.url);
const { publishedPlugins } = require('../../scripts/publication-policy.cjs');

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const DEFAULT_ROOT = join(dirname(SCRIPT_PATH), '..', '..');
const OUTPUT_PATH = 'marketplace/src/data/catalog.json';
const EXTENDED_PATH = '.claude-plugin/marketplace.extended.json';
const SKILLS_PATH = 'marketplace/src/data/skills-catalog.json';

function requireObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
  return value;
}

function requireString(value, label) {
  if (typeof value !== 'string' || value.length === 0) {
    throw new Error(`${label} must be a non-empty string`);
  }
  return value;
}

function normalizedIdentity(value, label) {
  const name = requireString(value, label);
  if (name !== name.trim()) throw new Error(`${label} must not contain surrounding whitespace`);
  return name.toLocaleLowerCase('und');
}

export function normalizePluginPath(value, label = 'plugin path') {
  const original = requireString(value, label);
  const candidate = original.replaceAll('\\', '/').replace(/^\.\//, '');
  if (
    candidate.includes('\0') ||
    /[\r\n]/.test(candidate) ||
    isAbsolute(candidate) ||
    /^[A-Za-z]:\//.test(candidate) ||
    candidate.startsWith(':') ||
    candidate.split('/').includes('..')
  ) {
    throw new Error(`${label} escapes the repository: ${original}`);
  }
  const normalized = posix.normalize(candidate).replace(/\/$/, '');
  if (normalized !== candidate.replace(/\/$/, '') || !normalized.startsWith('plugins/')) {
    throw new Error(`${label} is not a normalized plugins path: ${original}`);
  }
  return normalized;
}

export function slugFromName(name) {
  return name.replace(/^\d{3}-jeremy-/, '').replace(/^\d{3}-/, '');
}

function displayNameFromSlug(slug) {
  return slug.replaceAll('-', ' ').toLowerCase();
}

function nonNegativeInteger(value, label) {
  if (value === undefined) return 0;
  if (!Number.isInteger(value) || value < 0) {
    throw new Error(`${label} must be a non-negative integer`);
  }
  return value;
}

function readJson(root, repositoryPath, label) {
  try {
    return JSON.parse(readFileSync(join(root, repositoryPath), 'utf8'));
  } catch (error) {
    throw new Error(`cannot read ${label} at ${repositoryPath}: ${error.message}`);
  }
}

export function renderCatalog(extendedCatalog, skillsCatalog) {
  const extended = requireObject(extendedCatalog, 'extended catalog');
  const skillProjection = requireObject(skillsCatalog, 'skills catalog');
  if (!Array.isArray(extended.plugins)) throw new Error('extended catalog plugins must be an array');
  if (!Array.isArray(skillProjection.skills)) throw new Error('skills catalog skills must be an array');

  const canonicalRows = [];
  const identities = new Set();
  const slugs = new Set();
  const canonicalSources = new Set();

  for (const [index, rawPlugin] of publishedPlugins(extended.plugins, 'extended catalog').entries()) {
    const plugin = requireObject(rawPlugin, `extended plugin ${index}`);
    const name = requireString(plugin.name, `extended plugin ${index} name`);
    const identity = normalizedIdentity(name, `extended plugin ${index} name`);
    if (identities.has(identity)) throw new Error(`duplicate catalog plugin identity: ${name}`);
    identities.add(identity);

    const slug = slugFromName(name);
    if (!slug || slugs.has(slug)) throw new Error(`duplicate or empty catalog plugin slug: ${slug}`);
    slugs.add(slug);

    const source = normalizePluginPath(plugin.source, `extended plugin ${name} source`);
    canonicalSources.add(source);
    const category = requireString(plugin.category, `extended plugin ${name} category`);
    const description = requireString(plugin.description, `extended plugin ${name} description`);
    const version = requireString(plugin.version, `extended plugin ${name} version`);
    if (plugin.keywords !== undefined && !Array.isArray(plugin.keywords)) {
      throw new Error(`extended plugin ${name} keywords must be an array`);
    }
    const keywords = (plugin.keywords ?? []).map((keyword, keywordIndex) =>
      requireString(keyword, `extended plugin ${name} keyword ${keywordIndex}`),
    );
    if (plugin.featured !== undefined && typeof plugin.featured !== 'boolean') {
      throw new Error(`extended plugin ${name} featured must be boolean`);
    }
    if (
      plugin.components !== undefined &&
      (!plugin.components || typeof plugin.components !== 'object' || Array.isArray(plugin.components))
    ) {
      throw new Error(`extended plugin ${name} components must be an object`);
    }
    if (
      plugin.author !== undefined &&
      plugin.author !== null &&
      (typeof plugin.author !== 'object' || Array.isArray(plugin.author))
    ) {
      throw new Error(`extended plugin ${name} author must be an object`);
    }

    canonicalRows.push({
      name,
      slug,
      source,
      sourcePath: plugin.source,
      displayName: displayNameFromSlug(slug),
      description,
      version,
      category,
      keywords,
      commandCount: nonNegativeInteger(
        plugin.components?.commands,
        `extended plugin ${name} command count`,
      ),
      isFeatured: plugin.featured === true,
      author: plugin.author ?? { name: 'Claude Code Plugins' },
    });
  }

  const skillCounts = new Map();
  const skillPaths = new Set();
  if (
    skillProjection.count !== undefined &&
    (!Number.isInteger(skillProjection.count) || skillProjection.count !== skillProjection.skills.length)
  ) {
    throw new Error('skills catalog count does not match skills array length');
  }
  for (const [index, rawSkill] of skillProjection.skills.entries()) {
    const skill = requireObject(rawSkill, `skill ${index}`);
    const parent = requireObject(skill.parentPlugin, `skill ${index} parentPlugin`);
    const parentPath = normalizePluginPath(parent.path, `skill ${index} parentPlugin.path`);
    const filePath = normalizePluginPath(skill.filePath, `skill ${index} filePath`);
    if (!filePath.startsWith(`${parentPath}/`)) {
      throw new Error(`skill ${index} filePath is outside parent plugin: ${filePath}`);
    }
    if (!filePath.endsWith('/SKILL.md')) {
      throw new Error(`skill ${index} filePath is not a SKILL.md path: ${filePath}`);
    }
    if (skillPaths.has(filePath)) throw new Error(`duplicate skill filePath: ${filePath}`);
    skillPaths.add(filePath);
    skillCounts.set(parentPath, (skillCounts.get(parentPath) ?? 0) + 1);
  }

  for (const parentPath of skillCounts.keys()) {
    if (!canonicalSources.has(parentPath)) {
      throw new Error(`skills catalog parent has no canonical plugin source: ${parentPath}`);
    }
  }

  const byCategory = new Map();
  let totalCommands = 0;
  let pluginsWithSkills = 0;
  let featured = 0;
  const plugins = canonicalRows.map((plugin) => {
    const skillCount = skillCounts.get(plugin.source) ?? 0;
    byCategory.set(plugin.category, (byCategory.get(plugin.category) ?? 0) + 1);
    totalCommands += plugin.commandCount;
    if (skillCount > 0) pluginsWithSkills += 1;
    if (plugin.isFeatured) featured += 1;
    return {
      slug: plugin.slug,
      name: plugin.name,
      displayName: plugin.displayName,
      description: plugin.description,
      version: plugin.version,
      category: plugin.category,
      keywords: plugin.keywords,
      hasSkills: skillCount > 0,
      skillCount,
      commandCount: plugin.commandCount,
      installCommand: `/plugin install ${plugin.name}`,
      sourcePath: plugin.sourcePath,
      isFeatured: plugin.isFeatured,
      author: plugin.author,
      type: 'instruction-plugin',
    };
  });

  return normalizeDeadDomainValue({
    meta: {
      version: '1.0.0',
      source: 'marketplace.extended.json + skills-catalog.json',
      generator: 'marketplace/scripts/sync-catalog.mjs',
    },
    stats: {
      totalPlugins: plugins.length,
      totalSkills: skillPaths.size,
      totalCommands,
      pluginsWithSkills,
      byCategory: Object.fromEntries(byCategory),
      featured,
    },
    plugins,
  });
}

export function renderCatalogBytes(extendedCatalog, skillsCatalog) {
  return `${JSON.stringify(renderCatalog(extendedCatalog, skillsCatalog), null, 2)}\n`;
}

export function syncCatalog({ root = DEFAULT_ROOT, check = false } = {}) {
  const extended = readJson(root, EXTENDED_PATH, 'extended catalog');
  const skills = readJson(root, SKILLS_PATH, 'skills catalog');
  const contents = renderCatalogBytes(extended, skills);
  if (check) {
    assertGeneratedContentCurrent([{ path: OUTPUT_PATH, contents }], { root });
  } else {
    // Keep the literal target in the real write path so the Epic 1 harness can
    // discover this producer without a parallel hand-maintained writer list.
    const temporary = join(
      root,
      `marketplace/src/data/catalog.json.tmp-${process.pid}`,
    );
    try {
      writeFileSync(
        temporary /* atomic target: marketplace/src/data/catalog.json */,
        contents,
        { flag: 'wx' },
      );
      renameSync(temporary, join(root, OUTPUT_PATH));
    } finally {
      rmSync(temporary, { force: true });
    }
  }
  const catalog = JSON.parse(contents);
  return {
    contents,
    plugins: catalog.stats.totalPlugins,
    skills: catalog.stats.totalSkills,
    commands: catalog.stats.totalCommands,
  };
}

function main() {
  const unknown = process.argv.slice(2).filter((argument) => argument !== '--check');
  if (unknown.length > 0) throw new Error(`unknown argument(s): ${unknown.join(', ')}`);
  const check = process.argv.includes('--check');
  const result = syncCatalog({ check });
  console.log(
    `catalog projection: ${check ? 'OK' : 'generated'} (${result.plugins} plugins, ${result.skills} distinct skills, ${result.commands} commands)`,
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main();
  } catch (error) {
    console.error(`catalog projection: ${error.message}`);
    process.exitCode = 1;
  }
}
