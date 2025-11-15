#!/usr/bin/env node

/**
 * Claude Plugin Validator
 *
 * Validates Claude Code plugins for completeness and best practices.
 * Can be run as standalone script or via npx.
 *
 * Usage:
 *   node validate-plugin.js /path/to/plugin
 *   npx claude-plugin-validator /path/to/plugin
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m'
};

class PluginValidator {
  constructor(pluginPath) {
    this.pluginPath = path.resolve(pluginPath);
    this.errors = [];
    this.warnings = [];
    this.passes = [];
    this.score = 0;
    this.maxScore = 0;
  }

  log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
  }

  error(message, points = 10) {
    this.errors.push(message);
    this.maxScore += points;
  }

  warning(message, points = 5) {
    this.warnings.push(message);
    this.maxScore += points;
  }

  pass(message, points = 10) {
    this.passes.push(message);
    this.score += points;
    this.maxScore += points;
  }

  checkFileExists(filename, required = true, points = 10) {
    const filePath = path.join(this.pluginPath, filename);
    const exists = fs.existsSync(filePath);

    if (exists) {
      this.pass(`✓ ${filename} exists`, points);
      return true;
    } else {
      if (required) {
        this.error(`✗ ${filename} missing (REQUIRED)`, points);
      } else {
        this.warning(`⚠ ${filename} missing (recommended)`, points);
      }
      return false;
    }
  }

  validateJSON(filename, schema = null) {
    const filePath = path.join(this.pluginPath, filename);

    if (!fs.existsSync(filePath)) {
      return false;
    }

    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const data = JSON.parse(content);

      if (filename === '.claude-plugin/plugin.json') {
        this.validatePluginManifest(data);
      }

      this.pass(`✓ ${filename} is valid JSON`, 5);
      return data;
    } catch (err) {
      this.error(`✗ ${filename} is invalid JSON: ${err.message}`, 10);
      return false;
    }
  }

  validatePluginManifest(data) {
    const required = ['name', 'version', 'description', 'author'];

    required.forEach(field => {
      if (!data[field]) {
        this.error(`✗ plugin.json missing required field: ${field}`, 5);
      } else {
        this.pass(`✓ plugin.json has ${field}`, 2);
      }
    });

    // Check version format
    if (data.version && !/^\d+\.\d+\.\d+$/.test(data.version)) {
      this.warning(`⚠ version should follow semver format (x.y.z)`, 3);
    }

    // Check for deprecated opus model
    if (JSON.stringify(data).includes('"opus"')) {
      this.error('✗ plugin.json contains deprecated "opus" model identifier (use "sonnet" or "haiku")', 10);
    }
  }

  validateSkills() {
    const skillsDir = path.join(this.pluginPath, 'skills');

    if (!fs.existsSync(skillsDir)) {
      this.warning('⚠ No skills directory found', 5);
      return;
    }

    const skillDirs = fs.readdirSync(skillsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);

    if (skillDirs.length === 0) {
      this.warning('⚠ Skills directory is empty', 5);
      return;
    }

    this.pass(`✓ Found ${skillDirs.length} skill(s)`, 5);

    skillDirs.forEach(skillName => {
      const skillFile = path.join(skillsDir, skillName, 'SKILL.md');

      if (!fs.existsSync(skillFile)) {
        this.error(`✗ Skill "${skillName}" missing SKILL.md`, 5);
        return;
      }

      const content = fs.readFileSync(skillFile, 'utf8');

      // Check for YAML frontmatter
      if (!content.startsWith('---')) {
        this.error(`✗ Skill "${skillName}" missing YAML frontmatter`, 5);
        return;
      }

      // Extract frontmatter
      const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
      if (!frontmatterMatch) {
        this.error(`✗ Skill "${skillName}" has invalid frontmatter`, 5);
        return;
      }

      const frontmatter = frontmatterMatch[1];

      // Check 2025 schema compliance
      const has2025Schema =
        frontmatter.includes('allowed-tools:') &&
        frontmatter.includes('version:');

      if (has2025Schema) {
        this.pass(`✓ Skill "${skillName}" complies with 2025 schema (allowed-tools + version)`, 5);
      } else {
        this.warning(`⚠ Skill "${skillName}" missing 2025 schema fields (allowed-tools, version)`, 5);
      }

      // Check for trigger phrases in description
      if (!frontmatter.includes('description:')) {
        this.error(`✗ Skill "${skillName}" missing description`, 5);
      } else {
        this.pass(`✓ Skill "${skillName}" has description`, 2);
      }
    });
  }

  validateScripts() {
    const scriptsDir = path.join(this.pluginPath, 'scripts');

    if (!fs.existsSync(scriptsDir)) {
      return; // Scripts are optional
    }

    const scripts = fs.readdirSync(scriptsDir)
      .filter(f => f.endsWith('.sh'));

    scripts.forEach(script => {
      const scriptPath = path.join(scriptsDir, script);
      const stats = fs.statSync(scriptPath);

      // Check executable bit
      const isExecutable = (stats.mode & 0o111) !== 0;

      if (isExecutable) {
        this.pass(`✓ Script ${script} is executable`, 2);
      } else {
        this.error(`✗ Script ${script} is not executable (chmod +x)`, 5);
      }

      // Check for dangerous patterns
      const content = fs.readFileSync(scriptPath, 'utf8');

      if (content.includes('rm -rf /')) {
        this.error(`✗ Script ${script} contains dangerous command: rm -rf /`, 20);
      }

      if (content.includes('eval(') || content.includes('eval ')) {
        this.warning(`⚠ Script ${script} uses eval() (potential security risk)`, 5);
      }
    });
  }

  checkSecrets() {
    const dangerous = [
      { pattern: /password\s*=\s*["'][^"']+["']/, msg: 'hardcoded password' },
      { pattern: /api[_-]?key\s*=\s*["'][^"']+["']/, msg: 'hardcoded API key' },
      { pattern: /secret\s*=\s*["'][^"']+["']/, msg: 'hardcoded secret' },
      { pattern: /AKIA[0-9A-Z]{16}/, msg: 'AWS access key' },
      { pattern: /-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----/, msg: 'private key' }
    ];

    const searchDirs = ['commands', 'agents', 'scripts', 'hooks'];
    let foundSecrets = false;

    searchDirs.forEach(dir => {
      const dirPath = path.join(this.pluginPath, dir);
      if (!fs.existsSync(dirPath)) return;

      const files = this.getAllFiles(dirPath);

      files.forEach(file => {
        const content = fs.readFileSync(file, 'utf8');

        dangerous.forEach(({ pattern, msg }) => {
          if (pattern.test(content)) {
            this.error(`✗ ${path.relative(this.pluginPath, file)} contains ${msg}`, 20);
            foundSecrets = true;
          }
        });
      });
    });

    if (!foundSecrets) {
      this.pass('✓ No hardcoded secrets detected', 10);
    }
  }

  getAllFiles(dir) {
    const files = [];

    const items = fs.readdirSync(dir, { withFileTypes: true });

    for (const item of items) {
      const fullPath = path.join(dir, item.name);

      if (item.isDirectory()) {
        files.push(...this.getAllFiles(fullPath));
      } else {
        files.push(fullPath);
      }
    }

    return files;
  }

  hasComponents() {
    const components = ['commands', 'agents', 'hooks', 'skills', 'scripts', 'mcp'];

    const found = components.filter(c =>
      fs.existsSync(path.join(this.pluginPath, c))
    );

    if (found.length === 0) {
      this.error('✗ No component directories found (commands, agents, hooks, skills, scripts, mcp)', 10);
    } else {
      this.pass(`✓ Has ${found.length} component(s): ${found.join(', ')}`, 10);
    }
  }

  validate() {
    this.log('\n' + '='.repeat(60), 'cyan');
    this.log(`🔍 Validating Plugin: ${path.basename(this.pluginPath)}`, 'bold');
    this.log('='.repeat(60) + '\n', 'cyan');

    // Check required files
    this.log('📄 Checking Required Files...', 'blue');
    this.checkFileExists('README.md', true, 10);
    this.checkFileExists('LICENSE', true, 10);
    this.checkFileExists('.claude-plugin/plugin.json', true, 10);

    // Validate JSONs
    this.log('\n📋 Validating Configuration Files...', 'blue');
    this.validateJSON('.claude-plugin/plugin.json');

    if (fs.existsSync(path.join(this.pluginPath, '.claude-plugin/hooks.json'))) {
      this.validateJSON('.claude-plugin/hooks.json');
    }

    // Check components
    this.log('\n🧩 Checking Plugin Components...', 'blue');
    this.hasComponents();
    this.validateSkills();
    this.validateScripts();

    // Security checks
    this.log('\n🔒 Security Checks...', 'blue');
    this.checkSecrets();

    // Generate report
    this.generateReport();
  }

  generateReport() {
    this.log('\n' + '='.repeat(60), 'cyan');
    this.log('📊 VALIDATION REPORT', 'bold');
    this.log('='.repeat(60), 'cyan');

    if (this.passes.length > 0) {
      this.log(`\n✅ PASSED (${this.passes.length})`, 'green');
      this.passes.forEach(p => this.log(`  ${p}`, 'green'));
    }

    if (this.warnings.length > 0) {
      this.log(`\n⚠️  WARNINGS (${this.warnings.length})`, 'yellow');
      this.warnings.forEach(w => this.log(`  ${w}`, 'yellow'));
    }

    if (this.errors.length > 0) {
      this.log(`\n❌ ERRORS (${this.errors.length})`, 'red');
      this.errors.forEach(e => this.log(`  ${e}`, 'red'));
    }

    // Calculate score
    const percentage = Math.round((this.score / this.maxScore) * 100);
    const grade =
      percentage >= 90 ? 'A' :
      percentage >= 80 ? 'B' :
      percentage >= 70 ? 'C' :
      percentage >= 60 ? 'D' : 'F';

    this.log('\n' + '='.repeat(60), 'cyan');
    this.log(`🎯 SCORE: ${this.score}/${this.maxScore} (${percentage}%) - Grade: ${grade}`,
      grade === 'A' ? 'green' : grade === 'F' ? 'red' : 'yellow');
    this.log('='.repeat(60) + '\n', 'cyan');

    if (percentage === 100) {
      this.log('🎉 Perfect! Your plugin is ready for publication!\n', 'green');
    } else if (percentage >= 80) {
      this.log('👍 Good! Address warnings for best practices.\n', 'yellow');
    } else if (percentage >= 60) {
      this.log('⚠️  Needs improvement. Fix errors before publishing.\n', 'yellow');
    } else {
      this.log('❌ Plugin is not ready. Please fix critical errors.\n', 'red');
    }

    process.exit(this.errors.length > 0 ? 1 : 0);
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(`
${colors.bold}Claude Plugin Validator${colors.reset}

Usage:
  node validate-plugin.js <path-to-plugin>
  npx claude-plugin-validator <path-to-plugin>

Examples:
  node validate-plugin.js ./my-plugin
  node validate-plugin.js /absolute/path/to/plugin

Checks:
  ✓ Required files (README.md, LICENSE, plugin.json)
  ✓ Valid JSON syntax
  ✓ 2025 schema compliance for Skills
  ✓ Script permissions (chmod +x)
  ✓ Security (no hardcoded secrets)
  ✓ Best practices
    `);
    process.exit(1);
  }

  const pluginPath = args[0];

  if (!fs.existsSync(pluginPath)) {
    console.error(`${colors.red}Error: Plugin directory not found: ${pluginPath}${colors.reset}`);
    process.exit(1);
  }

  const validator = new PluginValidator(pluginPath);
  validator.validate();
}

module.exports = PluginValidator;
