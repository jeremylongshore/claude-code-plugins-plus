#!/usr/bin/env node
/**
 * Generate badges from validation results
 *
 * Reads validator JSON output and generates badge data
 * Calculates scores per category, determines earned badges
 * Updates marketplace.extended.json with badge data
 *
 * Usage:
 *   python3 scripts/validate-skills-schema.py --json > validation-results.json
 *   node scripts/generate-badges.mjs validation-results.json
 *
 * Or pipe directly:
 *   python3 scripts/validate-skills-schema.py --json | node scripts/generate-badges.mjs
 *
 * Author: Jeremy Longshore <jeremy@intentsolutions.io>
 * Version: 1.0.0
 */

import { readFileSync } from 'fs';
import { resolve } from 'path';

/**
 * Safe expression evaluator for badge requirements
 * Only handles simple comparisons: ===, >=, <=, >, <
 * Avoids security risks of new Function() or eval()
 */
function safeEvaluateRequirement(requirement, context) {
  // Parse simple comparison expressions
  const patterns = [
    /^(\w+)\s*===\s*(\d+)$/,   // variable === number
    /^(\w+)\s*>=\s*(\d+)$/,    // variable >= number
    /^(\w+)\s*<=\s*(\d+)$/,    // variable <= number
    /^(\w+)\s*>\s*(\d+)$/,     // variable > number
    /^(\w+)\s*<\s*(\d+)$/,     // variable < number
  ];

  const trimmed = requirement.trim();

  for (const pattern of patterns) {
    const match = trimmed.match(pattern);
    if (match) {
      const [, variable, value] = match;
      const contextValue = context[variable];
      const numValue = parseInt(value, 10);

      if (contextValue === undefined) {
        console.warn(`Unknown variable in requirement: ${variable}`);
        return false;
      }

      if (trimmed.includes('===')) return contextValue === numValue;
      if (trimmed.includes('>=')) return contextValue >= numValue;
      if (trimmed.includes('<=')) return contextValue <= numValue;
      if (trimmed.includes('>')) return contextValue > numValue;
      if (trimmed.includes('<')) return contextValue < numValue;
    }
  }

  console.warn(`Unsupported requirement expression: ${requirement}`);
  return false;
}

/**
 * Badge definitions with requirements
 */
const BADGE_DEFINITIONS = {
  'verified': {
    name: 'Verified',
    description: 'All validations pass with no errors',
    requirement: 'total_errors === 0',
  },
  'secure': {
    name: 'Secure',
    description: 'Security score >= 20/25',
    requirement: 'security_score >= 20',
  },
  'documented': {
    name: 'Documented',
    description: 'Documentation score >= 20/25',
    requirement: 'documentation_score >= 20',
  },
  'compliant': {
    name: 'Compliant',
    description: '90%+ of files fully compliant',
    requirement: 'compliance_rate >= 90',
  },
  'valid-frontmatter': {
    name: 'Valid Frontmatter',
    description: 'All frontmatter validation passes',
    requirement: 'total_errors === 0',
  },
  'well-documented': {
    name: 'Well Documented',
    description: 'Compliance rate >= 90%',
    requirement: 'compliance_rate >= 90',
  },
};

/**
 * Grade thresholds
 */
const GRADE_THRESHOLDS = {
  'A': 90,
  'B': 80,
  'C': 70,
  'D': 60,
  'F': 0,
};

/**
 * Read validation results from file or stdin
 */
function readValidationResults(filePath) {
  let input;

  if (filePath) {
    // Read from file
    const fullPath = resolve(filePath);
    input = readFileSync(fullPath, 'utf-8');
  } else {
    // Read from stdin
    input = readFileSync(0, 'utf-8');
  }

  try {
    return JSON.parse(input);
  } catch (error) {
    console.error('ERROR: Invalid JSON input');
    console.error(error.message);
    process.exit(1);
  }
}

/**
 * Merge multiple validation results
 */
