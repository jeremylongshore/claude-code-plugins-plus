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

// ── Markdown-to-HTML converter (tables, code blocks, lists, headings) ──

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function inlineFormat(text) {
  return text
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/__([^_]+)__/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/_([^_]+)_/g, '<em>$1</em>');
}

function mdToHtml(md) {
  const lines = md.split('\n');
  const out = [];
  let inCodeBlock = false;
  let inList = false;
  let listType = null;
  let inTable = false;
  let tableHeaderDone = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Fenced code blocks
    if (line.trimStart().startsWith('```')) {
      if (inCodeBlock) {
        out.push('</code></pre>');
        inCodeBlock = false;
      } else {
        if (inList) { out.push(`</${listType}>`); inList = false; listType = null; }
        if (inTable) { out.push('</tbody></table>'); inTable = false; tableHeaderDone = false; }
        const lang = line.trim().slice(3).trim();
        out.push(`<pre${lang ? ` data-lang="${escapeHtml(lang)}"` : ''}><code>`);
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      out.push(escapeHtml(line));
      continue;
    }

    const trimmed = line.trim();

    // Table rows (detect by pipe characters)
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      const cells = trimmed.slice(1, -1).split('|').map(c => c.trim());

      // Separator row (|---|---|)
      if (cells.every(c => /^[-:]+$/.test(c))) {
        tableHeaderDone = true;
        continue;
      }

      if (!inTable) {
        if (inList) { out.push(`</${listType}>`); inList = false; listType = null; }
        out.push('<table><thead><tr>');
        cells.forEach(c => out.push(`<th>${inlineFormat(c)}</th>`));
        out.push('</tr></thead><tbody>');
        inTable = true;
        tableHeaderDone = false;
        continue;
      }

      out.push('<tr>');
      cells.forEach(c => out.push(`<td>${inlineFormat(c)}</td>`));
      out.push('</tr>');
      continue;
    }

    // Close table if we hit a non-table line
    if (inTable) {
      out.push('</tbody></table>');
      inTable = false;
      tableHeaderDone = false;
    }

    // Empty line
    if (!trimmed) {
      if (inList) { out.push(`</${listType}>`); inList = false; listType = null; }
      continue;
    }

    // Headings (h1-h6)
    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      if (inList) { out.push(`</${listType}>`); inList = false; listType = null; }
      const level = headingMatch[1].length;
      out.push(`<h${level}>${inlineFormat(headingMatch[2])}</h${level}>`);
      continue;
    }

    // Horizontal rule
    if (/^[-*_]{3,}$/.test(trimmed)) {
      if (inList) { out.push(`</${listType}>`); inList = false; listType = null; }
      out.push('<hr>');
      continue;
    }

    // Unordered list
    if (/^[-*+]\s/.test(trimmed)) {
      if (!inList || listType !== 'ul') {
        if (inList) out.push(`</${listType}>`);
        out.push('<ul>');
        inList = true;
        listType = 'ul';
      }
      out.push(`<li>${inlineFormat(trimmed.replace(/^[-*+]\s+/, ''))}</li>`);
      continue;
    }

    // Ordered list
    if (/^\d+[.)]\s/.test(trimmed)) {
      if (!inList || listType !== 'ol') {
        if (inList) out.push(`</${listType}>`);
        out.push('<ol>');
        inList = true;
        listType = 'ol';
      }
      out.push(`<li>${inlineFormat(trimmed.replace(/^\d+[.)]\s+/, ''))}</li>`);
      continue;
    }

    // Paragraph
    if (inList) { out.push(`</${listType}>`); inList = false; listType = null; }
    out.push(`<p>${inlineFormat(trimmed)}</p>`);
  }

  if (inList) out.push(`</${listType}>`);
  if (inCodeBlock) out.push('</code></pre>');
  if (inTable) out.push('</tbody></table>');

  return out.join('\n');
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
      content: mdToHtml(markdownContent),
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
