#!/usr/bin/env node

/**
 * Sync marketplace/src/data/catalog.json to match .claude-plugin/marketplace.extended.json.
 *
 * Goal: avoid broken /explore links by ensuring the plugin set in catalog.json matches
 * the actual plugin pages generated from marketplace.extended.json.
 *
 * Strategy:
 * - Keep existing catalog entries (preserves badges/flags) when names match.
 * - Drop entries not present in marketplace.extended.json.
 * - Add missing entries with sensible defaults.
 * - Deduplicate by plugin name deterministically.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_ROOT = path.join(__dirname, '..', '..');
const EXTENDED_PATH = path.join(REPO_ROOT, '.claude-plugin', 'marketplace.extended.json');
const CATALOG_PATH = path.join(REPO_ROOT, 'marketplace', 'src', 'data', 'catalog.json');

function slugFromName(name) {
  const numberedJeremy = name.match(/^\d{3}-jeremy-(.+)$/);
  if (numberedJeremy) return numberedJeremy[1];
  const numbered = name.match(/^\d{3}-(.+)$/);
  if (numbered) return numbered[1];
  return name;
}

function displayNameFromSlug(slug) {
  return slug.replace(/-/g, ' ').toLowerCase();
}

function scoreCatalogEntry(entry) {
  const hasEmail = entry?.author?.email ? 1 : 0;
  const hasSkills = entry?.hasSkills ? 1 : 0;
  const skillCount = Number(entry?.skillCount || 0);
  const commandCount = Number(entry?.commandCount || 0);
  const keywordCount = Array.isArray(entry?.keywords) ? entry.keywords.length : 0;
  const descriptionLength = typeof entry?.description === 'string' ? entry.description.length : 0;

  return (
    hasEmail * 10_000 +
    hasSkills * 5_000 +
    skillCount * 1_000 +
    commandCount * 500 +
    keywordCount * 10 +
    descriptionLength
  );
}

function buildDefaultCatalogEntry(plugin, now) {
  const name = plugin?.name || 'unknown';
  const slug = slugFromName(name);
  const category = plugin?.category || 'other';
  const keywords = Array.isArray(plugin?.keywords) ? plugin.keywords : [];
  const author = plugin?.author && typeof plugin.author === 'object' ? plugin.author : { name: 'Claude Code Plugins' };
  const version = plugin?.version || '1.0.0';

  const skillCount = Number(plugin?.components?.skills || 0);
  const commandCount = Number(plugin?.components?.commands || 0);

  return {
    slug,
    name,
    displayName: displayNameFromSlug(slug),
    description: plugin?.description || '',
    version,
    category,
    keywords,
    hasSkills: skillCount > 0,
    skillCount,
    commandCount,
    installCommand: `/plugin install ${name}`,
    sourcePath: plugin?.source || '',
    lastUpdatedEpoch: Math.floor(now.getTime() / 1000),
    lastUpdatedDate: now.toISOString(),
    status: 'active',
    badges: ['new'],
    isFeatured: Boolean(plugin?.featured),
    isNew: true,
    author,
    type: 'instruction-plugin'
  };
}

function main() {
  if (!fs.existsSync(EXTENDED_PATH)) {
    console.error(`❌ Missing marketplace.extended.json at ${EXTENDED_PATH}`);
    process.exit(1);
  }

  const extended = JSON.parse(fs.readFileSync(EXTENDED_PATH, 'utf8'));
  const extendedPlugins = Array.isArray(extended?.plugins) ? extended.plugins : [];
  const extendedNameSet = new Set(extendedPlugins.map(p => p?.name).filter(Boolean));

  const now = new Date();

  let existingCatalog = null;
  if (fs.existsSync(CATALOG_PATH)) {
    existingCatalog = JSON.parse(fs.readFileSync(CATALOG_PATH, 'utf8'));
  }

  const existingPlugins = Array.isArray(existingCatalog?.plugins) ? existingCatalog.plugins : [];

  // Build best existing entry per name (handles duplicates deterministically).
  const bestExistingByName = new Map();
  for (const entry of existingPlugins) {
    if (!entry || typeof entry !== 'object') continue;
    const name = entry.name;
    if (!name || !extendedNameSet.has(name)) continue;

    const prev = bestExistingByName.get(name);
    if (!prev || scoreCatalogEntry(entry) > scoreCatalogEntry(prev)) {
      bestExistingByName.set(name, entry);
    }
  }

  // Preserve existing order where possible, drop unknowns, and dedupe.
  const ordered = [];
  const seen = new Set();
  for (const entry of existingPlugins) {
    const name = entry?.name;
    if (!name || !extendedNameSet.has(name) || seen.has(name)) continue;
    const best = bestExistingByName.get(name) || entry;
    ordered.push(best);
    seen.add(name);
  }

  // Append any plugins missing from catalog (deterministic by name).
  const missingPlugins = extendedPlugins
    .filter(p => p?.name && !seen.has(p.name))
    .sort((a, b) => a.name.localeCompare(b.name));

  for (const plugin of missingPlugins) {
    ordered.push(buildDefaultCatalogEntry(plugin, now));
    seen.add(plugin.name);
  }

  // Recompute stats from final plugin list.
  const byCategory = {};
  const byStatus = {};
  let totalSkills = 0;
  let totalCommands = 0;
  let pluginsWithSkills = 0;
  let featured = 0;
  let newCount = 0;

  for (const plugin of ordered) {
    const category = plugin.category || 'other';
    byCategory[category] = (byCategory[category] || 0) + 1;

    const status = plugin.status || 'unknown';
    byStatus[status] = (byStatus[status] || 0) + 1;

    totalSkills += Number(plugin.skillCount || 0);
    totalCommands += Number(plugin.commandCount || 0);
    if (plugin.hasSkills) pluginsWithSkills += 1;
    if (plugin.isFeatured) featured += 1;
    if (plugin.isNew) newCount += 1;
  }

  const nextCatalog = {
    meta: {
      version: existingCatalog?.meta?.version || '1.0.0',
      generated: now.toISOString(),
      source: 'marketplace.extended.json',
      generator: 'scripts/sync-catalog.mjs'
    },
    stats: {
      totalPlugins: ordered.length,
      totalSkills,
      totalCommands,
      pluginsWithSkills,
      byCategory,
      byStatus,
      featured,
      new: newCount,
      generatedAt: now.toISOString()
    },
    plugins: ordered
  };

  fs.writeFileSync(CATALOG_PATH, JSON.stringify(nextCatalog, null, 2) + '\n');
  const keptNames = new Set(ordered.map(p => p.name).filter(Boolean));
  const removedCount = existingPlugins.filter(p => p?.name && !keptNames.has(p.name)).length;
  console.log(`✅ Synced catalog -> ${CATALOG_PATH}`);
  console.log(`   Plugins: ${ordered.length}`);
  console.log(`   Removed: ${removedCount}`);
  console.log(`   Added: ${missingPlugins.length}`);
}

main();