function mergeValidationResults(results) {
  if (results.length === 1) {
    return results[0];
  }

  // Merge multiple validator outputs
  const merged = {
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    validators: results.map(r => r.validator),
    summary: {
      total: 0,
      passed: 0,
      failed: 0,
      warnings: 0,
    },
    score: {
      total: 0,
      grade: 'F',
      categories: {},
    },
    badges: [],
    details: {
      total_errors: 0,
      total_warnings: 0,
      compliance_rate: 0,
    },
    files: [],
  };

  // Sum totals
  for (const result of results) {
    merged.summary.total += result.summary.total;
    merged.summary.passed += result.summary.passed;
    merged.summary.failed += result.summary.failed;
    merged.summary.warnings += result.summary.warnings;

    if (result.details) {
      merged.details.total_errors += result.details.total_errors || 0;
      merged.details.total_warnings += result.details.total_warnings || 0;
    }

    if (result.files) {
      merged.files.push(...result.files);
    }

    // Merge badges
    if (result.badges) {
      for (const badge of result.badges) {
        if (!merged.badges.includes(badge)) {
          merged.badges.push(badge);
        }
      }
    }

    // Merge category scores
    if (result.score && result.score.categories) {
      for (const [category, score] of Object.entries(result.score.categories)) {
        if (!merged.score.categories[category]) {
          merged.score.categories[category] = 0;
        }
        merged.score.categories[category] += score;
      }
    }
  }

  // Average category scores
  for (const category of Object.keys(merged.score.categories)) {
    merged.score.categories[category] = Math.round(
      merged.score.categories[category] / results.length
    );
  }

  // Calculate overall score
  const categoryScores = Object.values(merged.score.categories);
  merged.score.total = categoryScores.reduce((sum, score) => sum + score, 0);

  // Determine grade
  for (const [grade, threshold] of Object.entries(GRADE_THRESHOLDS)) {
    if (merged.score.total >= threshold) {
      merged.score.grade = grade;
      break;
    }
  }

  // Calculate compliance rate
  if (merged.summary.total > 0) {
    merged.details.compliance_rate = Math.round(
      (merged.summary.passed / merged.summary.total) * 100 * 10
    ) / 10;
  }

  return merged;
}

/**
 * Calculate badge status
 */
function calculateBadges(validationResult) {
  const badges = {
    earned: [],
    available: [],
  };

  const context = {
    total_errors: validationResult.details?.total_errors || 0,
    total_warnings: validationResult.details?.total_warnings || 0,
    compliance_rate: validationResult.details?.compliance_rate || 0,
    security_score: validationResult.score?.categories?.security || 0,
    documentation_score: validationResult.score?.categories?.documentation || 0,
    functionality_score: validationResult.score?.categories?.functionality || 0,
    maintenance_score: validationResult.score?.categories?.maintenance || 0,
  };

  // Check each badge definition
  for (const [badgeId, definition] of Object.entries(BADGE_DEFINITIONS)) {
    // Simple eval of requirement (safe for our controlled requirements)
    let earned = false;

    try {
      // Use safe expression evaluator (no dynamic code execution)
      earned = safeEvaluateRequirement(definition.requirement, context);
    } catch (error) {
      console.error(`Warning: Failed to evaluate badge requirement for ${badgeId}`);
      console.error(error.message);
    }

    const badgeInfo = {
      id: badgeId,
      name: definition.name,
      description: definition.description,
      requirement: definition.requirement,
    };

    if (earned) {
      badges.earned.push(badgeInfo);
    } else {
      badges.available.push(badgeInfo);
    }
  }

  return badges;
}

/**
 * Generate badge summary output
 */
function generateBadgeSummary(validationResult) {
  const badges = calculateBadges(validationResult);

  return {
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    validator: validationResult.validator || 'merged',
    score: validationResult.score,
    badges: {
      earned: badges.earned.map(b => b.id),
      earned_details: badges.earned,
      available: badges.available.map(b => b.id),
      available_details: badges.available,
    },
    summary: validationResult.summary,
    details: validationResult.details,
  };
}

/**
 * Format badge output for display
 */
