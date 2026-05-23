#!/usr/bin/env node

/**
 * Sync the CLI marketplace catalog with the extended metadata file.
 * Ensures `.claude-plugin/marketplace.json` only contains schema-supported fields.
 */

const fs = require('fs');
const path = require('path');

const repoRoot = path.join(__dirname, '..');
const extendedPath = path.join(repoRoot, '.claude-plugin', 'marketplace.extended.json');
const cliPath = path.join(repoRoot, '.claude-plugin', 'marketplace.json');

const DISALLOWED_KEYS = new Set([
  'featured',
  'mcpTools',
  'pluginCount',
  'pricing',
  'components',
  'zcf_metadata',
  'external_sync',
  'verification',
  // Marketplace-website-only display fields. Added 2026-05-07 (Phase 4 of the
  // "Use the Printing Press to Learn" plan). The website renders these from
  // marketplace.extended.json; the CLI marketplace.json never sees them.
  'tagline', // 6–10 word NOI-framed outcome subtitle
  'jrig', // { verified, layers_passed, total_layers, baseline_delta }
  'generated', // boolean — set by /skill-creator --forge in plugin.json AND mirrored to marketplace.extended.json
  'author_type', // 'human' | 'forge' — provenance flag, ditto
]);

if (!fs.existsSync(extendedPath)) {
  console.error(`❌ Missing extended marketplace catalog at ${extendedPath}`);
  process.exit(1);
}

const rawData = fs.readFileSync(extendedPath, 'utf8');
let marketplace;

try {
  marketplace = JSON.parse(rawData);
} catch (error) {
  console.error('❌ Failed to parse marketplace.extended.json:', error.message);
  process.exit(1);
}

if (!Array.isArray(marketplace.plugins)) {
  console.error('❌ Invalid marketplace format: expected "plugins" array.');
  process.exit(1);
}

const sanitized = {
  ...marketplace,
  plugins: marketplace.plugins.map((plugin) => {
    if (plugin === null || typeof plugin !== 'object') {
      return plugin;
    }

    const sanitizedPlugin = {};
    for (const [key, value] of Object.entries(plugin)) {
      if (!DISALLOWED_KEYS.has(key)) {
        sanitizedPlugin[key] = value;
      }
    }
    return sanitizedPlugin;
  }),
};

fs.writeFileSync(cliPath, JSON.stringify(sanitized, null, 2) + '\n');
console.log(`✅ Synced CLI marketplace catalog -> ${cliPath}`);
