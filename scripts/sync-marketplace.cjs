#!/usr/bin/env node

/**
 * Sync the CLI marketplace catalog with the extended metadata file.
 * Ensures `.claude-plugin/marketplace.json` only contains schema-supported fields.
 *
 * KERNEL-DERIVED BLOCKLIST (DR-049 consumer cutover, cleanup half):
 * The set of keys stripped from each plugin entry is DERIVED from the Spec
 * Authority Kernel (@intentsolutions/core, pinned exactly in package.json):
 * allowed entry keys = plugin-manifest (upstream-base + is-overlay properties)
 * ∪ the marketplace-catalog items surface (properties + required)
 * ∪ CATALOG_ENTRY_ONLY_KEYS (entry-only keys documented at
 *   code.claude.com/docs/en/plugin-marketplaces that the kernel's
 *   marketplace-catalog items schema has not vendored yet).
 * DISALLOWED = extended-catalog entry keys NOT in the allowed set, UNION the
 * hand-curated display-only floor below. When the kernel is absent the script
 * warns loudly and falls back to the floor alone.
 */

const fs = require('fs');
const path = require('path');

const repoRoot = path.join(__dirname, '..');
const extendedPath = path.join(repoRoot, '.claude-plugin', 'marketplace.extended.json');
const cliPath = path.join(repoRoot, '.claude-plugin', 'marketplace.json');

// Hand-curated display-only list — KEPT as the FLOOR of the blocklist (always
// stripped, even if a future kernel schema were to allow one of them). The
// kernel-derived set above it is the authority-tracking layer; this floor is
// the website-display contract.
const FLOOR_DISALLOWED_KEYS = new Set([
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

// Catalog-entry-only keys documented in the Anthropic plugin-marketplaces
// reference (code.claude.com/docs/en/plugin-marketplaces "Plugin entries")
// that the kernel's marketplace-catalog items schema does not vendor yet —
// it currently constrains entries to required [name, source] only. Remove
// each key from this supplement once the kernel vendors it.
const CATALOG_ENTRY_ONLY_KEYS = ['category', 'tags', 'strict'];

const KERNEL_SCHEMA_DIR = path.join(
  repoRoot,
  'node_modules',
  '@intentsolutions',
  'core',
  'schemas',
  'authoring',
  'v1',
);

/**
 * Existence-guarded load of the kernel's authoring/v1 contract surface for a
 * marketplace plugin entry. Returns a Set of allowed top-level keys, or null
 * when the kernel is not installed / unreadable (caller falls back to the
 * hand-curated floor with a loud warning).
 */
function loadKernelAllowedEntryKeys() {
  const manifestBasePath = path.join(KERNEL_SCHEMA_DIR, 'upstream-base', 'plugin-manifest.v1.json');
  const manifestOverlayPath = path.join(KERNEL_SCHEMA_DIR, 'is-overlay', 'plugin-manifest.v1.json');
  const catalogBasePath = path.join(
    KERNEL_SCHEMA_DIR,
    'upstream-base',
    'marketplace-catalog.v1.json',
  );
  if (
    !fs.existsSync(manifestBasePath) ||
    !fs.existsSync(manifestOverlayPath) ||
    !fs.existsSync(catalogBasePath)
  ) {
    return null;
  }
  try {
    const manifestBase = JSON.parse(fs.readFileSync(manifestBasePath, 'utf8'));
    const manifestOverlay = JSON.parse(fs.readFileSync(manifestOverlayPath, 'utf8'));
    const catalogBase = JSON.parse(fs.readFileSync(catalogBasePath, 'utf8'));

    const allowed = new Set([
      ...Object.keys(manifestBase.properties || {}),
      ...Object.keys(manifestOverlay.properties || {}),
    ]);
    // The marketplace-catalog base constrains each plugins[] entry
    // (required [name, source]) — fold that entry surface in.
    const items = ((catalogBase.properties || {}).plugins || {}).items || {};
    for (const key of Object.keys(items.properties || {})) allowed.add(key);
    for (const key of items.required || []) allowed.add(key);
    for (const key of CATALOG_ENTRY_ONLY_KEYS) allowed.add(key);
    return allowed;
  } catch (error) {
    console.warn(`⚠️  Failed to load kernel schemas (${error.message}) — falling back.`);
    return null;
  }
}

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

// Derive the blocklist: extended-catalog entry keys not allowed by the kernel
// contract, UNION the hand-curated display-only floor.
const kernelAllowed = loadKernelAllowedEntryKeys();
const derivedKeys = new Set();
if (kernelAllowed === null) {
  console.warn(
    '⚠️  KERNEL ABSENT: @intentsolutions/core schemas not found under node_modules — ' +
      'cannot derive the blocklist from the kernel contract. Falling back to the ' +
      'hand-curated DISALLOWED_KEYS floor only. Run `pnpm install` to restore derivation.',
  );
} else {
  for (const plugin of marketplace.plugins) {
    if (plugin === null || typeof plugin !== 'object') continue;
    for (const key of Object.keys(plugin)) {
      if (!kernelAllowed.has(key)) {
        derivedKeys.add(key);
      }
    }
  }
}

const DISALLOWED_KEYS = new Set([...derivedKeys, ...FLOOR_DISALLOWED_KEYS]);

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
if (kernelAllowed !== null) {
  console.log(
    `   Blocklist: ${derivedKeys.size} key(s) DERIVED from the kernel contract` +
      `${derivedKeys.size ? ` [${[...derivedKeys].sort().join(', ')}]` : ''} + ` +
      `${FLOOR_DISALLOWED_KEYS.size} hand-curated FLOOR key(s) ` +
      `[${[...FLOOR_DISALLOWED_KEYS].sort().join(', ')}]`,
  );
} else {
  console.log(
    `   Blocklist: kernel absent — FLOOR only ` +
      `[${[...FLOOR_DISALLOWED_KEYS].sort().join(', ')}]`,
  );
}
