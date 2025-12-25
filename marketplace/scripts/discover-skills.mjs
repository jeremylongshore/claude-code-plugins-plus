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

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT_DIR = join(__dirname, '..', '..');
const PLUGINS_DIR = join(ROOT_DIR, 'plugins');
const OUTPUT_FILE = join(ROOT_DIR, 'marketplace', 'src', 'data', 'skills-catalog.json');
const MARKETPLACE_CATALOG = join(ROOT_DIR, '.claude-plugin', 'marketplace.extended.json');

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
      // Append to multiline value
      if (trimmed && !trimmed.startsWith('-')) {
        currentValue += (currentValue ? ' ' : '') + trimmed;
      } else if (trimmed.startsWith('-')) {
        // End of multiline, start of list
        if (currentKey && currentValue) {
          metadata[currentKey] = currentValue.trim();
        }
        inMultiline = false;
        currentKey = 'allowed-tools';
        metadata[currentKey] = [trimmed.substring(1).trim()];
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
 * Process a single SKILL.md file
 */
function processSkillFile(filePath) {
  try {
    const content = readFileSync(filePath, 'utf-8');
    const frontmatter = parseFrontmatter(content);

    if (!frontmatter) {
      console.warn(`No valid frontmatter found in ${filePath}`);
      return null;
    }

    // Extract markdown content (everything after frontmatter)
    const contentMatch = content.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
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

    return {
      slug,
      name: frontmatter.name || 'Unnamed Skill',
      description: frontmatter.description || '',
      allowedTools,
      version: frontmatter.version || '1.0.0',
      author: authorStr,
      license: frontmatter.license || 'MIT',
      content: markdownContent,
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
  console.log('🔍 Discovering skills across plugin marketplace...\n');
  console.log(`Plugins directory: ${PLUGINS_DIR}`);
  console.log(`Output file: ${OUTPUT_FILE}\n`);

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
    const skill = processSkillFile(filePath);
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

  // Generate catalog
  const catalog = {
    skills,
    count: skills.length,
    generatedAt: new Date().toISOString(),
    categories: [...new Set(skills.map(s => s.parentPlugin.category))].sort(),
    allowedToolsUsed: [...new Set(skills.flatMap(s => s.allowedTools))].sort()
  };

  // Write to file
  writeFileSync(OUTPUT_FILE, JSON.stringify(catalog, null, 2));

  console.log('📊 Skills Catalog Summary:');
  console.log(`   Total skills: ${catalog.count}`);
  console.log(`   Categories: ${catalog.categories.length}`);
  console.log(`   Unique tools: ${catalog.allowedToolsUsed.length}`);
  console.log(`\n✅ Catalog generated: ${OUTPUT_FILE}`);

  // Show sample
  console.log('\n📝 First 3 skills:');
  catalog.skills.slice(0, 3).forEach((skill, i) => {
    console.log(`\n${i + 1}. ${skill.name}`);
    console.log(`   Slug: ${skill.slug}`);
    console.log(`   Category: ${skill.parentPlugin.category}`);
    console.log(`   Plugin: ${skill.parentPlugin.name}`);
    console.log(`   Tools: ${skill.allowedTools.join(', ')}`);
  });

  process.exit(0);
}

main();
