#!/usr/bin/env node
/**
 * Update README.md badges based on validation output
 *
 * Auto-updates badges in README.md:
 * - Plugin count
 * - Skill count
 * - Compliance badges
 * - Quality score badges
 *
 * Usage:
 *   node scripts/update-readme-badges.mjs [--dry-run]
 *
 * Or with validation results:
 *   python3 scripts/validate-skills-schema.py --json | \
 *     node scripts/generate-badges.mjs --json | \
 *     node scripts/update-readme-badges.mjs
 *
 * Author: Jeremy Longshore <jeremy@intentsolutions.io>
 * Version: 1.0.0
 */

import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(__dirname, '..');

/**
 * Badge templates using shields.io
 */
const BADGE_TEMPLATES = {
  plugins: (count) =>
    `![Plugins](https://img.shields.io/badge/plugins-${count}-blue)`,

  skills: (count) =>
    `![Skills](https://img.shields.io/badge/skills-${count}-green)`,

  compliance: (rate) => {
    const color = rate >= 90 ? 'brightgreen' : rate >= 70 ? 'yellow' : 'red';
    return `![Compliance](https://img.shields.io/badge/compliance-${rate}%25-${color})`;
  },

  score: (score, grade) => {
    const color = score >= 90 ? 'brightgreen' : score >= 70 ? 'yellow' : 'red';
    return `![Quality](https://img.shields.io/badge/quality-${score}%2F100%20(${grade})-${color})`;
  },

  verified: (earned) => {
    if (earned) {
      return `![Verified](https://img.shields.io/badge/verified-✓-brightgreen)`;
    } else {
      return `![Verified](https://img.shields.io/badge/verified-✗-lightgrey)`;
    }
  },

  secure: (earned) => {
    if (earned) {
      return `![Secure](https://img.shields.io/badge/secure-✓-brightgreen)`;
    } else {
      return `![Secure](https://img.shields.io/badge/secure-✗-lightgrey)`;
    }
  },

  documented: (earned) => {
    if (earned) {
      return `![Documented](https://img.shields.io/badge/documented-✓-brightgreen)`;
    } else {
      return `![Documented](https://img.shields.io/badge/documented-✗-lightgrey)`;
    }
  },
};

/**
 * Read marketplace catalog to get plugin/skill counts
 */
function getMarketplaceCounts() {
  try {
    const catalogPath = resolve(REPO_ROOT, '.claude-plugin/marketplace.extended.json');
    const catalog = JSON.parse(readFileSync(catalogPath, 'utf-8'));

    const pluginCount = catalog.plugins?.length || 0;

    // Count skills across all plugins
    let skillCount = 0;
    for (const plugin of catalog.plugins || []) {
      if (plugin.components?.skills && Array.isArray(plugin.components.skills)) {
        skillCount += plugin.components.skills.length;
      } else if (typeof plugin.components?.skills === 'number') {
        // Handle case where skills is a count number
        skillCount += plugin.components.skills;
      }
    }

    return { pluginCount, skillCount };
  } catch (error) {
    console.error('Warning: Could not read marketplace catalog:', error.message);
    return { pluginCount: 0, skillCount: 0 };
  }
}

/**
 * Read badge summary from stdin or file
 */
function readBadgeSummary(filePath) {
  let input;

  if (filePath) {
    const fullPath = resolve(filePath);
    try {
      input = readFileSync(fullPath, 'utf-8');
    } catch (error) {
      console.error(`Warning: Could not read file ${filePath}:`, error.message);
      return null;
    }
  } else if (!process.stdin.isTTY) {
    // Read from stdin if available
    try {
      input = readFileSync(0, 'utf-8');
    } catch (error) {
      // stdin not available or empty - use defaults
      return null;
    }
  } else {
    // No input provided - use defaults
    return null;
  }

  // Check if input is empty
  if (!input || input.trim().length === 0) {
    return null;
  }

  try {
    return JSON.parse(input);
  } catch (error) {
    console.error('Warning: Invalid JSON input, using defaults');
    return null;
  }
}

/**
 * Generate badge section content
 */
function generateBadgeSection(badgeSummary, marketplaceCounts) {
  const badges = [];

  // Plugin and skill counts (from marketplace catalog)
  badges.push(BADGE_TEMPLATES.plugins(marketplaceCounts.pluginCount));
  badges.push(BADGE_TEMPLATES.skills(marketplaceCounts.skillCount));

  // Validation badges (from badge summary if available)
  if (badgeSummary) {
    const complianceRate = Math.round(badgeSummary.details?.compliance_rate || 0);
    badges.push(BADGE_TEMPLATES.compliance(complianceRate));

    const score = badgeSummary.score?.total || 0;
    const grade = badgeSummary.score?.grade || 'F';
    badges.push(BADGE_TEMPLATES.score(score, grade));

    // Individual badges
    const earnedBadges = new Set(badgeSummary.badges?.earned || []);
    badges.push(BADGE_TEMPLATES.verified(earnedBadges.has('verified')));
    badges.push(BADGE_TEMPLATES.secure(earnedBadges.has('secure')));
    badges.push(BADGE_TEMPLATES.documented(earnedBadges.has('documented')));
  }

  return badges.join(' ');
}

