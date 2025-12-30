#!/usr/bin/env node

// Performance Budget Validation Gate
// Purpose: Prevent bundle bloat and performance regressions
// Exit codes: 0 = All budgets met, 1 = Budget violations detected

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { promisify } from 'util';
import { exec } from 'child_process';
import zlib from 'zlib';

const execAsync = promisify(exec);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_ROOT = path.resolve(__dirname, '..');
const DIST_DIR = path.join(REPO_ROOT, 'marketplace', 'dist');

// Performance budgets
const BUDGETS = {
  totalSize: 3 * 1024 * 1024,  // 3MB gzipped (increased for SaaS skill packs)
  largestFile: 150 * 1024,    // 150KB gzipped (accommodates explore page)
  buildTime: 10 * 1000,       // 10 seconds (ms)
  routeCount: {
    min: 500,
    max: 650,  // Increased for /learn/ hub pages
  },
};

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  bold: '\x1b[1m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

async function gzipSize(filePath) {
  const content = fs.readFileSync(filePath);
  return new Promise((resolve, reject) => {
    zlib.gzip(content, (err, compressed) => {
      if (err) reject(err);
      else resolve(compressed.length);
    });
  });
}

async function walkDir(dir, fileList = []) {
  const files = fs.readdirSync(dir);

  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      await walkDir(filePath, fileList);
    } else {
      fileList.push(filePath);
    }
  }

  return fileList;
}

function countRoutes() {
  let count = 0;

  function walk(dir) {
    const items = fs.readdirSync(dir);

    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        // Check if this directory has an index.html
        const indexPath = path.join(fullPath, 'index.html');
        if (fs.existsSync(indexPath)) {
          count++;
        }
        walk(fullPath);
      }
    }
  }

  // Root index.html
  if (fs.existsSync(path.join(DIST_DIR, 'index.html'))) {
    count++;
  }

  walk(DIST_DIR);
  return count;
}

async function analyzeBundleSize() {
  log('Analyzing bundle size...', 'blue');

  const files = await walkDir(DIST_DIR);
  const fileSizes = [];
  let totalSize = 0;
  let totalGzippedSize = 0;

  for (const file of files) {
    const stat = fs.statSync(file);
    const gzipped = await gzipSize(file);

    totalSize += stat.size;
    totalGzippedSize += gzipped;

    fileSizes.push({
      path: path.relative(DIST_DIR, file),
      size: stat.size,
      gzipped,
    });
  }

  // Sort by gzipped size
  fileSizes.sort((a, b) => b.gzipped - a.gzipped);

  return {
    totalSize,
    totalGzippedSize,
    fileCount: files.length,
    largestFiles: fileSizes.slice(0, 10),
    largestFile: fileSizes[0],
  };
}

