#!/usr/bin/env node
/**
 * Canonical Metrics Summary
 *
 * Single source of truth for all marketplace metrics.
 * All documentation should reference output from this script.
 *
 * Usage:
 *   node scripts/metrics-summary.js          # Human-readable output
 *   node scripts/metrics-summary.js --json   # JSON output for scripts
 *   node scripts/metrics-summary.js --md     # Markdown snippet for docs
 */

import { readFileSync, readdirSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = join(__dirname, '..');

// Canonical source: unified-search-index.json (generated at build time)
const SEARCH_INDEX_PATH = join(ROOT, 'marketplace/src/data/unified-search-index.json');
const MARKETPLACE_JSON_PATH = join(ROOT, '.claude-plugin/marketplace.json');
const PLUGINS_DIR = join(ROOT, 'plugins');

function getSearchIndexMetrics() {
  try {
    const data = JSON.parse(readFileSync(SEARCH_INDEX_PATH, 'utf-8'));
    return {
      source: 'unified-search-index.json',
      totalPlugins: data.stats.totalPlugins,
      totalSkills: data.stats.totalSkills,
      totalItems: data.stats.totalItems,
      categories: data.stats.categories,
      categoryCount: data.stats.categories.length,
      skillToolsCount: data.stats.skillTools?.length || 0,
    };
  } catch (e) {
    return { error: `Failed to read search index: ${e.message}` };
  }
}

function getMarketplaceJsonMetrics() {
  try {
    const data = JSON.parse(readFileSync(MARKETPLACE_JSON_PATH, 'utf-8'));
    return {
      source: 'marketplace.json',
      catalogPlugins: data.plugins.length,
    };
  } catch (e) {
    return { error: `Failed to read marketplace.json: ${e.message}` };
  }
}

function countFilesystem() {
  let pluginDirs = 0;
  let skillFiles = 0;
  const categoryDirs = new Set();

  function walk(dir, depth = 0) {
    try {
      const entries = readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = join(dir, entry.name);
        if (entry.isDirectory()) {
          if (entry.name === '.claude-plugin') {
            pluginDirs++;
          } else if (depth === 0) {
            categoryDirs.add(entry.name);
          }
          if (entry.name !== 'node_modules' && entry.name !== '.git') {
            walk(fullPath, depth + 1);
          }
        } else if (entry.name === 'SKILL.md') {
          skillFiles++;
        }
      }
    } catch (e) {
      // Skip inaccessible directories
    }
  }

  walk(PLUGINS_DIR);
  return {
    source: 'filesystem',
    pluginDirectories: pluginDirs,
    skillFiles: skillFiles,
    categoryDirectories: categoryDirs.size,
  };
}

function main() {
  const args = process.argv.slice(2);
  const jsonOutput = args.includes('--json');
  const mdOutput = args.includes('--md');

  const searchIndex = getSearchIndexMetrics();
  const marketplace = getMarketplaceJsonMetrics();
  const filesystem = countFilesystem();

  const metrics = {
    timestamp: new Date().toISOString(),
    canonical: {
      description: 'Use these values in documentation (from unified-search-index.json)',
      totalPlugins: searchIndex.totalPlugins,
      totalSkills: searchIndex.totalSkills,
      totalCategories: searchIndex.categoryCount,
      totalSearchItems: searchIndex.totalItems,
    },
    sources: {
      searchIndex,
      marketplace,
      filesystem,
    },
    discrepancies: {
      pluginsDiff: filesystem.pluginDirectories - searchIndex.totalPlugins,
      skillsDiff: filesystem.skillFiles - searchIndex.totalSkills,
      catalogVsIndex: marketplace.catalogPlugins - searchIndex.totalPlugins,
      notes: [
        `${filesystem.pluginDirectories - marketplace.catalogPlugins} plugins on disk not in catalog`,
        `${filesystem.skillFiles - searchIndex.totalSkills} SKILL.md files not indexed (orphaned)`,
      ],
    },
  };

  if (jsonOutput) {
    console.log(JSON.stringify(metrics, null, 2));
  } else if (mdOutput) {
    console.log(`## Marketplace Metrics (${new Date().toLocaleDateString()})\n`);
    console.log(`| Metric | Count | Source |`);
    console.log(`|--------|-------|--------|`);
    console.log(`| Plugins | ${metrics.canonical.totalPlugins} | search index |`);
    console.log(`| Skills | ${metrics.canonical.totalSkills} | search index |`);
    console.log(`| Categories | ${metrics.canonical.totalCategories} | search index |`);
    console.log(`| Search Items | ${metrics.canonical.totalSearchItems} | search index |`);
    console.log(`\n**Definitions:**`);
    console.log(`- **Plugins**: Entries in unified-search-index.json (excludes orphaned/unlisted)`);
    console.log(`- **Skills**: Agent Skills indexed for search (excludes orphaned)`);
    console.log(`- **Categories**: Unique category values in search index`);
  } else {
    console.log('='.repeat(60));
    console.log('CANONICAL MARKETPLACE METRICS');
    console.log('Generated:', metrics.timestamp);
    console.log('='.repeat(60));
    console.log('\n📊 USE THESE VALUES IN DOCUMENTATION:\n');
    console.log(`  Plugins:     ${metrics.canonical.totalPlugins}`);
    console.log(`  Skills:      ${metrics.canonical.totalSkills}`);
    console.log(`  Categories:  ${metrics.canonical.totalCategories}`);
    console.log(`  Search Items: ${metrics.canonical.totalSearchItems}`);
    console.log('\n📁 SOURCE BREAKDOWN:\n');
    console.log(`  Search Index (canonical):`);
    console.log(`    - Plugins: ${searchIndex.totalPlugins}`);
    console.log(`    - Skills: ${searchIndex.totalSkills}`);
    console.log(`    - Categories: ${searchIndex.categoryCount}`);
    console.log(`\n  Marketplace Catalog:`);
    console.log(`    - Catalog Entries: ${marketplace.catalogPlugins}`);
    console.log(`\n  Filesystem:`);
    console.log(`    - Plugin Dirs: ${filesystem.pluginDirectories}`);
    console.log(`    - SKILL.md Files: ${filesystem.skillFiles}`);
    console.log(`    - Category Dirs: ${filesystem.categoryDirectories}`);
    console.log('\n⚠️  DISCREPANCIES:\n');
    metrics.discrepancies.notes.forEach(note => console.log(`  - ${note}`));
    console.log('\n' + '='.repeat(60));
  }
}

main();
