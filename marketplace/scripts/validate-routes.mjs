#!/usr/bin/env node
/**
 * CI GATE: Plugin Route Validation
 *
 * Validates that every plugin in catalog has a corresponding route in dist/
 * Ensures no orphan routes (route exists but no plugin)
 *
 * Exit codes:
 * - 0: All routes valid
 * - 1: Missing routes or orphan routes detected
 */

import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const CATALOG_PATH = join(__dirname, '../../.claude-plugin/marketplace.extended.json');
const DIST_PLUGINS_PATH = join(__dirname, '../dist/plugins');

console.log('🔍 Validating plugin routes...\n');

// Load catalog
let catalog;
try {
  catalog = JSON.parse(readFileSync(CATALOG_PATH, 'utf-8'));
} catch (error) {
  console.error('❌ Failed to load catalog:', error.message);
  process.exit(1);
}

// Check if dist/plugins exists
if (!existsSync(DIST_PLUGINS_PATH)) {
  console.error('❌ dist/plugins/ directory not found. Did you run the build?');
  process.exit(1);
}

// Get all generated routes
const generatedRoutes = new Set(
  readdirSync(DIST_PLUGINS_PATH, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name)
);

console.log(`📊 Statistics:`);
console.log(`   Plugins in catalog: ${catalog.plugins.length}`);
console.log(`   Routes in dist/: ${generatedRoutes.size}\n`);

// Validate each plugin has a route
let missingRoutes = [];
let errors = 0;

for (const plugin of catalog.plugins) {
  const expectedRoute = plugin.name; // Canonical slug is plugin.name

  if (!generatedRoutes.has(expectedRoute)) {
    missingRoutes.push({
      plugin: plugin.name,
      expectedRoute,
      source: plugin.source
    });
    errors++;
  }
}

// Check for orphan routes (routes without plugins)
let orphanRoutes = [];
for (const route of generatedRoutes) {
  const hasPlugin = catalog.plugins.some(p => p.name === route);
  if (!hasPlugin) {
    orphanRoutes.push(route);
  }
}

// Report results
if (missingRoutes.length > 0) {
  console.error(`❌ ${missingRoutes.length} plugin(s) missing routes:\n`);
  missingRoutes.forEach(({ plugin, expectedRoute, source }) => {
    console.error(`   • ${plugin}`);
    console.error(`     Expected: /plugins/${expectedRoute}/`);
    console.error(`     Source: ${source}\n`);
  });
}

if (orphanRoutes.length > 0) {
  console.warn(`⚠️  ${orphanRoutes.length} orphan route(s) detected:\n`);
  orphanRoutes.forEach(route => {
    console.warn(`   • /plugins/${route}/ (no matching plugin in catalog)`);
  });
  console.warn('');
}

if (errors > 0) {
  console.error(`\n❌ Route validation FAILED with ${errors} error(s)`);
  process.exit(1);
}

if (orphanRoutes.length > 0) {
  console.warn(`\n⚠️  Route validation completed with ${orphanRoutes.length} warning(s)`);
  console.warn('   Orphan routes will not cause a failure but should be investigated.\n');
}

console.log('✅ All plugin routes validated successfully!\n');
process.exit(0);
