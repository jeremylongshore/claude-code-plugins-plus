#!/usr/bin/env node

/**
 * Enhance marketplace.extended.json with license and repository fields
 * Part of EPIC F (Catalog Metadata) - claude-code-plugins-0kh.6
 */

const fs = require('fs');
const path = require('path');

const MARKETPLACE_EXTENDED_PATH = path.join(
  __dirname,
  '../.claude-plugin/marketplace.extended.json'
);

const REPO_URL = 'https://github.com/jeremylongshore/claude-code-plugins';
const DEFAULT_LICENSE = 'MIT';

function enhanceMarketplaceMetadata() {
  console.log('📝 Enhancing marketplace metadata...\n');

  // Read marketplace.extended.json
  const catalogPath = MARKETPLACE_EXTENDED_PATH;
  const catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));

  let addedLicense = 0;
  let addedRepository = 0;
  let skippedLicense = 0;
  let skippedRepository = 0;

  // Enhance each plugin
  for (const plugin of catalog.plugins) {
    // Add license if not present
    if (!plugin.license) {
      plugin.license = DEFAULT_LICENSE;
      addedLicense++;
    } else {
      skippedLicense++;
    }

    // Add repository if not present
    if (!plugin.repository) {
      plugin.repository = REPO_URL;
      addedRepository++;
    } else {
      skippedRepository++;
    }
  }

  // Write back to file with pretty formatting
  fs.writeFileSync(
    catalogPath,
    JSON.stringify(catalog, null, 2) + '\n',
    'utf8'
  );

  // Report results
  console.log('✅ Marketplace metadata enhanced!\n');
  console.log(`License field:`);
  console.log(`  ✓ Added to ${addedLicense} plugins`);
  console.log(`  • Skipped ${skippedLicense} plugins (already had license)\n`);

  console.log(`Repository field:`);
  console.log(`  ✓ Added to ${addedRepository} plugins`);
  console.log(`  • Skipped ${skippedRepository} plugins (already had repository)\n`);

  console.log(`Total plugins: ${catalog.plugins.length}`);
  console.log(`\nNext step: Run 'npm run sync-marketplace' to update marketplace.json`);
}

// Run enhancement
try {
  enhanceMarketplaceMetadata();
} catch (error) {
  console.error('❌ Error enhancing metadata:', error.message);
  process.exit(1);
}
