#!/usr/bin/env node

// Route Crawl Validation Gate
// Purpose: Verify all expected routes exist in built marketplace/dist/ directory
// Exit codes: 0 = All routes found, 1 = Missing routes detected

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_ROOT = path.resolve(__dirname, '..');
const DIST_DIR = path.join(REPO_ROOT, 'marketplace', 'dist');
const CATALOG_PATH = path.join(REPO_ROOT, '.claude-plugin', 'marketplace.extended.json');

// ANSI color codes for output
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

function checkFileExists(routePath) {
  // Convert route to file path
  // / -> index.html
  // /plugins -> plugins/index.html
  // /plugins/foo -> plugins/foo/index.html

  let filePath;
  if (routePath === '/') {
    filePath = path.join(DIST_DIR, 'index.html');
  } else {
    const cleanPath = routePath.replace(/^\//, '');
    filePath = path.join(DIST_DIR, cleanPath, 'index.html');
  }

  return fs.existsSync(filePath);
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function generateExpectedRoutes() {
  const routes = new Set();

  // Core pages
  routes.add('/');
  routes.add('/plugins');
  routes.add('/skills');
  routes.add('/tools');
  routes.add('/sponsor');
  routes.add('/spotlight');
  routes.add('/skill-enhancers');

  // Legal pages
  routes.add('/terms');
  routes.add('/privacy');
  routes.add('/acceptable-use');

  // Learning lab (if exists)
  // Note: getting-started and built-system-summary were removed in PR #193 due to syntax errors
  const learningGuides = [
    'pattern-explained',
    'building-your-own',
    'debugging-tips',
    'orchestration-pattern',
    'visual-map',
  ];

  // Add learning routes only if dist has learning directory
  const learningDir = path.join(DIST_DIR, 'learning');
  if (fs.existsSync(learningDir)) {
    routes.add('/learning');
    for (const guide of learningGuides) {
      routes.add(`/learning/${guide}`);
    }
  }

  // Load catalog for dynamic routes
  if (!fs.existsSync(CATALOG_PATH)) {
    log(`Error: Catalog not found at ${CATALOG_PATH}`, 'red');
    process.exit(1);
  }

  const catalog = JSON.parse(fs.readFileSync(CATALOG_PATH, 'utf-8'));

  // Plugin detail pages
  for (const plugin of catalog.plugins) {
    const slug = slugify(plugin.name);
    routes.add(`/plugins/${slug}`);
  }

  // Skill detail pages (extract skills from plugins)
  for (const plugin of catalog.plugins) {
    if (plugin.components?.skills > 0) {
      // Skills are embedded in plugins, we'd need to parse each plugin
      // For now, we'll check if /skills route exists but not individual skills
      // since the marketplace structure may vary
    }
  }

  // Playbooks (check if they exist in dist)
  const playbooksDir = path.join(DIST_DIR, 'playbooks');
  if (fs.existsSync(playbooksDir)) {
    routes.add('/playbooks');
    const playbooks = fs.readdirSync(playbooksDir)
      .filter(item => {
        const itemPath = path.join(playbooksDir, item);
        return fs.statSync(itemPath).isDirectory();
      });

    for (const playbook of playbooks) {
      routes.add(`/playbooks/${playbook}`);
    }
  }

  return Array.from(routes).sort();
}

function main() {
  const startTime = Date.now();

  log('\n=== Route Crawl Validation Gate ===\n', 'bold');

  // Check if dist directory exists
  if (!fs.existsSync(DIST_DIR)) {
    log(`Error: Dist directory not found at ${DIST_DIR}`, 'red');
    log('Run "cd marketplace && npm run build" first', 'yellow');
    process.exit(1);
  }

  log(`Dist directory: ${DIST_DIR}`, 'blue');
  log(`Catalog: ${CATALOG_PATH}\n`, 'blue');

  // Generate expected routes
  const expectedRoutes = generateExpectedRoutes();
  log(`Expected routes: ${expectedRoutes.length}`, 'blue');

  // Check each route
  const missingRoutes = [];
  let checkedCount = 0;

  for (const route of expectedRoutes) {
    if (!checkFileExists(route)) {
      missingRoutes.push(route);
    }
    checkedCount++;

    // Progress indicator
    if (checkedCount % 50 === 0) {
      process.stdout.write(`\rChecked ${checkedCount}/${expectedRoutes.length} routes...`);
    }
  }

  process.stdout.write(`\rChecked ${checkedCount}/${expectedRoutes.length} routes...\n\n`);

  // Report results
  const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(2);

  if (missingRoutes.length === 0) {
    log(`✓ All ${expectedRoutes.length} routes found`, 'green');
    log(`Execution time: ${elapsedTime}s\n`, 'blue');
    process.exit(0);
  } else {
    log(`✗ ${missingRoutes.length} missing routes:\n`, 'red');

    for (const route of missingRoutes) {
      log(`  - ${route}`, 'red');
    }

    log(`\nFound: ${expectedRoutes.length - missingRoutes.length}/${expectedRoutes.length}`, 'yellow');
    log(`Missing: ${missingRoutes.length}/${expectedRoutes.length}`, 'red');
    log(`Execution time: ${elapsedTime}s\n`, 'blue');

    process.exit(1);
  }
}

main();
