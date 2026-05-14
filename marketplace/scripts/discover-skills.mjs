#!/usr/bin/env node

/**
 * Skills Discovery Script
 *
 * Scans the plugins directory for all SKILL.md files, parses their frontmatter,
 * and generates a comprehensive skills catalog for the Astro marketplace.
 */

import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from 'fs';
import { join, dirname, relative } from 'path';
import { fileURLToPath } from 'url';
import { mdToHtml } from './md-to-html.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT_DIR = join(__dirname, '..', '..');
const PLUGINS_DIR = join(ROOT_DIR, 'plugins');
const OUTPUT_FILE = join(ROOT_DIR, 'marketplace', 'src', 'data', 'skills-catalog.json');
const INDEX_FILE = join(ROOT_DIR, 'marketplace', 'src', 'data', 'skills-index.json');
const MARKETPLACE_CATALOG = join(ROOT_DIR, '.claude-plugin', 'marketplace.extended.json');

// ── Progressive disclosure level ─────────────────────────────────────────
// L0 (metadata): name + description + parent + version + slug; no body HTML.
//   Emitted to skills-index.json — fast load for catalog browsing / trigger
//   matching. Whole index is ~3-10 KB gzipped at our scale.
// L1 (full): full catalog including body HTML. Emitted to skills-catalog.json.
//   Default mode for backward compat with marketplace UI build.
// L2 (file): runtime-only — single reference file read by client on demand.
//   Not a build-time concern; CLI errors with guidance.
const LEVELS = new Set(['metadata', 'full', 'file']);
let LEVEL = 'full';
for (const arg of process.argv.slice(2)) {
  const m = arg.match(/^--level=(.+)$/);
  if (m) LEVEL = m[1];
}
if (!LEVELS.has(LEVEL)) {
  console.error(`❌ Unknown --level=${LEVEL}. Expected: metadata | full | file`);
  process.exit(2);
}
if (LEVEL === 'file') {
  console.error('❌ --level=file is a runtime concern (client-side reference-file read).');
  console.error('   Build step emits L0 (skills-index.json) + L1 (skills-catalog.json).');
  console.error('   For a single reference file, read it directly from the plugin path.');
  process.exit(2);
}

/**
 * Parse YAML frontmatter from markdown content
 */
function parseFrontmatter(content) {
  const frontmatterRegex = /^---\n([\s\S]*?)\n---/;
  const match = content.match(frontmatterRegex);

  if (!match) {
    return null;
  }

  const frontmatterText = match[1];
  const metadata = {};

  // Simple YAML parser for our known structure
  const lines = frontmatterText.split('\n');
  let currentKey = null;
  let currentValue = '';
  let inMultiline = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (!trimmed) continue;

    // Handle list items (allowed-tools)
    if (trimmed.startsWith('-')) {
      if (currentKey === 'allowed-tools') {
        if (!Array.isArray(metadata[currentKey])) {
          metadata[currentKey] = [];
        }
        metadata[currentKey].push(trimmed.substring(1).trim());
      }
      continue;
    }

    // Handle key: value pairs
    const colonIndex = trimmed.indexOf(':');
    if (colonIndex > 0 && !inMultiline) {
      if (currentKey && currentValue) {
        metadata[currentKey] = currentValue.trim();
      }

      currentKey = trimmed.substring(0, colonIndex).trim();
      const value = trimmed.substring(colonIndex + 1).trim();

      if (value === '|') {
        // Start of multiline value
        inMultiline = true;
        currentValue = '';
      } else if (value) {
        currentValue = value;
      } else {
        currentValue = '';
      }
    } else if (inMultiline) {
      // Check if this line is a new top-level key (not indented, has colon)
      // YAML block scalars end when a line appears at the original indentation level
      const isIndented = line.startsWith(' ') || line.startsWith('\t');
      if (!isIndented && colonIndex > 0) {
        // End multiline, save current value, process as new key
        if (currentKey && currentValue) {
          metadata[currentKey] = currentValue.trim();
        }
        inMultiline = false;
        currentKey = trimmed.substring(0, colonIndex).trim();
        const value = trimmed.substring(colonIndex + 1).trim();
        if (value === '|') {
          inMultiline = true;
          currentValue = '';
        } else if (value) {
          currentValue = value;
        } else {
          currentValue = '';
        }
      } else if (trimmed.startsWith('-')) {
        // End of multiline, start of list
        if (currentKey && currentValue) {
          metadata[currentKey] = currentValue.trim();
        }
        inMultiline = false;
        currentKey = 'allowed-tools';
        metadata[currentKey] = [trimmed.substring(1).trim()];
      } else {
        // Append to multiline value
        currentValue += (currentValue ? ' ' : '') + trimmed;
      }
    }
  }

  // Save last key-value pair
  if (currentKey && currentValue && !Array.isArray(metadata[currentKey])) {
    metadata[currentKey] = currentValue.trim();
  }

  return metadata;
}

