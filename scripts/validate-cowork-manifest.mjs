#!/usr/bin/env node
/**
 * validate-cowork-manifest.mjs
 *
 * CI GATE: catalog ↔ manifest ↔ disk alignment for the cowork pipeline.
 *
 * The intended invariant: every non-MCP plugin in marketplace.extended.json
 * has exactly one zip on disk and exactly one manifest entry — and nothing
 * else exists on disk. build-cowork-zips.mjs is responsible for producing
 * that state (it wipes plugins/ + bundles/ before each run); this script
 * is the regression gate that catches drift if either side breaks.
 *
 * Complements the two pre-existing cowork gates:
 *   - marketplace/scripts/validate-cowork-downloads.mjs
 *       Walks manifest → disk to assert every referenced zip is present.
 *       Does NOT detect orphans (disk → manifest direction).
 *   - scripts/validate-cowork-security.mjs
 *       Samples 30 zip contents for sensitive files. Content-level check.
 *
 * This validator owns the topology-level check: catalog drives manifest,
 * manifest drives disk, and disk must contain nothing the manifest does
 * not declare. The catalog is the single source of truth.
 *
 * References:
 *   - CLAUDE.md § "Auto-cowork contract" — the invariant + author workflow
 *   - scripts/build-cowork-zips.mjs — the producer this gate guards
 *   - .claude-plugin/marketplace.extended.json — source of truth (catalog)
 *
 * Exit codes:
 *   0 - aligned
 *   1 - drift detected (catalog/manifest/disk mismatch)
 *
 * Usage:
 *   node scripts/validate-cowork-manifest.mjs
 *
 * CI wiring:
 *   - marketplace/scripts/build.mjs runs this immediately after `cowork:zips`
 *     so a local `npm run build` catches drift before it can land.
 *   - .github/workflows/validate-plugins.yml runs it as a separate named
 *     step after `Validate Cowork Downloads` for a clear CI failure signal.
 */

import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');

const EXTENDED_JSON = join(ROOT, '.claude-plugin', 'marketplace.extended.json');
const MANIFEST_JSON = join(ROOT, 'marketplace', 'src', 'data', 'cowork-manifest.json');
const PLUGIN_ZIP_DIR = join(ROOT, 'marketplace', 'public', 'downloads', 'plugins');
const BUNDLE_ZIP_DIR = join(ROOT, 'marketplace', 'public', 'downloads', 'bundles');

const SKIP_CATEGORIES = new Set(['mcp']);

function catalogCategory(plugin) {
  const source = plugin.source || '';
  const dirParts = source.replace(/^\.?\/?plugins\//, '').split('/');
  return dirParts.length > 1 ? dirParts[0] : plugin.category || 'uncategorized';
}

function listZips(dir) {
  if (!existsSync(dir)) return [];
  return readdirSync(dir).filter((f) => f.endsWith('.zip'));
}

const errors = [];

if (!existsSync(EXTENDED_JSON)) {
  console.error(`FATAL: catalog not found at ${EXTENDED_JSON}`);
  process.exit(1);
}
if (!existsSync(MANIFEST_JSON)) {
  console.error(
    `FATAL: cowork manifest not found at ${MANIFEST_JSON} — run \`node scripts/build-cowork-zips.mjs\` first`,
  );
  process.exit(1);
}

const catalog = JSON.parse(readFileSync(EXTENDED_JSON, 'utf-8'));
const manifest = JSON.parse(readFileSync(MANIFEST_JSON, 'utf-8'));

const catalogPlugins = (catalog.plugins || []).filter(
  (p) => !SKIP_CATEGORIES.has(catalogCategory(p)),
);
const catalogNames = new Set(catalogPlugins.map((p) => p.name));

const manifestPlugins = manifest.plugins || [];
const manifestNames = new Set(manifestPlugins.map((p) => p.name));

const manifestBundles = manifest.bundles || [];
const manifestBundleNames = new Set(manifestBundles.map((b) => b.fileName));

// Check 1: catalog count == manifest count (non-MCP)
if (catalogPlugins.length !== manifestPlugins.length) {
  errors.push(
    `Plugin count mismatch: catalog has ${catalogPlugins.length} non-MCP plugins, manifest has ${manifestPlugins.length}`,
  );
}

// Check 2: every catalog (non-MCP) plugin appears in manifest
for (const p of catalogPlugins) {
  if (!manifestNames.has(p.name)) {
    errors.push(`Catalog plugin "${p.name}" missing from manifest`);
  }
}

// Check 3: every manifest entry's zip exists on disk
for (const p of manifestPlugins) {
  const zipPath = join(ROOT, 'marketplace', 'public', p.path.replace(/^\//, ''));
  if (!existsSync(zipPath)) {
    errors.push(`Manifest plugin "${p.name}" references missing zip: ${p.path}`);
  }
}

// Check 4: every zip on disk has a matching manifest entry
const diskPluginZips = listZips(PLUGIN_ZIP_DIR);
const expectedPluginZips = new Set(manifestPlugins.map((p) => p.fileName));
for (const zip of diskPluginZips) {
  if (!expectedPluginZips.has(zip)) {
    errors.push(`Orphan plugin zip on disk (no manifest entry): plugins/${zip}`);
  }
}

// Check 5: every manifest plugin entry's name appears in catalog (no extra manifest entries)
for (const p of manifestPlugins) {
  if (!catalogNames.has(p.name)) {
    errors.push(`Manifest plugin "${p.name}" not present in catalog (stale manifest entry)`);
  }
}

// Check 6: every bundle zip on disk has a matching manifest bundle entry
const diskBundleZips = listZips(BUNDLE_ZIP_DIR);
for (const zip of diskBundleZips) {
  if (!manifestBundleNames.has(zip)) {
    errors.push(`Orphan bundle zip on disk (no manifest entry): bundles/${zip}`);
  }
}

// Check 7: every manifest bundle has a zip on disk
for (const b of manifestBundles) {
  const zipPath = join(ROOT, 'marketplace', 'public', b.path.replace(/^\//, ''));
  if (!existsSync(zipPath)) {
    errors.push(`Manifest bundle "${b.fileName}" references missing zip: ${b.path}`);
  }
}

if (errors.length > 0) {
  console.error('Cowork manifest drift detected:\n');
  for (const e of errors) {
    console.error(`  - ${e}`);
  }
  console.error(
    `\n${errors.length} drift error(s). Run \`node scripts/build-cowork-zips.mjs\` to regenerate.`,
  );
  process.exit(1);
}

console.log('Cowork manifest aligned:');
console.log(`  ${catalogPlugins.length} non-MCP catalog plugins`);
console.log(`  ${manifestPlugins.length} manifest plugin entries`);
console.log(`  ${diskPluginZips.length} plugin zips on disk`);
console.log(`  ${manifestBundles.length} manifest bundle entries`);
console.log(`  ${diskBundleZips.length} bundle zips on disk`);
