#!/usr/bin/env node

/**
 * Generate Unified Search Index
 * Combines plugins and skills into a single searchable index for /explore page
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT_DIR = path.resolve(__dirname, '..');
const DATA_DIR = path.join(ROOT_DIR, 'src/data');
const CATALOG_FILE = path.join(DATA_DIR, 'catalog.json');
const SKILLS_FILE = path.join(DATA_DIR, 'skills-catalog.json');
const OUTPUT_FILE = path.join(DATA_DIR, 'unified-search-index.json');

console.log('🔍 Generating unified search index...\n');

// Read source files
const catalogData = JSON.parse(fs.readFileSync(CATALOG_FILE, 'utf8'));
const skillsData = JSON.parse(fs.readFileSync(SKILLS_FILE, 'utf8'));

// Transform plugins for search
const plugins = catalogData.plugins.map(plugin => ({
  type: 'plugin',
  id: plugin.slug,
  slug: plugin.slug,
  name: plugin.name,  // FULL plugin name (e.g., "004-jeremy-google-cloud-agent-sdk")
  displayName: plugin.displayName || plugin.name,  // Display name for UI
  description: plugin.description,
  category: plugin.category,
  tags: plugin.tags || [],
  author: plugin.author,
  version: plugin.version,
  // Trust signals
  isFeatured: plugin.isFeatured || false,
  isNew: plugin.isNew || false,
  badges: plugin.badges || [],
  skillCount: plugin.skillCount || 0,
  // Search-specific fields
  searchText: `${plugin.displayName || plugin.name} ${plugin.description} ${plugin.category} ${(plugin.tags || []).join(' ')}`.toLowerCase()
}));

// Transform skills for search
const skills = skillsData.skills.map(skill => ({
  type: 'skill',
  id: skill.slug,
  slug: skill.slug,
  name: skill.name,
  description: skill.description || '',
  category: skill.parentPlugin.category,
  allowedTools: skill.allowedTools || [],
  version: skill.version,
  // Link to parent plugin
  parentPlugin: {
    name: skill.parentPlugin.name,
    slug: skill.parentPlugin.slug,
    category: skill.parentPlugin.category
  },
  // Search-specific fields
  searchText: `${skill.name} ${skill.description || ''} ${skill.parentPlugin.category} ${(skill.allowedTools || []).join(' ')}`.toLowerCase()
}));

// Combine into unified index
const unifiedIndex = {
  meta: {
    version: '1.0.0',
    generated: new Date().toISOString(),
    generator: 'scripts/generate-unified-search.mjs'
  },
  stats: {
    totalPlugins: plugins.length,
    totalSkills: skills.length,
    totalItems: plugins.length + skills.length,
    categories: [...new Set([...plugins.map(p => p.category), ...skills.map(s => s.category)])].sort(),
    skillTools: skillsData.allowedToolsUsed || []
  },
  items: [...plugins, ...skills]
};

// Write unified index
fs.writeFileSync(OUTPUT_FILE, JSON.stringify(unifiedIndex, null, 2));

console.log('✅ Unified search index generated!\n');
console.log(`📊 Statistics:`);
console.log(`   Plugins: ${plugins.length}`);
console.log(`   Skills: ${skills.length}`);
console.log(`   Total searchable items: ${unifiedIndex.stats.totalItems}`);
console.log(`   Categories: ${unifiedIndex.stats.categories.length}`);
console.log(`   Skill tools: ${unifiedIndex.stats.skillTools.length}\n`);
console.log(`📝 Output: ${OUTPUT_FILE}\n`);
