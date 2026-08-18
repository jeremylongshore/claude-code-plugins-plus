#!/usr/bin/env node

/**
 * Render marketplace/src/data/unified-search-index.json from deterministic
 * repository inputs. The tracked output is never an input.
 */

import { lstatSync, readFileSync, readdirSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { assertGeneratedContentCurrent } from '../../scripts/check-generated-artifacts.mjs';
import { normalizeDeadDomainValue } from '../../scripts/dead-domain-policy.mjs';

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const DEFAULT_ROOT = join(dirname(SCRIPT_PATH), '..', '..');
const OUTPUT_PATH = 'marketplace/src/data/unified-search-index.json';
const CATALOG_PATH = 'marketplace/src/data/catalog.json';
const SKILLS_PATH = 'marketplace/src/data/skills-catalog.json';
const EXTENDED_PATH = '.claude-plugin/marketplace.extended.json';
const PLUGINS_PATH = 'plugins';
const DOCS_PATH = 'marketplace/src/content/docs';
const WALK_SKIP = new Set(['node_modules', 'dist', 'build', '.git', '.next', '.astro']);

export function compareOrdinal(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

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

function requireSlug(value, label) {
  const slug = requireString(value, label);
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
    throw new Error(`${label} must be a lowercase kebab-case path segment`);
  }
  return slug;
}

function optionalString(value, label) {
  if (value === undefined || value === null) return '';
  if (typeof value !== 'string') throw new Error(`${label} must be a string`);
  return value;
}

function searchableDescription(value, label) {
  if (value === undefined || value === null) return { value: '', text: '' };
  if (typeof value === 'string') return { value, text: value };
  if (Array.isArray(value)) {
    const entries = stringArray(value, label);
    return { value: entries, text: entries.join(' ') };
  }
  throw new Error(`${label} must be a string or string array`);
}

function stringArray(value, label, fallback = [], { allowEmpty = false } = {}) {
  if (value === undefined || value === null) return fallback;
  if (!Array.isArray(value)) throw new Error(`${label} must be an array`);
  return value.map((entry, index) => {
    if (typeof entry !== 'string' || (!allowEmpty && entry.length === 0)) {
      throw new Error(
        `${label} ${index} must be ${allowEmpty ? 'a string' : 'a non-empty string'}`,
      );
    }
    return entry;
  });
}

function nonNegativeInteger(value, label, fallback = 0) {
  if (value === undefined) return fallback;
  if (!Number.isInteger(value) || value < 0) {
    throw new Error(`${label} must be a non-negative integer`);
  }
  return value;
}

function assertRepositoryPath(root, repositoryPath, finalKind) {
  const components = repositoryPath.split('/');
  if (components.some((component) => !component || component === '.' || component === '..')) {
    throw new Error(`unsafe repository path: ${repositoryPath}`);
  }
  let current = root;
  for (const [index, component] of components.entries()) {
    current = join(current, component);
    const label = components.slice(0, index + 1).join('/');
    let stat;
    try {
      stat = lstatSync(current);
    } catch (error) {
      throw new Error(`cannot inspect ${label}: ${error.message}`);
    }
    if (stat.isSymbolicLink()) throw new Error(`${label} must not be a symlink`);
    const isFinal = index === components.length - 1;
    if (!isFinal && !stat.isDirectory()) throw new Error(`${label} must be a regular directory`);
    if (isFinal && finalKind === 'file' && !stat.isFile()) {
      throw new Error(`${label} must be a regular file`);
    }
    if (isFinal && finalKind === 'directory' && !stat.isDirectory()) {
      throw new Error(`${label} must be a regular directory`);
    }
  }
}

function readJson(root, repositoryPath, label) {
  try {
    const path = join(root, repositoryPath);
    assertRepositoryPath(root, repositoryPath, 'file');
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch (error) {
    throw new Error(`cannot read ${label} at ${repositoryPath}: ${error.message}`);
  }
}

function readDirectory(path, label) {
  try {
    const stat = lstatSync(path);
    if (stat.isSymbolicLink() || !stat.isDirectory()) {
      throw new Error(`${label} must be a regular directory`);
    }
    return readdirSync(path, { withFileTypes: true }).sort((left, right) =>
      compareOrdinal(left.name, right.name),
    );
  } catch (error) {
    throw new Error(`cannot read ${label}: ${error.message}`);
  }
}

function assertRegularFile(path, label) {
  let stat;
  try {
    stat = lstatSync(path);
  } catch (error) {
    throw new Error(`cannot inspect ${label}: ${error.message}`);
  }
  if (stat.isSymbolicLink() || !stat.isFile()) {
    throw new Error(`${label} must be a regular file`);
  }
}

function assertReadableRegularFile(path, label, readFile) {
  assertRegularFile(path, label);
  try {
    readFile(path);
  } catch (error) {
    throw new Error(`cannot read ${label}: ${error.message}`);
  }
}

function countSurfaceFiles(directory, extensions, label, readFile) {
  let count = 0;
  for (const entry of readDirectory(directory, label)) {
    const entryPath = join(directory, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`${label}/${entry.name} must not be a symlink`);
    if (entry.isFile() && extensions.some((extension) => entry.name.endsWith(extension))) {
      assertReadableRegularFile(entryPath, `${label}/${entry.name}`, readFile);
      count += 1;
    }
  }
  return count;
}

export function countAgentsAndHooks(root = DEFAULT_ROOT, { readFile = readFileSync } = {}) {
  const pluginsRoot = join(root, PLUGINS_PATH);
  assertRepositoryPath(root, PLUGINS_PATH, 'directory');

  let totalAgents = 0;
  let totalHooks = 0;
  let pluginsWithAgents = 0;
  let pluginsWithHooks = 0;

  function walk(directory) {
    const entries = readDirectory(directory, relative(root, directory) || PLUGINS_PATH);
    for (const surface of [
      { name: 'agents', extensions: ['.md'], total: 'agents' },
      { name: 'hooks', extensions: ['.json', '.sh'], total: 'hooks' },
    ]) {
      const entry = entries.find((candidate) => candidate.name === surface.name);
      if (!entry) continue;
      if (entry.isSymbolicLink() || !entry.isDirectory()) {
        throw new Error(
          `${relative(root, join(directory, surface.name))} must be a regular directory`,
        );
      }
      const count = countSurfaceFiles(
        join(directory, surface.name),
        surface.extensions,
        relative(root, join(directory, surface.name)),
        readFile,
      );
      if (surface.total === 'agents') {
        totalAgents += count;
        if (count > 0) pluginsWithAgents += 1;
      } else {
        totalHooks += count;
        if (count > 0) pluginsWithHooks += 1;
      }
    }

    for (const entry of entries) {
      if (WALK_SKIP.has(entry.name)) continue;
      if (entry.isSymbolicLink()) {
        throw new Error(`${relative(root, join(directory, entry.name))} must not be a symlink`);
      }
      if (!entry.isDirectory()) continue;
      if (entry.name === 'agents' || entry.name === 'hooks') continue;
      walk(join(directory, entry.name));
    }
  }

  walk(pluginsRoot);
  return { totalAgents, totalHooks, pluginsWithAgents, pluginsWithHooks };
}

export function parseDocFrontmatter(content, label = 'document') {
  if (typeof content !== 'string') throw new Error(`${label} content must be a string`);
  const normalized = content.replaceAll('\r\n', '\n');
  const match = normalized.match(/^---\n([\s\S]*?)\n---(?:\n|$)/);
  if (!match) throw new Error(`${label} is missing YAML frontmatter`);

  const frontmatter = {};
  let currentKey = null;
  for (const line of match[1].split('\n')) {
    const keyValue = line.match(/^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$/);
    if (keyValue) {
      currentKey = keyValue[1];
      const value = keyValue[2].trim();
      if (value === '') {
        frontmatter[currentKey] = [];
      } else if (value.startsWith('[')) {
        let parsed;
        try {
          parsed = JSON.parse(value);
        } catch (error) {
          throw new Error(`${label} ${currentKey} inline list is invalid: ${error.message}`);
        }
        frontmatter[currentKey] = stringArray(parsed, `${label} ${currentKey}`);
      } else {
        frontmatter[currentKey] = value.replace(/^["']|["']$/g, '');
      }
      continue;
    }
    const item = line.match(/^\s+-\s+(.*)$/);
    if (item && currentKey && Array.isArray(frontmatter[currentKey])) {
      const value = item[1].trim().replace(/^["']|["']$/g, '');
      if (!/^[A-Za-z][A-Za-z0-9_-]*:\s/.test(value)) frontmatter[currentKey].push(value);
    }
  }
  requireString(frontmatter.title, `${label} title`);
  if (frontmatter.description !== undefined && typeof frontmatter.description !== 'string') {
    throw new Error(`${label} description must be a string`);
  }
  if (frontmatter.section !== undefined && typeof frontmatter.section !== 'string') {
    throw new Error(`${label} section must be a string`);
  }
  if (frontmatter.keywords !== undefined && !Array.isArray(frontmatter.keywords)) {
    throw new Error(`${label} keywords must be a list`);
  }
  return frontmatter;
}

export function readDocs(root = DEFAULT_ROOT) {
  const docsRoot = join(root, DOCS_PATH);
  const docs = [];
  assertRepositoryPath(root, DOCS_PATH, 'directory');

  function walk(directory) {
    for (const entry of readDirectory(directory, relative(root, directory))) {
      const entryPath = join(directory, entry.name);
      if (entry.isSymbolicLink()) {
        throw new Error(`${relative(root, entryPath)} must not be a symlink`);
      }
      if (entry.isDirectory()) {
        walk(entryPath);
      } else if (entry.name.endsWith('.md')) {
        assertRegularFile(entryPath, relative(root, entryPath));
        const slug = relative(docsRoot, entryPath).split(sep).join('/').replace(/\.md$/, '');
        if (!slug || slug.startsWith('../')) throw new Error(`invalid documentation slug: ${slug}`);
        const frontmatter = parseDocFrontmatter(
          readFileSync(entryPath, 'utf8'),
          relative(root, entryPath),
        );
        const keywords = frontmatter.keywords ?? [];
        docs.push({
          type: 'docs',
          id: `docs/${slug}`,
          slug,
          name: frontmatter.title,
          description: frontmatter.description ?? '',
          category: frontmatter.section ?? 'docs',
          keywords,
          url: `/docs/${slug}/`,
          searchText:
            `${frontmatter.title} ${frontmatter.description ?? ''} ${frontmatter.section ?? ''} ${keywords.join(' ')}`.toLowerCase(),
        });
      }
    }
  }

  walk(docsRoot);
  docs.sort((left, right) => compareOrdinal(left.slug, right.slug));
  assertUnique(docs, 'id', 'documentation');
  return docs;
}

export function getAuthorType(author) {
  if (!author) return 'community';
  const value = requireObject(author, 'plugin author');
  const name = optionalString(value.name, 'plugin author name').toLowerCase();
  const email = optionalString(value.email, 'plugin author email').toLowerCase();
  if (
    name.includes('jeremy longshore') ||
    email.endsWith('@intentsolutions.io') ||
    name.includes('claude code plugins team') ||
    name.includes('claude code plugin hub') ||
    name.includes('claude code plugins') ||
    name === 'claudecodeplugins' ||
    name.includes('intent solutions') ||
    name === 'community'
  ) {
    return 'official';
  }
  return 'community';
}

function assertUnique(rows, key, label) {
  const seen = new Set();
  for (const [index, row] of rows.entries()) {
    const value = requireString(row[key], `${label} ${index} ${key}`);
    const normalized = value.normalize('NFC').toLocaleLowerCase('und');
    if (seen.has(normalized)) throw new Error(`duplicate ${label} ${key}: ${value}`);
    seen.add(normalized);
  }
}

export function renderUnifiedSearch({
  catalogData,
  skillsData,
  extendedData,
  docs,
  agentHookStats,
}) {
  const catalog = requireObject(catalogData, 'catalog');
  const skillsCatalog = requireObject(skillsData, 'skills catalog');
  const extended = requireObject(extendedData, 'extended catalog');
  const stats = requireObject(agentHookStats, 'agent and hook stats');
  if (!Array.isArray(catalog.plugins)) throw new Error('catalog plugins must be an array');
  if (!Array.isArray(skillsCatalog.skills))
    throw new Error('skills catalog skills must be an array');
  if (!Array.isArray(extended.plugins))
    throw new Error('extended catalog plugins must be an array');
  if (!Array.isArray(docs)) throw new Error('documents must be an array');
  if (
    skillsCatalog.count !== undefined &&
    (!Number.isInteger(skillsCatalog.count) || skillsCatalog.count !== skillsCatalog.skills.length)
  ) {
    throw new Error('skills catalog count does not match skills array length');
  }

  assertUnique(catalog.plugins, 'slug', 'plugin');
  assertUnique(skillsCatalog.skills, 'slug', 'skill');

  const verificationMap = new Map();
  const extendedNames = new Set();
  for (const [index, rawPlugin] of extended.plugins.entries()) {
    const plugin = requireObject(rawPlugin, `extended plugin ${index}`);
    const name = requireString(plugin.name, `extended plugin ${index} name`);
    const normalizedName = name.normalize('NFC').toLocaleLowerCase('und');
    if (extendedNames.has(normalizedName)) {
      throw new Error(`duplicate extended plugin name: ${name}`);
    }
    extendedNames.add(normalizedName);
    if (plugin.verification !== undefined) {
      verificationMap.set(
        name,
        requireObject(plugin.verification, `extended plugin ${name} verification`),
      );
    }
  }

  const plugins = catalog.plugins.map((rawPlugin, index) => {
    const plugin = requireObject(rawPlugin, `catalog plugin ${index}`);
    const slug = requireSlug(plugin.slug, `catalog plugin ${index} slug`);
    const name = requireString(plugin.name, `catalog plugin ${index} name`);
    const displayName =
      optionalString(plugin.displayName, `catalog plugin ${name} displayName`) || name;
    const description = requireString(plugin.description, `catalog plugin ${name} description`);
    const category = requireString(plugin.category, `catalog plugin ${name} category`);
    const keywords = stringArray(plugin.keywords ?? plugin.tags, `catalog plugin ${name} keywords`);
    const verification = verificationMap.get(name) ?? null;
    return {
      type: 'plugin',
      id: slug,
      slug,
      name,
      displayName,
      description,
      category,
      keywords,
      author: plugin.author,
      authorType: getAuthorType(plugin.author),
      version: requireString(plugin.version, `catalog plugin ${name} version`),
      isFeatured: plugin.isFeatured === true,
      isNew: plugin.isNew === true,
      badges: stringArray(plugin.badges, `catalog plugin ${name} badges`),
      skillCount: nonNegativeInteger(plugin.skillCount, `catalog plugin ${name} skillCount`),
      ...(verification && {
        verificationScore: verification.score,
        verificationGrade: verification.grade,
        verificationBadge: verification.badge,
      }),
      searchText: `${displayName} ${description} ${category} ${keywords.join(' ')}`.toLowerCase(),
    };
  });

  const skills = skillsCatalog.skills.map((rawSkill, index) => {
    const skill = requireObject(rawSkill, `skill ${index}`);
    const parent = requireObject(skill.parentPlugin, `skill ${index} parentPlugin`);
    const slug = requireSlug(skill.slug, `skill ${index} slug`);
    const name = requireString(skill.name, `skill ${index} name`);
    const description = searchableDescription(skill.description, `skill ${name} description`);
    const category = requireString(parent.category, `skill ${name} parent category`);
    const allowedTools = stringArray(skill.allowedTools, `skill ${name} allowedTools`, [], {
      allowEmpty: true,
    });
    const compatibleWith = stringArray(skill.compatibleWith, `skill ${name} compatibleWith`, [], {
      allowEmpty: true,
    });
    const parentSlug = optionalString(parent.slug, `skill ${name} parent slug`);
    if (parentSlug) requireSlug(parentSlug, `skill ${name} parent slug`);
    return {
      type: 'skill',
      id: slug,
      slug,
      name,
      description: description.value,
      category,
      allowedTools,
      compatibleWith,
      version: requireString(skill.version, `skill ${name} version`),
      parentPlugin: {
        name: requireString(parent.name, `skill ${name} parent name`),
        ...(parentSlug && { slug: parentSlug }),
        category,
      },
      searchText:
        `${name} ${description.text} ${category} ${allowedTools.join(' ')} ${compatibleWith.join(' ')}`.toLowerCase(),
    };
  });

  for (const key of ['totalAgents', 'totalHooks', 'pluginsWithAgents', 'pluginsWithHooks']) {
    if (!Number.isInteger(stats[key]) || stats[key] < 0) {
      throw new Error(`agent and hook stats ${key} must be a non-negative integer`);
    }
  }

  const officialPlugins = plugins.filter((plugin) => plugin.authorType === 'official');
  const communityPlugins = plugins.filter((plugin) => plugin.authorType === 'community');
  return normalizeDeadDomainValue({
    meta: {
      version: '1.0.0',
      source:
        'catalog.json + skills-catalog.json + marketplace.extended.json + plugin surfaces + docs',
      generator: 'marketplace/scripts/generate-unified-search.mjs',
    },
    stats: {
      totalPlugins: plugins.length,
      totalSkills: skills.length,
      totalDocs: docs.length,
      totalItems: plugins.length + skills.length + docs.length,
      categories: [...new Set([...plugins, ...skills].map((item) => item.category))].sort(
        compareOrdinal,
      ),
      skillTools: stringArray(
        skillsCatalog.allowedToolsUsed,
        'skills catalog allowedToolsUsed',
        [],
        {
          allowEmpty: true,
        },
      ),
      allKeywords: [...new Set(plugins.flatMap((plugin) => plugin.keywords))].sort(compareOrdinal),
      totalAgents: stats.totalAgents,
      totalHooks: stats.totalHooks,
      pluginsWithAgents: stats.pluginsWithAgents,
      pluginsWithHooks: stats.pluginsWithHooks,
      officialPlugins: officialPlugins.length,
      communityPlugins: communityPlugins.length,
      communityContributors: new Set(
        communityPlugins.map((plugin) => plugin.author?.name || 'Unknown'),
      ).size,
    },
    items: [...plugins, ...skills, ...docs],
  });
}

export function renderUnifiedSearchBytes({ root = DEFAULT_ROOT } = {}) {
  const index = renderUnifiedSearch({
    catalogData: readJson(root, CATALOG_PATH, 'catalog'),
    skillsData: readJson(root, SKILLS_PATH, 'skills catalog'),
    extendedData: readJson(root, EXTENDED_PATH, 'extended catalog'),
    docs: readDocs(root),
    agentHookStats: countAgentsAndHooks(root),
  });
  return `${JSON.stringify(index, null, 2)}\n`;
}

export function syncUnifiedSearch({ root = DEFAULT_ROOT, check = false } = {}) {
  const contents = renderUnifiedSearchBytes({ root });
  if (check) {
    assertGeneratedContentCurrent([{ path: OUTPUT_PATH, contents }], { root });
    return JSON.parse(contents);
  }

  const temporary = join(root, `${OUTPUT_PATH}.tmp-${process.pid}`);
  try {
    writeFileSync(
      temporary /* staging file for marketplace/src/data/unified-search-index.json */,
      contents,
      { flag: 'wx' },
    );
    renameSync(temporary, join(root, OUTPUT_PATH));
  } finally {
    rmSync(temporary, { force: true });
  }
  return JSON.parse(contents);
}

function main() {
  const args = process.argv.slice(2);
  if (args.some((arg) => arg !== '--check') || args.filter((arg) => arg === '--check').length > 1) {
    throw new Error(`unknown arguments: ${args.join(' ')}`);
  }
  const check = args.includes('--check');
  const index = syncUnifiedSearch({ check });
  const verb = check ? 'checked' : 'generated';
  console.log(
    `unified-search-index: ${verb} ${index.stats.totalPlugins} plugins, ${index.stats.totalSkills} skills, ${index.stats.totalDocs} docs, ${index.stats.totalItems} total`,
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main();
  } catch (error) {
    console.error(`unified-search-index: ${error.message}`);
    process.exitCode = 1;
  }
}
