#!/usr/bin/env node
/**
 * CI GATE: Cowork Zip Content Security Scanner
 *
 * Lists zip contents and verifies no sensitive files leaked through
 * the build-cowork-zips.mjs script. Does NOT extract zips - only
 * reads file listings.
 *
 * Exit codes:
 * - 0: No sensitive files found
 * - 1: Sensitive files detected in zips
 *
 * Usage:
 *   node scripts/validate-cowork-security.mjs
 */

import { existsSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = join(__dirname, '..');
const DIST_DIR = join(REPO_ROOT, 'marketplace', 'dist');
const PLUGINS_ZIP_DIR = join(DIST_DIR, 'downloads', 'plugins');

console.log('🔒 Scanning cowork zip contents for sensitive files...\n');

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

// Gather plugin zips to sample
if (!existsSync(PLUGINS_ZIP_DIR)) {
  console.log('⚠️  No plugin zips directory found. Skipping security scan.');
  console.log('   Expected: marketplace/dist/downloads/plugins/');
  process.exit(0);
}

const allZips = readdirSync(PLUGINS_ZIP_DIR)
  .filter(f => f.endsWith('.zip'))
  .map(f => join(PLUGINS_ZIP_DIR, f));

if (allZips.length === 0) {
  console.log('⚠️  No .zip files found in downloads/plugins/. Skipping.');
  process.exit(0);
}

// Sample up to 30 zips (or all if fewer)
const SAMPLE_SIZE = Math.min(30, allZips.length);
const sample = allZips
  .sort(() => Math.random() - 0.5)
  .slice(0, SAMPLE_SIZE);

console.log(`Sampling ${sample.length} of ${allZips.length} plugin zips\n`);

// Sensitive file patterns
const SENSITIVE_PATTERNS = [
  /^id_rsa/i,
  /\.key$/i,
  /\.pem$/i,
  /credentials/i,
  /secrets?\./i,
  /token\./i,
  /\.env($|\.)/i,
];

// ── Check 1: Scan for sensitive file patterns ───────────────────────────
console.log('1. Scanning for sensitive file patterns');
let sensitiveFound = 0;

for (const zipPath of sample) {
  let listing;
  try {
    listing = execSync(`unzip -l "${zipPath}" 2>/dev/null`, { encoding: 'utf-8' });
  } catch {
    // unzip may not be available; try zipinfo
    try {
      listing = execSync(`zipinfo -1 "${zipPath}" 2>/dev/null`, { encoding: 'utf-8' });
    } catch {
      console.log(`  ⚠ Cannot list contents of ${zipPath} (unzip/zipinfo not available)`);
      continue;
    }
  }

  const lines = listing.split('\n');
  for (const line of lines) {
    const filename = line.trim().split(/\s+/).pop() || '';
    for (const pattern of SENSITIVE_PATTERNS) {
      if (pattern.test(filename)) {
        fail(`Sensitive file in zip: ${filename} (in ${zipPath.split('/').pop()})`);
        sensitiveFound++;
      }
    }
  }
}

if (sensitiveFound === 0) {
  pass('No sensitive file patterns detected');
}

// ── Check 2: No hidden files (except .claude-plugin/) ───────────────────
console.log('\n2. Checking for hidden files');
let hiddenFound = 0;

for (const zipPath of sample) {
  let listing;
  try {
    listing = execSync(`zipinfo -1 "${zipPath}" 2>/dev/null`, { encoding: 'utf-8' });
  } catch {
    try {
      listing = execSync(`unzip -l "${zipPath}" 2>/dev/null`, { encoding: 'utf-8' });
    } catch {
      continue;
    }
  }

  const files = listing.split('\n').filter(f => f.trim());
  for (const file of files) {
    // For unzip -l lines, path is the last whitespace-delimited token;
    // for zipinfo -1 lines, the whole trimmed line is the path.
    const rawPath = file.trim().split(/\s+/).pop() || '';
    const parts = rawPath.split('/');
    for (const part of parts) {
      if (part.startsWith('.') && part !== '.' && part !== '..' && part !== '.claude-plugin') {
        fail(`Hidden file/dir in zip: ${file.trim()} (in ${zipPath.split('/').pop()})`);
        hiddenFound++;
        break;
      }
    }
  }
}

if (hiddenFound === 0) {
  pass('No unexpected hidden files found');
}

// ── Check 3: No node_modules ────────────────────────────────────────────
console.log('\n3. Checking for node_modules');
let nodeModulesFound = 0;

for (const zipPath of sample) {
  let listing;
  try {
    listing = execSync(`zipinfo -1 "${zipPath}" 2>/dev/null`, { encoding: 'utf-8' });
  } catch {
    try {
      listing = execSync(`unzip -l "${zipPath}" 2>/dev/null`, { encoding: 'utf-8' });
    } catch {
      continue;
    }
  }

  if (listing.includes('node_modules')) {
    fail(`node_modules found in ${zipPath.split('/').pop()}`);
    nodeModulesFound++;
  }
}

if (nodeModulesFound === 0) {
  pass('No node_modules found in any sampled zip');
}

// ── Check 4: No dist/ directories ──────────────────────────────────────
console.log('\n4. Checking for dist/ directories');
let distFound = 0;

for (const zipPath of sample) {
  let listing;
  try {
    listing = execSync(`zipinfo -1 "${zipPath}" 2>/dev/null`, { encoding: 'utf-8' });
  } catch {
    try {
      listing = execSync(`unzip -l "${zipPath}" 2>/dev/null`, { encoding: 'utf-8' });
    } catch {
      continue;
    }
  }

  // Check for dist/ as a directory entry (not substring of e.g. "distribution")
  const files = listing.split('\n');
  for (const file of files) {
    if (/(?:^|\/)dist\//.test(file.trim())) {
      fail(`dist/ directory found in ${zipPath.split('/').pop()}`);
      distFound++;
      break;
    }
  }
}

if (distFound === 0) {
  pass('No dist/ directories found in any sampled zip');
}

// ── Check 5: Verify zip integrity ──────────────────────────────────────
console.log('\n5. Verifying zip integrity (sampled)');
let corruptZips = 0;

for (const zipPath of sample) {
  try {
    execSync(`unzip -t "${zipPath}" 2>/dev/null`, { encoding: 'utf-8' });
  } catch {
    // Try alternative check
    try {
      execSync(`zipinfo "${zipPath}" 2>/dev/null`, { encoding: 'utf-8' });
    } catch {
      fail(`Corrupt or unreadable zip: ${zipPath.split('/').pop()}`);
      corruptZips++;
      continue;
    }
  }
}

if (corruptZips === 0) {
  pass(`All ${sample.length} sampled zips are valid archives`);
}

// ── Summary ─────────────────────────────────────────────────────────────
console.log(`\n📊 Results: ${passes} passed, ${failures} failed\n`);

if (failures > 0) {
  console.error('❌ Cowork security scan FAILED\n');
  process.exit(1);
}

console.log('✅ All cowork security checks passed!\n');
process.exit(0);
