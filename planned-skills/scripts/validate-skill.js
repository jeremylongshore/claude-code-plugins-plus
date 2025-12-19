#!/usr/bin/env node
/**
 * Skill Validator
 *
 * Validates SKILL.md files against Anthropic and Enterprise standards
 *
 * Usage:
 *   node validate-skill.js path/to/SKILL.md
 *   node validate-skill.js --batch 001
 *   node validate-skill.js --all
 */

const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

// Validation rules
const REQUIRED_FIELDS = ['name', 'description'];
const ENTERPRISE_FIELDS = ['allowed-tools', 'version', 'author', 'license'];
const MAX_NAME_LENGTH = 64;
const MAX_DESCRIPTION_LENGTH = 1024;
const VALID_TOOLS = [
  'Read', 'Write', 'Edit', 'Grep', 'Glob', 'Bash',
  'WebFetch', 'WebSearch', 'Task', 'TodoWrite'
];

function validateSkill(filePath) {
  const errors = [];
  const warnings = [];

  // Read file
  let content;
  try {
    content = fs.readFileSync(filePath, 'utf8');
  } catch (error) {
    return { valid: false, errors: [`Cannot read file: ${error.message}`], warnings: [] };
  }

  // Parse YAML frontmatter
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!frontmatterMatch) {
    return { valid: false, errors: ['Missing YAML frontmatter'], warnings: [] };
  }

  let frontmatter;
  try {
    frontmatter = yaml.parse(frontmatterMatch[1]);
  } catch (error) {
    return { valid: false, errors: [`Invalid YAML: ${error.message}`], warnings: [] };
  }

  // Check required fields
  for (const field of REQUIRED_FIELDS) {
    if (!frontmatter[field]) {
      errors.push(`Missing required field: ${field}`);
    }
  }

  // Check enterprise fields
  for (const field of ENTERPRISE_FIELDS) {
    if (!frontmatter[field]) {
      warnings.push(`Missing enterprise field: ${field}`);
    }
  }

  // Validate name
  if (frontmatter.name) {
    if (frontmatter.name.length > MAX_NAME_LENGTH) {
      errors.push(`Name exceeds ${MAX_NAME_LENGTH} characters`);
    }
    if (!/^[a-z0-9-]+$/.test(frontmatter.name)) {
      errors.push('Name must be kebab-case (lowercase letters, numbers, hyphens)');
    }
    if (frontmatter.name.includes('anthropic') || frontmatter.name.includes('claude')) {
      errors.push('Name contains reserved word (anthropic/claude)');
    }
  }

  // Validate description
  if (frontmatter.description) {
    const desc = typeof frontmatter.description === 'string'
      ? frontmatter.description
      : frontmatter.description.toString();
    if (desc.length > MAX_DESCRIPTION_LENGTH) {
      errors.push(`Description exceeds ${MAX_DESCRIPTION_LENGTH} characters`);
    }
    if (!desc.match(/Use when|Trigger with/i)) {
      warnings.push('Description should include trigger phrases');
    }
  }

  // Validate allowed-tools
  if (frontmatter['allowed-tools']) {
    const tools = Array.isArray(frontmatter['allowed-tools'])
      ? frontmatter['allowed-tools']
      : frontmatter['allowed-tools'].split(',').map(t => t.trim());

    for (const tool of tools) {
      const baseTool = tool.split('(')[0];
      if (!VALID_TOOLS.includes(baseTool)) {
        warnings.push(`Unknown tool: ${tool}`);
      }
    }
  }

  // Validate version
  if (frontmatter.version && !/^\d+\.\d+\.\d+$/.test(frontmatter.version)) {
    errors.push('Version must be semver format (X.Y.Z)');
  }

  // Check for body content
  const body = content.replace(/^---\n[\s\S]*?\n---\n?/, '').trim();
  if (body.length < 100) {
    warnings.push('Skill body seems too short');
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

function validateBatch(batchNumber) {
  const batchDir = path.join(__dirname, '..', 'batches', `batch-${batchNumber.toString().padStart(3, '0')}`);
  const outputDir = path.join(batchDir, 'output');
  const validatedDir = path.join(batchDir, 'validated');

  if (!fs.existsSync(outputDir)) {
    console.error(`Batch directory not found: ${outputDir}`);
    return;
  }

  const files = fs.readdirSync(outputDir).filter(f => f.endsWith('.md'));
  let passed = 0;
  let failed = 0;

  for (const file of files) {
    const filePath = path.join(outputDir, file);
    const result = validateSkill(filePath);

    if (result.valid) {
      passed++;
      console.log(`✓ ${file}`);
      // Copy to validated directory
      fs.copyFileSync(filePath, path.join(validatedDir, file));
    } else {
      failed++;
      console.log(`✗ ${file}`);
      result.errors.forEach(e => console.log(`  ERROR: ${e}`));
    }

    result.warnings.forEach(w => console.log(`  WARNING: ${w}`));
  }

  console.log(`\nValidation complete: ${passed} passed, ${failed} failed`);
}

// CLI handling
const args = process.argv.slice(2);

if (args.length === 0 || args.includes('--help')) {
  console.log(`
Skill Validator

Usage:
  node validate-skill.js <path-to-skill.md>
  node validate-skill.js --batch <number>
  node validate-skill.js --all

Options:
  --batch   Validate all skills in a batch
  --all     Validate all batches
  --help    Show this help
`);
  process.exit(0);
}

if (args[0] === '--batch') {
  validateBatch(parseInt(args[1]));
} else if (args[0] === '--all') {
  // TODO: Implement all batches validation
  console.log('Validating all batches...');
} else {
  const result = validateSkill(args[0]);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.valid ? 0 : 1);
}
