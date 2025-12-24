#!/usr/bin/env node

/**
 * validate-official-links.mjs
 *
 * Validates that all external links in playbook pages only reference official domains.
 * This enforces that "Official References" sections only link to authoritative sources.
 *
 * Allowed domains:
 * - docs.anthropic.com
 * - anthropic.com
 * - github.com/anthropics
 * - github.com/GoogleCloudPlatform
 *
 * Exit codes:
 * - 0: All links valid
 * - 1: Disallowed domains found
 */

import { readFileSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const pagesDir = join(__dirname, '../src/pages/playbooks');

// Allowed domains for official references
const ALLOWED_DOMAINS = [
  'docs.anthropic.com',
  'anthropic.com',
  'github.com/anthropics',
  'github.com/GoogleCloudPlatform'
];

// Regex to find URLs in Astro/HTML content
const URL_REGEX = /href=["']https?:\/\/([^"']+)["']/gi;

function extractDomain(url) {
  try {
    const urlObj = new URL(url);
    const domain = urlObj.hostname + urlObj.pathname;
    return domain;
  } catch (e) {
    return url;
  }
}

function isAllowedDomain(url) {
  const domain = extractDomain(url);

  return ALLOWED_DOMAINS.some(allowed => {
    if (allowed.includes('/')) {
      // Check if domain + path starts with allowed path
      return domain.startsWith(allowed);
    } else {
      // Check if hostname matches
      return domain.split('/')[0] === allowed || domain.split('/')[0].endsWith('.' + allowed);
    }
  });
}

function validateFile(filePath) {
  const content = readFileSync(filePath, 'utf-8');
  const errors = [];

  let match;
  while ((match = URL_REGEX.exec(content)) !== null) {
    const fullUrl = match[0];
    const urlWithoutQuotes = fullUrl.replace(/href=["']/, '').replace(/["']$/, '');

    // Skip internal links (relative paths, anchors)
    if (urlWithoutQuotes.startsWith('/') || urlWithoutQuotes.startsWith('#') || urlWithoutQuotes.startsWith('./')) {
      continue;
    }

    // Skip localhost URLs (used in examples)
    if (urlWithoutQuotes.includes('localhost') || urlWithoutQuotes.includes('127.0.0.1')) {
      continue;
    }

    if (!isAllowedDomain(urlWithoutQuotes)) {
      errors.push({
        url: urlWithoutQuotes,
        context: match[0]
      });
    }
  }

  return errors;
}

function main() {
  console.log('🔍 Validating official links in playbook pages...\n');
  console.log('Allowed domains:');
  ALLOWED_DOMAINS.forEach(domain => console.log(`  ✓ ${domain}`));
  console.log('');

  const files = readdirSync(pagesDir)
    .filter(f => f.endsWith('.astro') && f !== 'index.astro');

  let totalErrors = 0;
  const fileErrors = {};

  files.forEach(file => {
    const filePath = join(pagesDir, file);
    const errors = validateFile(filePath);

    if (errors.length > 0) {
      totalErrors += errors.length;
      fileErrors[file] = errors;
    }
  });

  if (totalErrors === 0) {
    console.log('✅ All external links are valid!');
    console.log(`   Checked ${files.length} playbook pages.`);
    process.exit(0);
  } else {
    console.error('❌ Found disallowed external links:\n');

    Object.entries(fileErrors).forEach(([file, errors]) => {
      console.error(`  ${file}:`);
      errors.forEach(error => {
        console.error(`    • ${error.url}`);
      });
      console.error('');
    });

    console.error(`Total violations: ${totalErrors}`);
    console.error('\nOnly these domains are allowed:');
    ALLOWED_DOMAINS.forEach(domain => console.error(`  - ${domain}`));

    process.exit(1);
  }
}

main();
