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

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DIST_DIR = join(__dirname, '../dist');

// Known broken links to ignore (pre-existing issues, tracked separately)
// TODO: Fix these and remove from ignore list
const KNOWN_ISSUES = [
  '/plugins/001-jeremy-taskwarrior-integration/',  // Plugin not in marketplace catalog
  '/plugins/skills-powerkit/',                      // Plugin not in marketplace catalog
];

// Seed pages to scan for internal links
const SEED_PAGES = [
  'index.html',
  'playbooks/index.html',
  'explore/index.html',
  'skills/index.html',
];

console.log('🔗 Validating internal links...\n');

// Check if dist directory exists
if (!existsSync(DIST_DIR)) {
  console.error('❌ Dist directory not found:', DIST_DIR);
  console.error('   Run `npm run build` first');
  process.exit(1);
}

/**
 * Extract internal links from HTML content
 */
function extractInternalLinks(html, sourcePath) {
  const links = [];
  // Match href attributes in anchor tags
  const hrefRegex = /<a[^>]+href=["']([^"']+)["']/gi;
  let match;

  while ((match = hrefRegex.exec(html)) !== null) {
    const href = match[1];

    // Skip external links
    if (href.startsWith('http://') || href.startsWith('https://')) continue;
    // Skip mailto/tel
    if (href.startsWith('mailto:') || href.startsWith('tel:')) continue;
    // Skip hash-only links
    if (href.startsWith('#')) continue;
    // Skip javascript:
    if (href.startsWith('javascript:')) continue;
    // Skip data: URIs
    if (href.startsWith('data:')) continue;
    // Skip unrendered template literals (client-side JS)
    if (href.includes('${')) continue;

    // Normalize: strip query and hash
    let path = href.split('?')[0].split('#')[0];

    // Skip empty paths
    if (!path || path === '') continue;

    links.push({
      href: path,
      source: sourcePath,
    });
  }

  return links;
}

/**
 * Check if a path resolves to an existing file in dist
 */
function pathExists(path) {
  // Normalize path
  let normalizedPath = path;

  // Handle root path
  if (normalizedPath === '/') {
    normalizedPath = '';
  }

  // Remove leading slash
  if (normalizedPath.startsWith('/')) {
    normalizedPath = normalizedPath.slice(1);
  }

  // Remove trailing slash for checking
  if (normalizedPath.endsWith('/')) {
    normalizedPath = normalizedPath.slice(0, -1);
  }

  // Check various file patterns
  const checks = [
    join(DIST_DIR, normalizedPath, 'index.html'),  // /foo/ -> /foo/index.html
    join(DIST_DIR, normalizedPath + '.html'),       // /foo -> /foo.html
    join(DIST_DIR, normalizedPath),                 // /foo.css, /foo.js, etc.
  ];

  // For root path
  if (normalizedPath === '') {
    return existsSync(join(DIST_DIR, 'index.html'));
  }

  return checks.some(checkPath => existsSync(checkPath));
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
