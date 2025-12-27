#!/usr/bin/env node
/**
 * CI GATE: Playbook Route Validation (0kh.10.3 - Real-world Scenario Testing)
 *
 * Validates that every playbook link in index.astro has a corresponding page file.
 * Also validates dist output exists after build (when available).
 * Prevents shipping broken 404s on /playbooks/* routes.
 *
 * Exit codes:
 * - 0: All playbook routes valid
 * - 1: Missing playbook pages detected
 *
 * Usage:
 *   node validate-playbook-routes.mjs           # Pre-build: check source files
 *   node validate-playbook-routes.mjs --dist    # Post-build: also check dist output
 */

import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, basename } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const checkDist = process.argv.includes('--dist');

const PLAYBOOKS_DIR = join(__dirname, '../src/pages/playbooks');
const INDEX_FILE = join(PLAYBOOKS_DIR, 'index.astro');

console.log('🔍 Validating playbook routes...\n');

// Check if playbooks directory exists
if (!existsSync(PLAYBOOKS_DIR)) {
  console.error('❌ Playbooks directory not found:', PLAYBOOKS_DIR);
  process.exit(1);
}

// Read index.astro to extract playbook slugs
let indexContent;
try {
  indexContent = readFileSync(INDEX_FILE, 'utf-8');
} catch (error) {
  console.error('❌ Failed to read playbooks index:', error.message);
  process.exit(1);
}

// Extract slugs from the playbooks array in index.astro
// Match: slug: '01-multi-agent-rate-limits',
const slugMatches = indexContent.matchAll(/slug:\s*['"]([^'"]+)['"]/g);
const expectedSlugs = [...slugMatches].map(m => m[1]);

if (expectedSlugs.length === 0) {
  console.error('❌ No playbook slugs found in index.astro');
  process.exit(1);
}

// Get all .astro files in playbooks directory (excluding index.astro)
const existingPages = readdirSync(PLAYBOOKS_DIR)
  .filter(f => f.endsWith('.astro') && f !== 'index.astro')
  .map(f => basename(f, '.astro'));

console.log(`📊 Statistics:`);
console.log(`   Playbooks in index: ${expectedSlugs.length}`);
console.log(`   Page files found: ${existingPages.length}\n`);

// Validate each slug has a corresponding page file
let missingPages = [];
let errors = 0;

for (const slug of expectedSlugs) {
  if (!existingPages.includes(slug)) {
    missingPages.push(slug);
    errors++;
  }
}

// Check for underscore-prefixed files (Astro ignores these)
const underscoreFiles = readdirSync(PLAYBOOKS_DIR)
  .filter(f => f.startsWith('_') && f.endsWith('.astro'));

if (underscoreFiles.length > 0) {
  console.warn(`⚠️  ${underscoreFiles.length} underscore-prefixed file(s) detected (NOT generated as routes):\n`);
  underscoreFiles.forEach(f => {
    console.warn(`   • ${f} → Rename to ${f.slice(1)} to generate route`);
  });
  console.warn('');
  // This is an error condition - underscore files won't be routes
  errors += underscoreFiles.length;
}

// Check for orphan pages (pages without index reference)
const orphanPages = existingPages.filter(p => !expectedSlugs.includes(p));

// Report results
if (missingPages.length > 0) {
  console.error(`❌ ${missingPages.length} playbook(s) missing page files:\n`);
  missingPages.forEach(slug => {
    console.error(`   • ${slug}`);
    console.error(`     Expected: ${PLAYBOOKS_DIR}/${slug}.astro`);
    console.error(`     Link: /playbooks/${slug}/\n`);
  });
}

if (orphanPages.length > 0) {
  console.warn(`⚠️  ${orphanPages.length} orphan page(s) detected (not in index):\n`);
  orphanPages.forEach(page => {
    console.warn(`   • ${page}.astro (not listed in index.astro)`);
  });
  console.warn('');
}

if (errors > 0) {
  console.error(`\n❌ Playbook route validation FAILED with ${errors} error(s)`);
  process.exit(1);
}

if (orphanPages.length > 0) {
  console.warn(`\n⚠️  Playbook validation completed with ${orphanPages.length} warning(s)`);
}

console.log('✅ Source file validation passed!\n');

// Phase 2: Validate dist output (post-build)
if (checkDist) {
  console.log('🔍 Validating dist output...\n');

  const DIST_DIR = join(__dirname, '../dist/playbooks');

  if (!existsSync(DIST_DIR)) {
    console.error('❌ Dist playbooks directory not found:', DIST_DIR);
    console.error('   Run `npm run build` first, then `npm run validate:playbooks -- --dist`');
    process.exit(1);
  }

  let distErrors = 0;
  const missingDist = [];

  for (const slug of expectedSlugs) {
    const distPath = join(DIST_DIR, slug, 'index.html');
    if (!existsSync(distPath)) {
      missingDist.push(slug);
      distErrors++;
    }
  }

  if (distErrors > 0) {
    console.error(`❌ ${distErrors} playbook(s) missing from dist output:\n`);
    missingDist.forEach(slug => {
      console.error(`   • ${slug}`);
      console.error(`     Expected: dist/playbooks/${slug}/index.html`);
      console.error(`     URL: /playbooks/${slug}/\n`);
    });
    console.error('\n❌ Dist validation FAILED - these pages will 404 in production');
    process.exit(1);
  }

  // Count what's in dist
  const distDirs = readdirSync(DIST_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  console.log(`📊 Dist Statistics:`);
  console.log(`   Expected playbooks: ${expectedSlugs.length}`);
  console.log(`   Built pages: ${distDirs.length}\n`);

  console.log('✅ Dist output validation passed!\n');
}

console.log('✅ All playbook route validations passed!\n');
process.exit(0);