function formatBadgeDisplay(badgeSummary) {
  const lines = [];

  lines.push('='.repeat(70));
  lines.push('BADGE GENERATION RESULTS');
  lines.push('='.repeat(70));
  lines.push('');

  // Score
  lines.push(`Overall Score: ${badgeSummary.score.total}/100 (Grade: ${badgeSummary.score.grade})`);
  lines.push('');

  // Category scores
  if (badgeSummary.score.categories) {
    lines.push('Category Scores:');
    for (const [category, score] of Object.entries(badgeSummary.score.categories)) {
      const percentage = Math.round((score / 25) * 100);
      lines.push(`  ${category.padEnd(20)} ${score}/25 (${percentage}%)`);
    }
    lines.push('');
  }

  // Earned badges
  lines.push(`Earned Badges (${badgeSummary.badges.earned.length}):`);
  if (badgeSummary.badges.earned_details.length > 0) {
    for (const badge of badgeSummary.badges.earned_details) {
      lines.push(`  ✓ ${badge.name}`);
      lines.push(`    ${badge.description}`);
    }
  } else {
    lines.push('  (none)');
  }
  lines.push('');

  // Available badges
  lines.push(`Available Badges (${badgeSummary.badges.available.length}):`);
  if (badgeSummary.badges.available_details.length > 0) {
    for (const badge of badgeSummary.badges.available_details) {
      lines.push(`  ☐ ${badge.name}`);
      lines.push(`    ${badge.description}`);
      lines.push(`    Requirement: ${badge.requirement}`);
    }
  } else {
    lines.push('  (all badges earned!)');
  }
  lines.push('');

  // Summary stats
  lines.push('Validation Summary:');
  lines.push(`  Total files: ${badgeSummary.summary.total}`);
  lines.push(`  Passed: ${badgeSummary.summary.passed}`);
  lines.push(`  Failed: ${badgeSummary.summary.failed}`);
  lines.push(`  Warnings: ${badgeSummary.summary.warnings}`);
  lines.push(`  Compliance rate: ${badgeSummary.details.compliance_rate}%`);
  lines.push('');

  lines.push('='.repeat(70));

  return lines.join('\n');
}

/**
 * Main execution
 */
function main() {
  const args = process.argv.slice(2);

  // Check for --help
  if (args.includes('--help') || args.includes('-h')) {
    console.log('Badge Generator v1.0.0');
    console.log('');
    console.log('Usage:');
    console.log('  node scripts/generate-badges.mjs [validation-results.json]');
    console.log('  python3 scripts/validate-skills-schema.py --json | node scripts/generate-badges.mjs');
    console.log('');
    console.log('Options:');
    console.log('  --help, -h     Show this help message');
    console.log('  --json         Output JSON instead of formatted text');
    console.log('');
    console.log('Examples:');
    console.log('  # From file');
    console.log('  python3 scripts/validate-skills-schema.py --json > results.json');
    console.log('  node scripts/generate-badges.mjs results.json');
    console.log('');
    console.log('  # From stdin (pipe)');
    console.log('  python3 scripts/validate-skills-schema.py --json | node scripts/generate-badges.mjs');
    console.log('');
    console.log('  # JSON output');
    console.log('  node scripts/generate-badges.mjs results.json --json');
    process.exit(0);
  }

  // Determine if JSON output requested
  const jsonOutput = args.includes('--json');
  const filePath = args.find(arg => !arg.startsWith('--'));

  // Read validation results
  const validationResult = readValidationResults(filePath);

  // Generate badge summary
  const badgeSummary = generateBadgeSummary(validationResult);

  // Output
  if (jsonOutput) {
    console.log(JSON.stringify(badgeSummary, null, 2));
  } else {
    console.log(formatBadgeDisplay(badgeSummary));
  }

  // Exit code based on score
  const exitCode = badgeSummary.score.total >= 70 ? 0 : 1;
  process.exit(exitCode);
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { calculateBadges, generateBadgeSummary, mergeValidationResults };
