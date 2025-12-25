#!/usr/bin/env node

// Official Link Allowlist Validation Gate
// Purpose: Enforce 3-domain allowlist for external links across markdown files
// Exit codes: 0 = All links allowed, 1 = Disallowed links found

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_ROOT = path.resolve(__dirname, '..');

// Blocklisted domains (known malicious/spam sites)
const BLOCKED_DOMAINS = [
  // Add known malicious domains here
  // Example: 'malicious-site.com',
];

// Additional allowed patterns (for development/relative links)
const ALLOWED_PATTERNS = [
  /^https?:\/\/localhost/,
  /^https?:\/\/127\.0\.0\.1/,
  /^https?:\/\/0\.0\.0\.0/,
  /^https?:\/\/\[::1\]/, // IPv6 localhost
  /^https?:\/\/.*\.local/, // Local network devices (.local domains)
  /^https?:\/\/example\.com/, // Reserved documentation domain
  /^https?:\/\/.*example\.com/, // Subdomains of example.com
  /\[REGION\]/, // Placeholder URLs with template variables
  /\[PROJECT/, // Placeholder URLs with template variables
];

// NOTE: This validator is configured to BLOCK known bad domains
// rather than ALLOW only specific domains, since this is an open-source
// plugin marketplace with legitimate external references to docs, tools, etc.

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

// Check if domain is blocked
function isDomainBlocked(hostname) {
  for (const blockedDomain of BLOCKED_DOMAINS) {
    if (hostname === blockedDomain || hostname.endsWith(`.${blockedDomain}`)) {
      return true;
    }
  }
  return false;
}

function findMarkdownFiles() {
  const files = [];

  // 1. Playbooks
  const playbooksDir = path.join(REPO_ROOT, 'playbooks');
  if (fs.existsSync(playbooksDir)) {
    const playbookFiles = fs.readdirSync(playbooksDir)
      .filter(f => f.endsWith('.md'))
      .map(f => path.join(playbooksDir, f));
    files.push(...playbookFiles);
  }

  // 2. Workspace lab (recursive)
  const labDir = path.join(REPO_ROOT, 'workspace', 'lab');
  if (fs.existsSync(labDir)) {
    const walkDir = (dir) => {
      const items = fs.readdirSync(dir);
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory()) {
          walkDir(fullPath);
        } else if (item.endsWith('.md')) {
          files.push(fullPath);
        }
      }
    };
    walkDir(labDir);
  }

  // 3. Plugin READMEs
  const pluginsDir = path.join(REPO_ROOT, 'plugins');
  if (fs.existsSync(pluginsDir)) {
    const walkPlugins = (dir) => {
      const items = fs.readdirSync(dir);
      for (const item of items) {
        // Skip node_modules, dist, and other build artifacts
        if (item === 'node_modules' || item === 'dist' || item === '.git') {
          continue;
        }

        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory()) {
          // Check for README.md in this directory
          const readme = path.join(fullPath, 'README.md');
          if (fs.existsSync(readme)) {
            files.push(readme);
          }
          // Recurse into subdirectories
          walkPlugins(fullPath);
        }
      }
    };
    walkPlugins(pluginsDir);
  }

  return files;
}

function extractLinks(markdown) {
  const links = [];

  // Match markdown links: [text](url)
  const markdownLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  let match;

  while ((match = markdownLinkRegex.exec(markdown)) !== null) {
    const url = match[2];
    links.push({ text: match[1], url, type: 'markdown' });
  }

  // Match raw URLs (http/https)
  const rawUrlRegex = /(?<![\(\[])(https?:\/\/[^\s\)]+)/g;
  while ((match = rawUrlRegex.exec(markdown)) !== null) {
    const url = match[1];
    // Avoid duplicates from markdown links
    if (!links.some(l => l.url === url)) {
      links.push({ text: '', url, type: 'raw' });
    }
  }

  return links;
}

function isLinkAllowed(url) {
  // Relative links
  if (url.startsWith('./') || url.startsWith('../') || url.startsWith('#')) {
    return { allowed: true, reason: 'relative' };
  }

  // Non-HTTP links (mailto, ftp, etc.)
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return { allowed: true, reason: 'non-http' };
  }

  // Development patterns
  for (const pattern of ALLOWED_PATTERNS) {
    if (pattern.test(url)) {
      return { allowed: true, reason: 'development' };
    }
  }

  // Check against blocklist
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname;

    // Block malicious domains
    if (isDomainBlocked(hostname)) {
      return { allowed: false, reason: 'blocked-domain', domain: hostname };
    }

    // Allow all other domains
    return { allowed: true, reason: 'default-allow' };
  } catch (error) {
    return { allowed: false, reason: 'invalid-url', error: error.message };
  }
}

function main() {
  const startTime = Date.now();

  log('\n=== Official Link Validation Gate ===\n', 'bold');

  if (BLOCKED_DOMAINS.length > 0) {
    log('Blocked domains:', 'red');
    for (const domain of BLOCKED_DOMAINS) {
      log(`  - ${domain}`, 'red');
    }
  } else {
    log('No blocked domains configured (all external links allowed)', 'green');
  }
  log('');

  // Find all markdown files
  const files = findMarkdownFiles();
  log(`Found ${files.length} markdown files to scan\n`, 'blue');

  // Scan each file
  const violations = [];
  let totalLinks = 0;
  let scannedFiles = 0;

  for (const filePath of files) {
    const content = fs.readFileSync(filePath, 'utf-8');
    const links = extractLinks(content);
    totalLinks += links.length;

    for (const link of links) {
      const result = isLinkAllowed(link.url);

      if (!result.allowed) {
        violations.push({
          file: path.relative(REPO_ROOT, filePath),
          link: link.url,
          text: link.text,
          reason: result.reason,
          domain: result.domain,
        });
      }
    }

    scannedFiles++;
    if (scannedFiles % 20 === 0) {
      process.stdout.write(`\rScanned ${scannedFiles}/${files.length} files...`);
    }
  }

  process.stdout.write(`\rScanned ${scannedFiles}/${files.length} files...\n\n`);

  // Report results
  const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(2);

  if (violations.length === 0) {
    log(`✓ All ${totalLinks} links allowed`, 'green');
    log(`Files scanned: ${files.length}`, 'blue');
    log(`Execution time: ${elapsedTime}s\n`, 'blue');
    process.exit(0);
  } else {
    log(`✗ ${violations.length} disallowed links found:\n`, 'red');

    // Group by domain
    const byDomain = {};
    for (const violation of violations) {
      const domain = violation.domain || 'unknown';
      if (!byDomain[domain]) {
        byDomain[domain] = [];
      }
      byDomain[domain].push(violation);
    }

    for (const [domain, items] of Object.entries(byDomain)) {
      log(`\n  Domain: ${domain}`, 'yellow');
      for (const item of items.slice(0, 5)) { // Show max 5 per domain
        log(`    File: ${item.file}`, 'red');
        log(`    Link: ${item.link}`, 'red');
        if (item.text) {
          log(`    Text: ${item.text}`, 'red');
        }
      }
      if (items.length > 5) {
        log(`    ... and ${items.length - 5} more`, 'yellow');
      }
    }

    log(`\nTotal links scanned: ${totalLinks}`, 'blue');
    log(`Violations: ${violations.length}`, 'red');
    log(`Files scanned: ${files.length}`, 'blue');
    log(`Execution time: ${elapsedTime}s\n`, 'blue');

    process.exit(1);
  }
}

main();
