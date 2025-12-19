#!/usr/bin/env node
/**
 * Skill Deployer
 *
 * Deploys validated skills from batches to production /skills/ directory
 *
 * Usage:
 *   node deploy-skills.js --batch 001
 *   node deploy-skills.js --all
 *   node deploy-skills.js --dry-run
 */

const fs = require('fs');
const path = require('path');

const BATCHES_PATH = path.join(__dirname, '..', 'batches');
const PRODUCTION_PATH = path.join(__dirname, '..', '..', 'skills');
const CATEGORIES_PATH = path.join(__dirname, '..', 'categories');

function getCategoryForSkill(skillName) {
  // Search all category configs for this skill
  const categories = fs.readdirSync(CATEGORIES_PATH);

  for (const category of categories) {
    const configPath = path.join(CATEGORIES_PATH, category, 'category-config.json');
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      if (config.skills && config.skills.includes(skillName)) {
        return {
          id: config.id,
          folder: config.id.replace(/^\d+-/, '') // Remove number prefix
        };
      }
    }
  }

  return null;
}

function deploySkill(skillFile, sourceDir, dryRun = false) {
  const skillName = path.basename(skillFile, '.md');
  const category = getCategoryForSkill(skillName);

  if (!category) {
    console.log(`  ⚠ Cannot find category for: ${skillName}`);
    return false;
  }

  const targetDir = path.join(PRODUCTION_PATH, category.folder, skillName);
  const targetFile = path.join(targetDir, 'SKILL.md');

  if (dryRun) {
    console.log(`  [DRY RUN] Would deploy: ${skillName} → ${targetDir}`);
    return true;
  }

  // Create target directory
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  // Copy file
  const sourceFile = path.join(sourceDir, skillFile);
  fs.copyFileSync(sourceFile, targetFile);

  console.log(`  ✓ Deployed: ${skillName} → ${category.folder}/`);
  return true;
}

function deployBatch(batchNumber, dryRun = false) {
  const batchDir = path.join(BATCHES_PATH, `batch-${batchNumber.toString().padStart(3, '0')}`);
  const validatedDir = path.join(batchDir, 'validated');

  if (!fs.existsSync(validatedDir)) {
    console.error(`No validated skills found in batch ${batchNumber}`);
    return;
  }

  const files = fs.readdirSync(validatedDir).filter(f => f.endsWith('.md'));

  if (files.length === 0) {
    console.log(`No skills to deploy in batch ${batchNumber}`);
    return;
  }

  console.log(`Deploying batch ${batchNumber} (${files.length} skills)...`);

  let deployed = 0;
  let failed = 0;

  for (const file of files) {
    if (deploySkill(file, validatedDir, dryRun)) {
      deployed++;
    } else {
      failed++;
    }
  }

  console.log(`\nDeployment complete: ${deployed} deployed, ${failed} failed`);

  // Update batch metadata
  if (!dryRun) {
    const metadataPath = path.join(batchDir, 'metadata.json');
    let metadata = {};
    if (fs.existsSync(metadataPath)) {
      metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
    }
    metadata.deployedAt = new Date().toISOString();
    metadata.deployedCount = deployed;
    metadata.status = 'deployed';
    fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
  }
}

// CLI handling
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');

if (args.length === 0 || args.includes('--help')) {
  console.log(`
Skill Deployer

Usage:
  node deploy-skills.js --batch <number> [--dry-run]
  node deploy-skills.js --all [--dry-run]

Options:
  --batch     Deploy skills from a specific batch
  --all       Deploy all validated batches
  --dry-run   Show what would be deployed without making changes
  --help      Show this help

Production directory: ${PRODUCTION_PATH}
`);
  process.exit(0);
}

// Ensure production directory exists
if (!dryRun && !fs.existsSync(PRODUCTION_PATH)) {
  fs.mkdirSync(PRODUCTION_PATH, { recursive: true });
  console.log(`Created production directory: ${PRODUCTION_PATH}`);
}

if (args.includes('--batch')) {
  const batchIdx = args.indexOf('--batch');
  deployBatch(parseInt(args[batchIdx + 1]), dryRun);
} else if (args.includes('--all')) {
  const batches = fs.readdirSync(BATCHES_PATH)
    .filter(d => d.startsWith('batch-'))
    .sort();

  for (const batch of batches) {
    const batchNumber = parseInt(batch.replace('batch-', ''));
    deployBatch(batchNumber, dryRun);
  }
}
