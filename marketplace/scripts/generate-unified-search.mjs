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

const PLUGINS_DIR = path.resolve(ROOT_DIR, '..', 'plugins');
const EXTENDED_CATALOG_FILE = path.resolve(ROOT_DIR, '..', '.claude-plugin', 'marketplace.extended.json');

console.log('🔍 Generating unified search index...\n');

// Count agents and hooks across all plugins
function countAgentsAndHooks() {
  let totalAgents = 0;
  let totalHooks = 0;
  let pluginsWithAgents = 0;
  let pluginsWithHooks = 0;

  const categories = fs.readdirSync(PLUGINS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory());

  for (const cat of categories) {
    const catPath = path.join(PLUGINS_DIR, cat.name);
    const plugins = fs.readdirSync(catPath, { withFileTypes: true })
      .filter(d => d.isDirectory());

    for (const plugin of plugins) {
      const agentsDir = path.join(catPath, plugin.name, 'agents');
      const hooksDir = path.join(catPath, plugin.name, 'hooks');

      if (fs.existsSync(agentsDir)) {
        const agentFiles = fs.readdirSync(agentsDir).filter(f => f.endsWith('.md'));
        if (agentFiles.length > 0) {
          totalAgents += agentFiles.length;
          pluginsWithAgents++;
        }
      }

      if (fs.existsSync(hooksDir)) {
        const hookFiles = fs.readdirSync(hooksDir).filter(f => f.endsWith('.json') || f.endsWith('.sh'));
        if (hookFiles.length > 0) {
          totalHooks += hookFiles.length;
          pluginsWithHooks++;
        }
      }
    }
  }

  return { totalAgents, totalHooks, pluginsWithAgents, pluginsWithHooks };
}

const agentHookStats = countAgentsAndHooks();

// Read source files
const catalogData = JSON.parse(fs.readFileSync(CATALOG_FILE, 'utf8'));
const skillsData = JSON.parse(fs.readFileSync(SKILLS_FILE, 'utf8'));

// Build verification lookup from extended catalog
const verificationMap = new Map();
if (fs.existsSync(EXTENDED_CATALOG_FILE)) {
  const extendedData = JSON.parse(fs.readFileSync(EXTENDED_CATALOG_FILE, 'utf8'));
  for (const plugin of extendedData.plugins || []) {
    if (plugin.verification) {
      verificationMap.set(plugin.name, plugin.verification);
    }
  }
  console.log(`   Verification data loaded for ${verificationMap.size} plugins`);
}

// Determine if author is official (Intent Solutions / Jeremy Longshore)
function getAuthorType(author) {
  if (!author) return 'community';
  const name = (author.name || '').toLowerCase();
  const email = (author.email || '').toLowerCase();
  if (name.includes('jeremy longshore') || email.includes('intentsolutions.io') ||
      name.includes('claude code plugins team')) {
    return 'official';
  }
  return 'community';
}

// Transform plugins for search
const plugins = catalogData.plugins.map(plugin => {
  const verification = verificationMap.get(plugin.name) || null;
  return {
    type: 'plugin',
    id: plugin.slug,
    slug: plugin.slug,
    name: plugin.name,  // FULL plugin name (e.g., "004-jeremy-google-cloud-agent-sdk")
    displayName: plugin.displayName || plugin.name,  // Display name for UI
    description: plugin.description,
    category: plugin.category,
    keywords: plugin.keywords || plugin.tags || [],
    author: plugin.author,
    authorType: getAuthorType(plugin.author),
    version: plugin.version,
    // Trust signals
    isFeatured: plugin.isFeatured || false,
    isNew: plugin.isNew || false,
    badges: plugin.badges || [],
    skillCount: plugin.skillCount || 0,
    // Verification
    ...(verification && {
      verificationScore: verification.score,
      verificationGrade: verification.grade,
      verificationBadge: verification.badge,
    }),
    // Search-specific fields
    searchText: `${plugin.displayName || plugin.name} ${plugin.description} ${plugin.category} ${(plugin.keywords || plugin.tags || []).join(' ')}`.toLowerCase()
  };
});

// Transform skills for search
const skills = skillsData.skills.map(skill => ({
  type: 'skill',
  id: skill.slug,
  slug: skill.slug,
  name: skill.name,
  description: skill.description || '',
  category: skill.parentPlugin.category,
  allowedTools: skill.allowedTools || [],
  compatibleWith: skill.compatibleWith || [],
  version: skill.version,
  // Link to parent plugin
  parentPlugin: {
    name: skill.parentPlugin.name,
    slug: skill.parentPlugin.slug,
    category: skill.parentPlugin.category
  },
  // Search-specific fields
  searchText: `${skill.name} ${skill.description || ''} ${skill.parentPlugin.category} ${(skill.allowedTools || []).join(' ')} ${(skill.compatibleWith || []).join(' ')}`.toLowerCase()
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
    skillTools: skillsData.allowedToolsUsed || [],
    allKeywords: [...new Set(plugins.flatMap(p => p.keywords || []))].sort(),
    totalAgents: agentHookStats.totalAgents,
    totalHooks: agentHookStats.totalHooks,
    pluginsWithAgents: agentHookStats.pluginsWithAgents,
    pluginsWithHooks: agentHookStats.pluginsWithHooks,
    officialPlugins: plugins.filter(p => p.authorType === 'official').length,
    communityPlugins: plugins.filter(p => p.authorType === 'community').length,
    communityContributors: [...new Set(plugins.filter(p => p.authorType === 'community').map(p => p.author?.name || 'Unknown'))].length
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
console.log(`   Skill tools: ${unifiedIndex.stats.skillTools.length}`);
console.log(`   Agents: ${unifiedIndex.stats.totalAgents} (across ${unifiedIndex.stats.pluginsWithAgents} plugins)`);
console.log(`   Hooks: ${unifiedIndex.stats.totalHooks} (across ${unifiedIndex.stats.pluginsWithHooks} plugins)\n`);
console.log(`📝 Output: ${OUTPUT_FILE}\n`);
