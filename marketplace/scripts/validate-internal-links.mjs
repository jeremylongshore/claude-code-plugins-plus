#!/usr/bin/env node
/**
 * CI GATE: Internal Link Integrity Validator
 *
 * Validates that internal links on key pages resolve to actual built pages.
 * Prevents shipping broken internal links that would 404.
 *
 * Exit codes:
 * - 0: All internal links valid
 * - 1: Broken internal links detected
 *
 * Usage:
 *   node validate-internal-links.mjs --dist
 */

import { readFileSync, existsSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { extractInternalLinks, pathExistsInDist } from './internal-link-utils.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DIST_DIR = join(__dirname, '../dist');

// Known broken links to ignore (pre-existing issues, tracked separately)
const KNOWN_ISSUES = [];

// Seed pages to scan for internal links
const SEED_PAGES = [
  'index.html',
  'playbooks/index.html',
  'explore/index.html',
  'skills/index.html',
  'cowork/index.html',
  'research/index.html',
  'docs/index.html',
];

console.log('🔗 Validating internal links...\n');

// Check if dist directory exists
if (!existsSync(DIST_DIR)) {
  console.error('❌ Dist directory not found:', DIST_DIR);
  console.error('   Run `npm run build` first');
  process.exit(1);
}

/**
 * Check if a path resolves to an existing file in dist
 */
function pathExists(path) {
  return pathExistsInDist(DIST_DIR, path);
}

// Collect all internal links from seed pages
const allLinks = [];
const scannedPages = [];

for (const seedPage of SEED_PAGES) {
  const pagePath = join(DIST_DIR, seedPage);

  if (!existsSync(pagePath)) {
    console.warn(`⚠️  Seed page not found: ${seedPage}`);
    continue;
  }

  const html = readFileSync(pagePath, 'utf-8');
  const links = extractInternalLinks(html, seedPage);
  allLinks.push(...links);
  scannedPages.push(seedPage);
}

console.log(`📊 Statistics:`);
console.log(`   Seed pages scanned: ${scannedPages.length}`);
console.log(`   Internal links found: ${allLinks.length}\n`);

// Deduplicate links by href
const uniqueLinks = new Map();
for (const link of allLinks) {
  if (!uniqueLinks.has(link.href)) {
    uniqueLinks.set(link.href, []);
  }
  uniqueLinks.get(link.href).push(link.source);
}

console.log(`   Unique links to check: ${uniqueLinks.size}\n`);

// Validate each unique link
const brokenLinks = [];
const knownIssueLinks = [];
let validCount = 0;

for (const [href, sources] of uniqueLinks) {
  if (pathExists(href)) {
    validCount++;
  } else if (KNOWN_ISSUES.includes(href)) {
    knownIssueLinks.push({ href, sources });
  } else {
    brokenLinks.push({ href, sources });
  }
}

// Report known issues (warnings, don't fail)
if (knownIssueLinks.length > 0) {
  console.warn(`⚠️  ${knownIssueLinks.length} known issue(s) (tracked separately):\n`);
  for (const { href, sources } of knownIssueLinks) {
    console.warn(`   • ${href}`);
    console.warn(`     Found in: ${sources.join(', ')}\n`);
  }
}

// Report results
if (brokenLinks.length > 0) {
  console.error(`❌ ${brokenLinks.length} broken internal link(s) detected:\n`);

  for (const { href, sources } of brokenLinks) {
    console.error(`   • ${href}`);
    console.error(`     Found in: ${sources.join(', ')}`);
    console.error('');
  }

  console.error(`\n❌ Internal link validation FAILED`);
  console.error(`   ${validCount} valid, ${brokenLinks.length} broken\n`);
  process.exit(1);
}

console.log(`✅ All ${validCount} internal links are valid!\n`);
process.exit(0);
