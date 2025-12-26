#!/usr/bin/env node

/**
 * Package Manager Enforcement Script
 *
 * Ensures pnpm-only usage across the repository.
 * Runs in CI to prevent regression to npm/yarn/bun.
 *
 * Exit codes:
 *   0 = All checks passed
 *   1 = Policy violations found
 */

import { readFileSync, readdirSync, statSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ANSI colors
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const RESET = '\x1b[0m';

let violations = 0;

console.log(`\n${GREEN}🔍 Package Manager Policy Enforcement${RESET}\n`);

/**
 * Check 1: Detect forbidden lockfiles
 */
function checkForbiddenLockfiles() {
  console.log('📦 Checking for forbidden lockfiles...');

  const forbidden = [
    'package-lock.json',
    'yarn.lock',
    'bun.lockb',
    'bun.lock'
  ];

  const found = [];

  function isAllowedLockfile(relPath, filename) {
    if (filename === 'package-lock.json' && relPath === join('marketplace', 'package-lock.json')) {
      const marketplacePkg = join(ROOT, 'marketplace', 'package.json');
      return existsSync(marketplacePkg);
    }
    return false;
  }

  function searchDirectory(dir, relativePath = '') {
    const entries = readdirSync(dir);

    for (const entry of entries) {
      const fullPath = join(dir, entry);
      const relPath = join(relativePath, entry);

      // Skip node_modules, .git, backups, dist, build
      if (entry === 'node_modules' || entry === '.git' || entry === 'backups' ||
          entry === 'dist' || entry === 'build' || entry === '.next') {
        continue;
      }

      const stat = statSync(fullPath);

      if (stat.isDirectory()) {
        searchDirectory(fullPath, relPath);
      } else if (forbidden.includes(entry)) {
        if (!isAllowedLockfile(relPath, entry)) {
          found.push(relPath);
        }
      }
    }
  }

  searchDirectory(ROOT);

  if (found.length > 0) {
    console.log(`${RED}❌ Found forbidden lockfiles:${RESET}`);
    found.forEach(file => console.log(`   ${RED}• ${file}${RESET}`));
    console.log(`\n${YELLOW}Fix: Remove these files and run 'pnpm install'${RESET}`);
    violations += found.length;
  } else {
    console.log(`${GREEN}✓ No forbidden lockfiles${RESET}`);
  }
}

/**
 * Check 2: Verify pnpm-lock.yaml exists
 */
function checkPnpmLockfile() {
  console.log('\n📦 Checking for pnpm-lock.yaml...');

  const lockfilePath = join(ROOT, 'pnpm-lock.yaml');

  if (!existsSync(lockfilePath)) {
    console.log(`${RED}❌ pnpm-lock.yaml not found${RESET}`);
    console.log(`${YELLOW}Fix: Run 'pnpm install' to generate lockfile${RESET}`);
    violations++;
  } else {
    console.log(`${GREEN}✓ pnpm-lock.yaml exists${RESET}`);
  }
}

/**
 * Check 3: Verify packageManager field in root package.json
 */
function checkPackageManagerField() {
  console.log('\n📦 Checking packageManager field...');

  const pkgPath = join(ROOT, 'package.json');

  if (!existsSync(pkgPath)) {
    console.log(`${RED}❌ package.json not found${RESET}`);
    violations++;
    return;
  }

  const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));

  if (!pkg.packageManager) {
    console.log(`${RED}❌ Missing "packageManager" field in package.json${RESET}`);
    console.log(`${YELLOW}Fix: Add "packageManager": "pnpm@9.15.9" to package.json${RESET}`);
    violations++;
  } else if (!pkg.packageManager.startsWith('pnpm@')) {
    console.log(`${RED}❌ packageManager is not pnpm: ${pkg.packageManager}${RESET}`);
    console.log(`${YELLOW}Fix: Change to "packageManager": "pnpm@9.15.9"${RESET}`);
    violations++;
  } else {
    console.log(`${GREEN}✓ packageManager set to ${pkg.packageManager}${RESET}`);
  }
}

/**
 * Check 4: Scan workflows for forbidden package manager commands
 */
function checkWorkflows() {
  console.log('\n📦 Checking GitHub Actions workflows...');

  const workflowsDir = join(ROOT, '.github', 'workflows');

  if (!existsSync(workflowsDir)) {
    console.log(`${YELLOW}⚠ No .github/workflows directory${RESET}`);
    return;
  }

  const workflows = readdirSync(workflowsDir).filter(f => f.endsWith('.yml') || f.endsWith('.yaml'));

  const forbiddenPatterns = [
    /^\s*run:\s*npm install(?!\s*#)/m,  // npm install (not in comment)
    /^\s*run:\s*yarn install(?!\s*#)/m, // yarn install (not in comment)
    /^\s*run:\s*bun install(?!\s*#)/m,  // bun install (not in comment)
  ];

  // Exceptions: workflows that intentionally test package managers
  const exceptions = ['cli-test.yml']; // This workflow tests npm/bun/pnpm compatibility

  for (const workflow of workflows) {
    if (exceptions.includes(workflow)) {
      continue; // Skip compatibility test workflows
    }

    const content = readFileSync(join(workflowsDir, workflow), 'utf-8');

    for (const pattern of forbiddenPatterns) {
      if (pattern.test(content)) {
        console.log(`${RED}❌ ${workflow} uses forbidden package manager${RESET}`);
        console.log(`   ${YELLOW}Found: ${content.match(pattern)[0].trim()}${RESET}`);
        console.log(`   ${YELLOW}Fix: Use 'pnpm install --frozen-lockfile'${RESET}`);
        violations++;
      }
    }
  }

  console.log(`${GREEN}✓ Workflows checked (${workflows.length} files)${RESET}`);
}

/**
 * Check 5: Verify pnpm workspace configuration
 */
function checkWorkspaceConfig() {
  console.log('\n📦 Checking pnpm-workspace.yaml...');

  const workspacePath = join(ROOT, 'pnpm-workspace.yaml');

  if (!existsSync(workspacePath)) {
    console.log(`${RED}❌ pnpm-workspace.yaml not found${RESET}`);
    console.log(`${YELLOW}Fix: Create pnpm-workspace.yaml with workspace packages${RESET}`);
    violations++;
  } else {
    const content = readFileSync(workspacePath, 'utf-8');
    if (!content.includes('packages:')) {
      console.log(`${RED}❌ pnpm-workspace.yaml missing 'packages:' field${RESET}`);
      violations++;
    } else {
      console.log(`${GREEN}✓ pnpm-workspace.yaml configured${RESET}`);
    }
  }
}

/**
 * Main execution
 */
function main() {
  checkForbiddenLockfiles();
  checkPnpmLockfile();
  checkPackageManagerField();
  checkWorkflows();
  checkWorkspaceConfig();

  console.log('\n' + '─'.repeat(60));

  if (violations > 0) {
    console.log(`\n${RED}❌ ${violations} policy violation(s) found${RESET}`);
    console.log(`\nSee 000-docs/Package-Policy.md for details.\n`);
    process.exit(1);
  } else {
    console.log(`\n${GREEN}✅ All package manager checks passed${RESET}\n`);
    process.exit(0);
  }
}

main();
