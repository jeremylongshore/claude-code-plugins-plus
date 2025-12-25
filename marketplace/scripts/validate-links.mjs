#!/usr/bin/env node
/**
 * CI GATE: Skill→Plugin Link Validation
 *
 * Validates that every skill's parent plugin link resolves to an existing plugin route
 * Ensures "Provided by" and "View Plugin" links never 404
 *
 * Exit codes:
 * - 0: All links valid
 * - 1: Broken links detected
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const SKILLS_CATALOG_PATH = join(__dirname, '../src/data/skills-catalog.json');
const DIST_PLUGINS_PATH = join(__dirname, '../dist/plugins');

console.log('🔗 Validating skill→plugin links...\n');

// Load skills catalog
let skillsCatalog;
try {
  skillsCatalog = JSON.parse(readFileSync(SKILLS_CATALOG_PATH, 'utf-8'));
} catch (error) {
  console.error('❌ Failed to load skills catalog:', error.message);
  process.exit(1);
}

// Check if dist/plugins exists
if (!existsSync(DIST_PLUGINS_PATH)) {
  console.error('❌ dist/plugins/ directory not found. Did you run the build?');
  process.exit(1);
}

console.log(`📊 Statistics:`);
console.log(`   Total skills: ${skillsCatalog.count}`);
console.log(`   Validating parent plugin links...\n`);

// Validate each skill's parent plugin link
let brokenLinks = [];
let errors = 0;

for (const skill of skillsCatalog.skills) {
  if (!skill.parentPlugin || !skill.parentPlugin.name) {
    brokenLinks.push({
      skill: skill.name,
      slug: skill.slug,
      issue: 'Missing parentPlugin.name',
      expectedLink: 'N/A'
    });
    errors++;
    continue;
  }

  const parentPluginName = skill.parentPlugin.name;
  const expectedRoute = join(DIST_PLUGINS_PATH, parentPluginName, 'index.html');

  if (!existsSync(expectedRoute)) {
    brokenLinks.push({
      skill: skill.name,
      slug: skill.slug,
      parentPlugin: parentPluginName,
      expectedRoute: `/plugins/${parentPluginName}/`,
      issue: 'Plugin route does not exist'
    });
    errors++;
  }
}

// Report results
if (brokenLinks.length > 0) {
  console.error(`❌ ${brokenLinks.length} skill(s) have broken plugin links:\n`);
  brokenLinks.forEach(({ skill, slug, parentPlugin, expectedRoute, issue }) => {
    console.error(`   • Skill: ${skill} (/skills/${slug}/)`);
    if (parentPlugin) {
      console.error(`     Parent Plugin: ${parentPlugin}`);
      console.error(`     Expected Route: ${expectedRoute}`);
    }
    console.error(`     Issue: ${issue}\n`);
  });

  console.error(`\n❌ Link validation FAILED with ${errors} error(s)`);
  process.exit(1);
}

console.log(`✅ All ${skillsCatalog.count} skill→plugin links validated successfully!\n`);
process.exit(0);
