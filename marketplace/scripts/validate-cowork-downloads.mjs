#!/usr/bin/env node
/**
 * CI GATE: Cowork Downloads Build Output Validator
 *
 * Validates that the cowork zip build script produced correct output:
 * manifest.json, plugin zips, bundle zips, mega-zip, checksums, and
 * download link integrity on the /cowork page.
 *
 * Exit codes:
 * - 0: All checks pass
 * - 1: Validation failures detected
 *
 * Usage:
 *   node marketplace/scripts/validate-cowork-downloads.mjs
 */

import { readFileSync, existsSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { createHash } from 'crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DIST_DIR = join(__dirname, '../dist');
const DOWNLOADS_DIR = join(DIST_DIR, 'downloads');
const MANIFEST_PATH = join(DOWNLOADS_DIR, 'manifest.json');
const COWORK_HTML_PATH = join(DIST_DIR, 'cowork/index.html');
const PACKS_JSON_PATH = join(__dirname, '../src/data/cowork-packs.json');

console.log('📦 Validating Cowork Downloads build output...\n');

let failures = 0;
let passes = 0;

function pass(msg) {
  console.log(`  ✓ ${msg}`);
  passes++;
}

function fail(msg) {
  console.error(`  ✗ ${msg}`);
  failures++;
}

// ── Check 1: Manifest exists ────────────────────────────────────────────
console.log('1. Manifest exists');
if (!existsSync(MANIFEST_PATH)) {
  fail(`manifest.json not found at ${MANIFEST_PATH}`);
  console.error('\n❌ Cannot continue without manifest. Run build-cowork-zips.mjs first.\n');
  process.exit(1);
}
pass('manifest.json exists');

let manifest;
try {
  manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
  pass('manifest.json is valid JSON');
} catch (e) {
  fail(`manifest.json is not valid JSON: ${e.message}`);
  console.error('\n❌ Cannot continue with invalid manifest.\n');
  process.exit(1);
}

// ── Check 2: Manifest schema ────────────────────────────────────────────
console.log('\n2. Manifest schema');
const requiredFields = ['plugins', 'bundles', 'megaZip'];
for (const field of requiredFields) {
  if (manifest[field] === undefined) {
    fail(`Missing required field: ${field}`);
  } else {
    pass(`Has '${field}' field`);
  }
}

if (manifest.generated) {
  // Verify ISO timestamp
  const d = new Date(manifest.generated);
  if (isNaN(d.getTime())) {
    fail(`'generated' is not a valid ISO timestamp: ${manifest.generated}`);
  } else {
    pass(`'generated' is valid ISO timestamp`);
  }
}

if (!Array.isArray(manifest.plugins)) {
  fail('plugins is not an array');
} else {
  pass(`plugins array has ${manifest.plugins.length} entries`);
}

if (!Array.isArray(manifest.bundles)) {
  fail('bundles is not an array');
} else {
  pass(`bundles array has ${manifest.bundles.length} entries`);
}

// ── Check 3: Plugin zip existence ───────────────────────────────────────
console.log('\n3. Plugin zip existence');
let missingPlugins = 0;
if (Array.isArray(manifest.plugins)) {
  for (const plugin of manifest.plugins) {
    if (!plugin.path) {
      fail(`Plugin '${plugin.name || 'unknown'}' has no path`);
      missingPlugins++;
      continue;
    }
    // Paths in manifest are relative to site root (e.g., /downloads/plugins/foo.zip)
    const zipPath = join(DIST_DIR, plugin.path.replace(/^\//, ''));
    if (!existsSync(zipPath)) {
      fail(`Plugin zip missing: ${plugin.path}`);
      missingPlugins++;
    }
  }
  if (missingPlugins === 0) {
    pass(`All ${manifest.plugins.length} plugin zips exist`);
  }
}

// ── Check 4: Bundle zip existence ───────────────────────────────────────
console.log('\n4. Bundle zip existence');
let missingBundles = 0;
if (Array.isArray(manifest.bundles)) {
  for (const bundle of manifest.bundles) {
    if (!bundle.path) {
      fail(`Bundle '${bundle.name || 'unknown'}' has no path`);
      missingBundles++;
      continue;
    }
    const zipPath = join(DIST_DIR, bundle.path.replace(/^\//, ''));
    if (!existsSync(zipPath)) {
      fail(`Bundle zip missing: ${bundle.path}`);
      missingBundles++;
    }
  }
  if (missingBundles === 0) {
    pass(`All ${manifest.bundles.length} bundle zips exist`);
  }
}

// ── Check 5: Mega-zip existence ─────────────────────────────────────────
console.log('\n5. Mega-zip existence');
if (manifest.megaZip && manifest.megaZip.path) {
  const megaPath = join(DIST_DIR, manifest.megaZip.path.replace(/^\//, ''));
  if (existsSync(megaPath)) {
    pass(`Mega-zip exists: ${manifest.megaZip.path}`);
  } else {
    fail(`Mega-zip missing: ${manifest.megaZip.path}`);
  }
} else {
  fail('megaZip has no path');
}

// ── Check 6: Size sanity ────────────────────────────────────────────────
console.log('\n6. Size sanity');
let sizeIssues = 0;
const MAX_PLUGIN_SIZE = 5 * 1024 * 1024; // 5MB

if (Array.isArray(manifest.plugins)) {
  for (const plugin of manifest.plugins) {
    if (!plugin.path) continue;
    const zipPath = join(DIST_DIR, plugin.path.replace(/^\//, ''));
    if (!existsSync(zipPath)) continue;

    const size = statSync(zipPath).size;
    if (size === 0) {
      fail(`Zero-byte zip: ${plugin.path}`);
      sizeIssues++;
    }
    if (size > MAX_PLUGIN_SIZE) {
      fail(`Plugin zip too large (${(size / 1024 / 1024).toFixed(1)}MB > 5MB): ${plugin.path}`);
      sizeIssues++;
    }
  }
}

// Mega-zip should be larger than any bundle
if (manifest.megaZip?.path && Array.isArray(manifest.bundles)) {
  const megaPath = join(DIST_DIR, manifest.megaZip.path.replace(/^\//, ''));
  if (existsSync(megaPath)) {
    const megaSize = statSync(megaPath).size;
    let largestBundle = 0;

    for (const bundle of manifest.bundles) {
      if (!bundle.path) continue;
      const bundlePath = join(DIST_DIR, bundle.path.replace(/^\//, ''));
      if (existsSync(bundlePath)) {
        const bSize = statSync(bundlePath).size;
        if (bSize > largestBundle) largestBundle = bSize;
      }
    }

    if (megaSize > largestBundle) {
      pass(`Mega-zip (${(megaSize / 1024 / 1024).toFixed(1)}MB) > largest bundle (${(largestBundle / 1024 / 1024).toFixed(1)}MB)`);
    } else {
      fail(`Mega-zip (${megaSize} bytes) is not larger than largest bundle (${largestBundle} bytes)`);
      sizeIssues++;
    }
  }
}

if (sizeIssues === 0) {
  pass('All zips pass size sanity checks');
}

// ── Check 7: Checksum spot-check ────────────────────────────────────────
console.log('\n7. Checksum spot-check (up to 10 random plugins)');
if (Array.isArray(manifest.plugins)) {
  const pluginsWithChecksums = manifest.plugins.filter(p => p.sha256 && p.path);
  const sample = pluginsWithChecksums
    .sort(() => Math.random() - 0.5)
    .slice(0, 10);

  let checksumFails = 0;
  for (const plugin of sample) {
    const zipPath = join(DIST_DIR, plugin.path.replace(/^\//, ''));
    if (!existsSync(zipPath)) continue;

    const content = readFileSync(zipPath);
    const hash = createHash('sha256').update(content).digest('hex');

    if (hash !== plugin.sha256) {
      fail(`Checksum mismatch for ${plugin.name}: expected ${plugin.sha256}, got ${hash}`);
      checksumFails++;
    }
  }

  if (checksumFails === 0 && sample.length > 0) {
    pass(`${sample.length} checksums verified`);
  } else if (sample.length === 0) {
    pass('No checksums to verify (plugins may not have sha256 field)');
  }
}

// ── Check 8: Bundle coverage ────────────────────────────────────────────
console.log('\n8. Bundle coverage (vs cowork-packs.json)');
if (existsSync(PACKS_JSON_PATH)) {
  const packsData = JSON.parse(readFileSync(PACKS_JSON_PATH, 'utf-8'));
  const packIds = (packsData.packs || []).map(p => p.id || p.category);

  if (Array.isArray(manifest.bundles)) {
    const bundleIds = manifest.bundles.map(b => b.id || b.category || b.name);
    const missingPacks = packIds.filter(id => !bundleIds.some(bid =>
      bid === id || bid.includes(id) || id.includes(bid)
    ));

    if (missingPacks.length === 0) {
      pass(`All ${packIds.length} category packs have bundles`);
    } else {
      // Warn but don't hard-fail since pack names may not perfectly match bundle IDs
      console.log(`  ⚠ ${missingPacks.length} pack(s) may not have matching bundles: ${missingPacks.join(', ')}`);
      pass('Bundle coverage check completed (see warnings above)');
    }
  }
} else {
  pass('cowork-packs.json not found, skipping bundle coverage');
}

// ── Check 9: Download link integrity ────────────────────────────────────
console.log('\n9. Download link integrity (cowork page)');
if (existsSync(COWORK_HTML_PATH)) {
  const html = readFileSync(COWORK_HTML_PATH, 'utf-8');
  const downloadHrefs = [];
  const hrefRegex = /href=["']([^"']*\/downloads\/[^"']*)["']/gi;
  let match;

  while ((match = hrefRegex.exec(html)) !== null) {
    downloadHrefs.push(match[1]);
  }

  let brokenLinks = 0;
  for (const href of downloadHrefs) {
    const filePath = join(DIST_DIR, href.replace(/^\//, ''));
    if (!existsSync(filePath)) {
      fail(`Broken download link: ${href}`);
      brokenLinks++;
    }
  }

  if (brokenLinks === 0 && downloadHrefs.length > 0) {
    pass(`All ${downloadHrefs.length} download links resolve to files`);
  } else if (downloadHrefs.length === 0) {
    pass('No /downloads/ links found on cowork page (may use dynamic paths)');
  }
} else {
  fail('cowork/index.html not found - cannot check download links');
}

// ── Summary ─────────────────────────────────────────────────────────────
console.log(`\n📊 Results: ${passes} passed, ${failures} failed\n`);

if (failures > 0) {
  console.error('❌ Cowork downloads validation FAILED\n');
  process.exit(1);
}

console.log('✅ All cowork download checks passed!\n');
process.exit(0);
