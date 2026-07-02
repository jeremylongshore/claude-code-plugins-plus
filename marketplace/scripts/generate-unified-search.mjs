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
const DOCS_DIR = path.join(ROOT_DIR, 'src/content/docs');

console.log('🔍 Generating unified search index...\n');

// Count agents and hooks across all plugins.
//
// We walk the entire plugins/ tree rather than the old fixed depth-3 walk
// (plugins/<cat>/<plugin>/agents). The shipped surface area includes meta-packs
// (devops-automation-pack, ai-ml-engineering-pack, etc.) that nest sub-plugins
// at plugins/<cat>/<pack>/plugins/<sub>/agents — those agents ship to users
// when the pack is installed, so the public-facing count must include them.
// Skipped dirs: node_modules, dist, build, .git (build/dep noise).
function countAgentsAndHooks() {
  const SKIP = new Set(['node_modules', 'dist', 'build', '.git', '.next', '.astro']);
  let totalAgents = 0;
  let totalHooks = 0;
  let pluginsWithAgents = 0;
  let pluginsWithHooks = 0;

  function walk(dir) {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }

    // If this dir contains agents/ or hooks/, count its files. Otherwise recurse.
    const agentsDir = path.join(dir, 'agents');
    if (fs.existsSync(agentsDir) && fs.statSync(agentsDir).isDirectory()) {
      const agentFiles = fs.readdirSync(agentsDir).filter((f) => f.endsWith('.md'));
      if (agentFiles.length > 0) {
        totalAgents += agentFiles.length;
        pluginsWithAgents++;
      }
    }
    const hooksDir = path.join(dir, 'hooks');
    if (fs.existsSync(hooksDir) && fs.statSync(hooksDir).isDirectory()) {
      const hookFiles = fs
        .readdirSync(hooksDir)
        .filter((f) => f.endsWith('.json') || f.endsWith('.sh'));
      if (hookFiles.length > 0) {
        totalHooks += hookFiles.length;
        pluginsWithHooks++;
      }
    }

    // Recurse into subdirectories (skip noise dirs and the agents/hooks dirs
    // we just counted — their contents are flat .md/.json/.sh files, not nested
    // plugin trees).
    for (const ent of entries) {
      if (!ent.isDirectory()) continue;
      if (SKIP.has(ent.name)) continue;
      if (ent.name === 'agents' || ent.name === 'hooks') continue;
      walk(path.join(dir, ent.name));
    }
  }

  walk(PLUGINS_DIR);
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

// Determine if author is official (Intent Solutions / Jeremy Longshore / house accounts)
function getAuthorType(author) {
  if (!author) return 'community';
  const name = (author.name || '').toLowerCase();
  const email = (author.email || '').toLowerCase();
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

// Transform docs for search — walk src/content/docs/**/*.md and index the
// documentation section alongside plugins and skills. URLs mirror the Astro
// content-collection routing in src/pages/docs/[...slug].astro, where the
// entry id is the file path relative to the collection root minus `.md`.
function walkDocFiles(dir) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return [];
  }
  const out = [];
  for (const ent of entries) {
    const full = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      out.push(...walkDocFiles(full));
    } else if (ent.name.endsWith('.md')) {
      out.push(full);
    }
  }
  return out;
}

// Minimal frontmatter parser for the docs schema (title, description,
// section: scalar strings; keywords: block list of strings). Nested object
// lists (officialLinks) are ignored — only scalar and string-list fields
// referenced below are consumed.
function parseDocFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  const fm = {};
  let currentKey = null;
  for (const line of match[1].split('\n')) {
    const kv = line.match(/^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$/);
    if (kv) {
      currentKey = kv[1];
      const value = kv[2].trim();
      if (value === '') {
        fm[currentKey] = []; // block list (or nested structure) follows
      } else {
        fm[currentKey] = value.replace(/^["']|["']$/g, '');
      }
      continue;
    }
    const item = line.match(/^\s*-\s+(.*)$/);
    if (item && currentKey && Array.isArray(fm[currentKey])) {
      const entry = item[1].trim().replace(/^["']|["']$/g, '');
      // Skip object-list entries (e.g. officialLinks `- title: ...`)
      if (!/^[A-Za-z][A-Za-z0-9_-]*:\s/.test(entry)) fm[currentKey].push(entry);
    }
  }
  return fm;
}

const docs = walkDocFiles(DOCS_DIR)
  .map(file => {
    const fm = parseDocFrontmatter(fs.readFileSync(file, 'utf8'));
    if (!fm || !fm.title) {
      console.warn(`   ⚠ Skipping doc without frontmatter title: ${path.relative(ROOT_DIR, file)}`);
      return null;
    }
    const slug = path.relative(DOCS_DIR, file).replace(/\\/g, '/').replace(/\.md$/, '');
    const keywords = Array.isArray(fm.keywords) ? fm.keywords : [];
    return {
      type: 'docs',
      id: `docs/${slug}`,
      slug,
      name: fm.title,
      description: typeof fm.description === 'string' ? fm.description : '',
      category: typeof fm.section === 'string' ? fm.section : 'docs',
      keywords,
      url: `/docs/${slug}/`,
      searchText: `${fm.title} ${fm.description || ''} ${fm.section || ''} ${keywords.join(' ')}`.toLowerCase()
    };
  })
  .filter(Boolean)
  .sort((a, b) => a.slug.localeCompare(b.slug));

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
    totalDocs: docs.length,
    totalItems: plugins.length + skills.length + docs.length,
    // Docs sections are intentionally excluded — this drives the plugin/skill
    // category filter dropdown and the "N categories" marketing copy.
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
  items: [...plugins, ...skills, ...docs]
};

// Write unified index
fs.writeFileSync(OUTPUT_FILE, JSON.stringify(unifiedIndex, null, 2));

console.log('✅ Unified search index generated!\n');
console.log(`📊 Statistics:`);
console.log(`   Plugins: ${plugins.length}`);
console.log(`   Skills: ${skills.length}`);
console.log(`   Docs: ${docs.length}`);
console.log(`   Total searchable items: ${unifiedIndex.stats.totalItems}`);
console.log(`   Categories: ${unifiedIndex.stats.categories.length}`);
console.log(`   Skill tools: ${unifiedIndex.stats.skillTools.length}`);
console.log(`   Agents: ${unifiedIndex.stats.totalAgents} (across ${unifiedIndex.stats.pluginsWithAgents} plugins)`);
console.log(`   Hooks: ${unifiedIndex.stats.totalHooks} (across ${unifiedIndex.stats.pluginsWithHooks} plugins)\n`);
console.log(`📝 Output: ${OUTPUT_FILE}\n`);