/**
 * Update README.md badges section
 */
function updateReadmeBadges(dryRun = false) {
  const readmePath = resolve(REPO_ROOT, 'README.md');

  let content;
  try {
    content = readFileSync(readmePath, 'utf-8');
  } catch (error) {
    console.error(`ERROR: Could not read ${readmePath}`);
    console.error(error.message);
    process.exit(1);
  }

  // Get marketplace counts
  const marketplaceCounts = getMarketplaceCounts();

  // Try to read badge summary from stdin
  const badgeSummary = readBadgeSummary();

  // Generate new badge section
  const newBadges = generateBadgeSection(badgeSummary, marketplaceCounts);

  // Find and replace badges section
  // Look for the section with shields.io badges (they're on separate lines in this repo)

  // Find the badge section markers
  const lines = content.split('\n');
  let badgeStartLine = -1;
  let badgeEndLine = -1;

  // Find first badge line
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('img.shields.io/badge/')) {
      badgeStartLine = i;
      break;
    }
  }

  if (badgeStartLine === -1) {
    console.error('ERROR: Could not find any shields.io badges in README.md');
    process.exit(1);
  }

  // Find where badges end (first non-badge, non-empty line)
  for (let i = badgeStartLine; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line && !line.includes('img.shields.io') && !line.startsWith('[![')) {
      badgeEndLine = i;
      break;
    }
  }

  if (badgeEndLine === -1) {
    badgeEndLine = lines.length;
  }

  // Get indentation from first badge line
  const indentation = lines[badgeStartLine].match(/^(\s*)/)[1];

  // Count the old badges
  const oldBadgeCount = badgeEndLine - badgeStartLine;

  // Create new content
  const beforeBadges = lines.slice(0, badgeStartLine).join('\n');
  const afterBadges = lines.slice(badgeEndLine).join('\n');

  // Split new badges into individual lines (they're space-separated)
  const badgeLines = newBadges.split(' ').map(badge => `${indentation}${badge}`).join('\n');

  const updatedContent = `${beforeBadges}\n${badgeLines}\n${afterBadges}`;

  if (dryRun) {
    console.log('DRY RUN - Would update badges:');
    console.log('');
    console.log(`Current badges (${oldBadgeCount} lines):`);
    for (let i = badgeStartLine; i < Math.min(badgeEndLine, badgeStartLine + 5); i++) {
      console.log(lines[i]);
    }
    if (oldBadgeCount > 5) {
      console.log(`... and ${oldBadgeCount - 5} more`);
    }
    console.log('');
    console.log('New badges:');
    console.log(badgeLines);
  } else {
    writeFileSync(readmePath, updatedContent, 'utf-8');
    console.log('✓ Updated README.md badges');
    console.log('');
    console.log(`Replaced ${oldBadgeCount} badge lines with ${newBadges.split(' ').length} new badges`);
    console.log('');
    console.log('New badges:');
    console.log(badgeLines);
  }
}

/**
 * Main execution
 */
function main() {
  const args = process.argv.slice(2);

  // Check for --help
  if (args.includes('--help') || args.includes('-h')) {
    console.log('README Badge Updater v1.0.0');
    console.log('');
    console.log('Usage:');
    console.log('  node scripts/update-readme-badges.mjs [--dry-run]');
    console.log('');
    console.log('Options:');
    console.log('  --help, -h     Show this help message');
    console.log('  --dry-run      Show what would be changed without writing');
    console.log('');
    console.log('Examples:');
    console.log('  # Update badges using marketplace catalog only');
    console.log('  node scripts/update-readme-badges.mjs');
    console.log('');
    console.log('  # Update badges with validation results');
    console.log('  python3 scripts/validate-skills-schema.py --json | \\');
    console.log('    node scripts/generate-badges.mjs --json | \\');
    console.log('    node scripts/update-readme-badges.mjs');
    console.log('');
    console.log('  # Preview changes');
    console.log('  node scripts/update-readme-badges.mjs --dry-run');
    process.exit(0);
  }

  const dryRun = args.includes('--dry-run');

  updateReadmeBadges(dryRun);
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { generateBadgeSection, updateReadmeBadges };