/**
 * Generate URL-safe slug from skill name
 */
function generateSlug(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

/**
 * Extract category from plugin path
 */
function extractCategory(pluginPath) {
  const parts = pluginPath.split('/');
  const pluginsIndex = parts.indexOf('plugins');
  if (pluginsIndex >= 0 && parts.length > pluginsIndex + 1) {
    return parts[pluginsIndex + 1];
  }
  return 'unknown';
}

/**
 * Extract plugin name from path
 */
function extractPluginName(pluginPath) {
  const parts = pluginPath.split('/');
  return parts[parts.length - 1] || 'unknown';
}

/**
 * Get plugin metadata from plugin.json
 */
function getPluginMetadata(pluginDir) {
  const pluginJsonPath = join(pluginDir, '.claude-plugin', 'plugin.json');

  if (existsSync(pluginJsonPath)) {
    try {
      const pluginJson = JSON.parse(readFileSync(pluginJsonPath, 'utf-8'));
      return {
        name: pluginJson.name || extractPluginName(pluginDir),
        version: pluginJson.version,
        description: pluginJson.description,
        author: pluginJson.author
      };
    } catch (error) {
      console.warn(`Failed to parse plugin.json at ${pluginJsonPath}: ${error.message}`);
    }
  }

  return {
    name: extractPluginName(pluginDir),
    version: 'unknown',
    description: '',
    author: ''
  };
}

/**
 * Recursively find all SKILL.md files
 */
function findSkillFiles(dir, skillFiles = []) {
  const entries = readdirSync(dir);

  for (const entry of entries) {
    const fullPath = join(dir, entry);
    const stat = statSync(fullPath);

    if (stat.isDirectory()) {
      // Skip node_modules and hidden directories
      if (entry === 'node_modules' || entry.startsWith('.')) {
        continue;
      }
      findSkillFiles(fullPath, skillFiles);
    } else if (entry === 'SKILL.md') {
      skillFiles.push(fullPath);
    }
  }

  return skillFiles;
}

/**
 * Project a full skill record down to its L0 metadata view.
 * Fields chosen for trigger-match / catalog browse — no body, no HTML.
 */
function projectL0(skill) {
  return {
    slug: skill.slug,
    name: skill.name,
    description: skill.description,
    version: skill.version,
    category: skill.parentPlugin.category,
    parentPlugin: skill.parentPlugin.name,
  };
}

/**
 * Process a single SKILL.md file
 *
 * @param {string} filePath
 * @param {{ metadataOnly?: boolean }} [opts]
 *   metadataOnly skips the mdToHtml body conversion — significant speedup
 *   on metadata-only builds.
 */
function processSkillFile(filePath, opts = {}) {
  const metadataOnly = opts.metadataOnly === true;
  try {
    const content = readFileSync(filePath, 'utf-8');
    const frontmatter = parseFrontmatter(content);

    if (!frontmatter) {
      console.warn(`No valid frontmatter found in ${filePath}`);
      return null;
    }

    // Extract markdown content (everything after frontmatter).
    // Skipped entirely in metadataOnly mode — mdToHtml is the slow step.
    const contentMatch = metadataOnly
      ? null
      : content.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
    const markdownContent = contentMatch ? contentMatch[1].trim() : '';

    // Find parent plugin directory (go up until we find .claude-plugin)
    let currentDir = dirname(filePath);
    let pluginDir = null;

    for (let i = 0; i < 10; i++) { // Max 10 levels up
      if (existsSync(join(currentDir, '.claude-plugin', 'plugin.json'))) {
        pluginDir = currentDir;
        break;
      }
      currentDir = dirname(currentDir);
    }

    // If no .claude-plugin found, use the directory structure to infer plugin dir
    // Skills are typically in plugins/category/plugin-name/skills/skill-name/SKILL.md
    if (!pluginDir) {
      const parts = filePath.split('/');
      const skillsIndex = parts.findIndex(p => p === 'skills');
      if (skillsIndex >= 2) {
        // Go up to plugin-name level (2 levels before 'skills')
        pluginDir = parts.slice(0, skillsIndex).join('/');
      }
    }

    if (!pluginDir) {
      console.warn(`Could not find parent plugin directory for ${filePath}`);
      return null;
    }

    const category = extractCategory(pluginDir);
    const pluginMetadata = getPluginMetadata(pluginDir);
    const relativePath = relative(ROOT_DIR, filePath);

    // Generate slug from name
    const slug = generateSlug(frontmatter.name || 'unnamed-skill');

    // Ensure allowedTools is always an array
    let allowedTools = frontmatter['allowed-tools'] || [];
    if (typeof allowedTools === 'string') {
      allowedTools = allowedTools.split(',').map(t => t.trim());
    }
    if (!Array.isArray(allowedTools)) {
      allowedTools = [];
    }

    // Normalize author to string
    let authorStr = frontmatter.author || pluginMetadata.author || '';
    if (typeof authorStr === 'object' && authorStr.name) {
      authorStr = authorStr.email
        ? `${authorStr.name} <${authorStr.email}>`
        : authorStr.name;
    }

    // Parse compatible-with field
    let compatibleWith = frontmatter['compatible-with'] || [];
    if (typeof compatibleWith === 'string') {
      compatibleWith = compatibleWith.split(',').map(p => p.trim().toLowerCase());
    }
    if (!Array.isArray(compatibleWith)) {
      compatibleWith = [];
    }

    return {
      slug,
      name: frontmatter.name || 'Unnamed Skill',
      description: frontmatter.description || '',
      allowedTools,
      compatibleWith,
      version: frontmatter.version || '1.0.0',
      author: authorStr,
      license: frontmatter.license || 'MIT',
      content: metadataOnly ? '' : mdToHtml(markdownContent),
      parentPlugin: {
        name: pluginMetadata.name,
        category: category,
        path: relative(ROOT_DIR, pluginDir),
        version: pluginMetadata.version,
        description: pluginMetadata.description
      },
      filePath: relativePath
    };
  } catch (error) {
    console.error(`Error processing ${filePath}: ${error.message}`);
    return null;
  }
}

/**
 * Main execution
 */
function main() {
  const metadataOnly = LEVEL === 'metadata';
  console.log('🔍 Discovering skills across plugin marketplace...\n');
  console.log(`Plugins directory: ${PLUGINS_DIR}`);
  console.log(`Level:             ${LEVEL}${metadataOnly ? ' (L0 index only — no body HTML)' : ' (L0 index + L1 catalog)'}`);
  console.log(`Index output:      ${INDEX_FILE}`);
  if (!metadataOnly) console.log(`Catalog output:    ${OUTPUT_FILE}`);
  console.log('');

  // Load marketplace catalog to get valid plugin names
  let marketplacePluginNames = new Set();
  try {
    const marketplaceCatalog = JSON.parse(readFileSync(MARKETPLACE_CATALOG, 'utf-8'));
    marketplacePluginNames = new Set(marketplaceCatalog.plugins.map(p => p.name));
    console.log(`📦 Loaded marketplace catalog: ${marketplacePluginNames.size} plugins\n`);
  } catch (error) {
    console.warn(`⚠️  Could not load marketplace catalog: ${error.message}`);
    console.warn(`    Proceeding without marketplace filtering...\n`);
  }

  // Find all SKILL.md files
  const skillFiles = findSkillFiles(PLUGINS_DIR);
  console.log(`Found ${skillFiles.length} SKILL.md files\n`);

  // Process each skill file
  const skills = [];
  const orphanedSkills = [];
  let successCount = 0;
  let failCount = 0;

  for (const filePath of skillFiles) {
    const skill = processSkillFile(filePath, { metadataOnly });
    if (skill) {
      // Only include skills whose parent plugin is in the marketplace
      if (marketplacePluginNames.size === 0 || marketplacePluginNames.has(skill.parentPlugin.name)) {
        skills.push(skill);
        successCount++;
      } else {
        orphanedSkills.push({
          skill: skill.name,
          parentPlugin: skill.parentPlugin.name,
          filePath: skill.filePath
        });
      }
    } else {
      failCount++;
    }
  }

  console.log(`✅ Successfully processed: ${successCount}`);
  console.log(`❌ Failed to process: ${failCount}`);
  if (orphanedSkills.length > 0) {
    console.log(`⚠️  Orphaned skills (parent not in marketplace): ${orphanedSkills.length}`);
    orphanedSkills.forEach(({ skill, parentPlugin, filePath }) => {
      console.log(`    • ${skill} (parent: ${parentPlugin})`);
      console.log(`      ${filePath}`);
    });
  }
  console.log('');

  // Sort skills by name
  skills.sort((a, b) => a.name.localeCompare(b.name));

  // Check for duplicate slugs
  const slugCounts = {};
  for (const skill of skills) {
    slugCounts[skill.slug] = (slugCounts[skill.slug] || 0) + 1;
  }

  const duplicateSlugs = Object.entries(slugCounts)
    .filter(([_, count]) => count > 1)
    .map(([slug, _]) => slug);

  if (duplicateSlugs.length > 0) {
    console.warn(`⚠️  Found ${duplicateSlugs.length} duplicate slugs:`);
    duplicateSlugs.forEach(slug => {
      const dupes = skills.filter(s => s.slug === slug);
      console.warn(`  - ${slug} (${dupes.length} occurrences)`);
      // Add unique suffix to duplicates
      dupes.forEach((skill, index) => {
        if (index > 0) {
          skill.slug = `${skill.slug}-${index + 1}`;
        }
      });
    });
    console.log('');
  }

  const generatedAt = new Date().toISOString();
  const categories = [...new Set(skills.map(s => s.parentPlugin.category))].sort();

  // L0 index — always emitted. ~150 bytes per skill, ~3-10 KB gzipped at our
  // scale. Schema v3.4.0 contract: clients load this first for trigger match
  // / catalog browse, then fetch L1 (skills-catalog.json) only on demand.
  const index = {
    schemaVersion: '3.4.0',
    level: 'metadata',
    skills: skills.map(projectL0),
    count: skills.length,
    generatedAt,
    categories,
  };
  writeFileSync(INDEX_FILE, JSON.stringify(index, null, 2));
  console.log(`✅ L0 index generated:   ${INDEX_FILE}  (${skills.length} skills)`);

  // L1 catalog — only emitted at level=full. Heavy artifact with body HTML.
  if (!metadataOnly) {
    const catalog = {
      schemaVersion: '3.4.0',
      level: 'full',
      skills,
      count: skills.length,
      generatedAt,
      categories,
      allowedToolsUsed: [...new Set(skills.flatMap(s => s.allowedTools))].sort()
    };
    writeFileSync(OUTPUT_FILE, JSON.stringify(catalog, null, 2));
    console.log(`✅ L1 catalog generated: ${OUTPUT_FILE}  (${skills.length} skills with body HTML)`);
  } else {
    console.log(`ℹ️  L1 catalog skipped (level=metadata — re-run without --level to emit it).`);
  }

  console.log('');
  console.log('📊 Skills Summary:');
  console.log(`   Total skills: ${skills.length}`);
  console.log(`   Categories: ${categories.length}`);
  if (!metadataOnly) {
    const allowedToolsUsed = [...new Set(skills.flatMap(s => s.allowedTools))];
    console.log(`   Unique tools: ${allowedToolsUsed.length}`);
  }

  // Show sample
  console.log('\n📝 First 3 skills:');
  skills.slice(0, 3).forEach((skill, i) => {
    console.log(`\n${i + 1}. ${skill.name}`);
    console.log(`   Slug: ${skill.slug}`);
    console.log(`   Category: ${skill.parentPlugin.category}`);
    console.log(`   Plugin: ${skill.parentPlugin.name}`);
    if (!metadataOnly) console.log(`   Tools: ${skill.allowedTools.join(', ')}`);
  });

  process.exit(0);
}

main();