async function main() {
  const startTime = Date.now();

  log('\n=== Performance Budget Validation Gate ===\n', 'bold');

  // Check if dist exists
  if (!fs.existsSync(DIST_DIR)) {
    log(`Error: Dist directory not found at ${DIST_DIR}`, 'red');
    log('Run "cd marketplace && npm run build" first', 'yellow');
    process.exit(1);
  }

  log('Performance budgets:', 'blue');
  log(`  - Total size: < ${formatBytes(BUDGETS.totalSize)} (gzipped)`, 'blue');
  log(`  - Largest file: < ${formatBytes(BUDGETS.largestFile)} (gzipped)`, 'blue');
  log(`  - Build time: < ${BUDGETS.buildTime / 1000}s`, 'blue');
  log(`  - Route count: ${BUDGETS.routeCount.min}-${BUDGETS.routeCount.max}`, 'blue');
  log('');

  const violations = [];

  // 1. Bundle Size Analysis
  log('1. Analyzing bundle size...', 'bold');
  const bundleAnalysis = await analyzeBundleSize();

  log(`   Total files: ${bundleAnalysis.fileCount}`, 'blue');
  log(`   Total size (raw): ${formatBytes(bundleAnalysis.totalSize)}`, 'blue');
  log(`   Total size (gzipped): ${formatBytes(bundleAnalysis.totalGzippedSize)}`, 'blue');

  if (bundleAnalysis.totalGzippedSize > BUDGETS.totalSize) {
    const overage = bundleAnalysis.totalGzippedSize - BUDGETS.totalSize;
    log(`   ✗ Over budget by ${formatBytes(overage)}`, 'red');
    violations.push({
      check: 'Total Bundle Size',
      budget: formatBytes(BUDGETS.totalSize),
      actual: formatBytes(bundleAnalysis.totalGzippedSize),
      overage: formatBytes(overage),
    });
  } else {
    const remaining = BUDGETS.totalSize - bundleAnalysis.totalGzippedSize;
    log(`   ✓ Under budget by ${formatBytes(remaining)}`, 'green');
  }

  // 2. Largest File Check
  log('\n2. Checking largest file...', 'bold');

  if (bundleAnalysis.largestFile) {
    const largest = bundleAnalysis.largestFile;
    log(`   Largest file: ${largest.path}`, 'blue');
    log(`   Size (raw): ${formatBytes(largest.size)}`, 'blue');
    log(`   Size (gzipped): ${formatBytes(largest.gzipped)}`, 'blue');

    if (largest.gzipped > BUDGETS.largestFile) {
      const overage = largest.gzipped - BUDGETS.largestFile;
      log(`   ✗ Over budget by ${formatBytes(overage)}`, 'red');
      violations.push({
        check: 'Largest File',
        budget: formatBytes(BUDGETS.largestFile),
        actual: formatBytes(largest.gzipped),
        file: largest.path,
        overage: formatBytes(overage),
      });
    } else {
      const remaining = BUDGETS.largestFile - largest.gzipped;
      log(`   ✓ Under budget by ${formatBytes(remaining)}`, 'green');
    }
  } else {
    log(`   No files found in dist`, 'yellow');
  }

  // 3. Top 5 largest files
  if (bundleAnalysis.largestFiles.length > 0) {
    log('\n   Top 5 largest files (gzipped):', 'blue');
    for (let i = 0; i < Math.min(5, bundleAnalysis.largestFiles.length); i++) {
      const file = bundleAnalysis.largestFiles[i];
      log(`     ${i + 1}. ${file.path} - ${formatBytes(file.gzipped)}`, 'blue');
    }
  }

  // 4. Route Count
  log('\n3. Counting routes...', 'bold');
  const routeCount = countRoutes();
  log(`   Routes found: ${routeCount}`, 'blue');

  if (routeCount < BUDGETS.routeCount.min || routeCount > BUDGETS.routeCount.max) {
    log(`   ✗ Outside expected range (${BUDGETS.routeCount.min}-${BUDGETS.routeCount.max})`, 'red');
    violations.push({
      check: 'Route Count',
      budget: `${BUDGETS.routeCount.min}-${BUDGETS.routeCount.max}`,
      actual: routeCount,
    });
  } else {
    log(`   ✓ Within expected range`, 'green');
  }

  // 4. Build Time Check (note in output, but can't measure retroactively)
  log('\n4. Build time check...', 'bold');
  log('   Note: Build time must be measured externally', 'yellow');
  log(`   Budget: < ${BUDGETS.buildTime / 1000}s`, 'blue');
  log('   To measure: time npm run build', 'blue');

  // Report results
  const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(2);
  log(`\nValidation time: ${elapsedTime}s`, 'blue');

  if (violations.length === 0) {
    log('\n✓ All performance budgets met', 'green');
    log('');
    process.exit(0);
  } else {
    log(`\n✗ ${violations.length} budget violation(s):\n`, 'red');

    for (const violation of violations) {
      log(`  ${violation.check}:`, 'red');
      log(`    Budget: ${violation.budget}`, 'red');
      log(`    Actual: ${violation.actual}`, 'red');
      if (violation.overage) {
        log(`    Overage: ${violation.overage}`, 'red');
      }
      if (violation.file) {
        log(`    File: ${violation.file}`, 'red');
      }
      log('');
    }

    log(`Recommendation: Optimize assets, enable code splitting, or adjust budgets\n`, 'yellow');
    process.exit(1);
  }
}

main();
