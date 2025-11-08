# Skills Powerkit

**The ultimate plugin management toolkit for the claude-code-plugins marketplace** - Includes 5 Agent Skills that automatically manage plugin development, validation, auditing, and marketplace updates.

[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)](.)
[![Skills](https://img.shields.io/badge/skills-5-blue)](.)
[![Type](https://img.shields.io/badge/type-meta--plugin-purple)](.)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What Is This?

**Skills Powerkit is a "meta-plugin"** - a plugin specifically designed to help you CREATE, VALIDATE, AUDIT, and MANAGE plugins within the claude-code-plugins repository.

**Think of it as your AI assistant FOR building plugins** - it knows the repository structure, standards, and workflows, and automatically handles all the tedious tasks.

---

## 5 Included Agent Skills

### 1. 🛠️ Plugin Creator
**Automatically scaffolds new plugins from scratch**

**Activates when you say:**
- "Create a new plugin"
- "Scaffold a plugin for [purpose]"
- "Add new plugin to marketplace"

**What it does:**
- Creates complete directory structure
- Generates plugin.json with proper schema
- Creates README, LICENSE, component files
- Adds entry to marketplace catalog
- Syncs marketplace.json
- Validates everything

**Example:** "Create a security plugin called 'owasp-scanner' with commands"

---

### 2. ✅ Plugin Validator
**Automatically validates plugin structure and compliance**

**Activates when you say:**
- "Validate this plugin"
- "Check plugin for errors"
- "Is my plugin ready to commit?"

**What it does:**
- Validates plugin.json schema
- Checks required files exist
- Validates markdown frontmatter
- Verifies script permissions
- Checks marketplace compliance
- Runs comprehensive validation suite

**Example:** "Validate the skills-powerkit plugin"

---

### 3. 📦 Marketplace Manager
**Automatically manages marketplace catalog and syncing**

**Activates when you say:**
- "Add plugin to marketplace"
- "Sync marketplace catalog"
- "Update marketplace version"

**What it does:**
- Updates marketplace.extended.json
- Runs `npm run sync-marketplace`
- Validates both catalog files
- Checks for duplicates
- Ensures catalog integrity

**Example:** "Add the new security-scanner to marketplace"

---

### 4. 🔍 Plugin Auditor
**Automatically audits plugins for security and quality**

**Activates when you say:**
- "Audit this plugin"
- "Security review"
- "Check best practices"

**What it does:**
- Scans for security vulnerabilities
- Checks hardcoded secrets
- Validates best practices
- Verifies CLAUDE.md compliance
- Generates quality score
- Provides recommendations

**Example:** "Audit the security-scanner plugin for production"

---

### 5. 🔢 Version Bumper
**Automatically handles semantic version updates**

**Activates when you say:**
- "Bump version to patch/minor/major"
- "Release version [x.y.z]"
- "Update plugin version"

**What it does:**
- Calculates new semantic version
- Updates plugin.json
- Updates marketplace catalog
- Syncs marketplace.json
- Updates CHANGELOG.md (if exists)
- Creates git tags (optional)

**Example:** "Bump the security-scanner plugin to patch version"

---

## Who Is This For?

### For Repository Maintainers
- Create new plugins quickly with proper structure
- Validate plugins before merging PRs
- Audit plugins for quality and security
- Manage marketplace catalog efficiently

### For Plugin Contributors
- Ensure your plugin meets all standards
- Validate before submitting PR
- Check compliance with CLAUDE.md
- Get quality recommendations

### For This Repository Specifically
This plugin is **optimized for claude-code-plugins** workflow:
- Knows the two-catalog system (extended vs CLI)
- Understands repository structure
- Follows CLAUDE.md standards
- Handles Skills, Commands, Agents, MCP plugins
- Manages marketplace sync automatically

---

## Installation

```bash
# Add marketplace (if not already added)
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install Skills Powerkit
/plugin install skills-powerkit@claude-code-plugins-plus
```

**That's it!** All 5 skills are now active in this repository.

---

## How to Use

**Just talk naturally while working on plugins!**

### Example Workflows

**Workflow 1: Create New Plugin**
```
You: "I need to create a new DevOps plugin called 'docker-optimizer' with commands"

Skills Powerkit automatically:
1. Recognizes "create new plugin" → Invokes Plugin Creator
2. Scaffolds plugins/devops/docker-optimizer/
3. Generates plugin.json, README, LICENSE, commands/
4. Adds to marketplace.extended.json
5. Syncs marketplace.json
6. Validates everything
7. Reports: "✅ Plugin created and ready!"
```

**Workflow 2: Validate Before Commit**
```
You: "Is my owasp-scanner plugin ready to commit?"

Skills Powerkit automatically:
1. Recognizes "ready to commit" → Invokes Plugin Validator
2. Checks plugin.json schema
3. Validates frontmatter
4. Verifies marketplace entry
5. Checks permissions
6. Reports: "✅ PASSED - Ready to commit!"
```

**Workflow 3: Security Audit**
```
You: "Security audit on the new password-manager plugin"

Skills Powerkit automatically:
1. Recognizes "security audit" → Invokes Plugin Auditor
2. Scans for hardcoded secrets
3. Checks dangerous commands
4. Validates security patterns
5. Generates audit report
6. Reports: "⚠️ Found 2 issues - no hardcoded credentials allowed"
```

**Workflow 4: Release Management**
```
You: "Bump docker-optimizer to minor version and update marketplace"

Skills Powerkit automatically:
1. Recognizes "bump to minor" → Invokes Version Bumper
2. Calculates new version (1.0.0 → 1.1.0)
3. Updates plugin.json
4. Recognizes "update marketplace" → Invokes Marketplace Manager
5. Updates marketplace.extended.json
6. Syncs marketplace.json
7. Reports: "✅ Version bumped to 1.1.0, marketplace updated"
```

---

## Why Is This Powerful?

### Auto-Invoked Intelligence
- **You don't run commands** - Skills activate based on what you say
- **Context-aware** - Knows you're working in claude-code-plugins
- **Workflow understanding** - Knows the two-catalog system
- **Repository-specific** - Follows CLAUDE.md standards

### Complete Automation
- Creates plugins in seconds
- Validates before you forget
- Audits for security automatically
- Manages marketplace with zero effort
- Handles versioning correctly

### Quality Assurance
- Ensures CLAUDE.md compliance
- Validates against CI standards
- Checks marketplace integrity
- Enforces best practices
- Prevents common mistakes

---

## Skills vs Manual Work

| Task | Manual | With Skills Powerkit |
|------|--------|---------------------|
| **Create Plugin** | 15-30 min (create dirs, write JSON, update catalog, sync) | Say "create plugin X" → Done in seconds |
| **Validate Plugin** | 5-10 min (run scripts, check files, review) | Say "validate plugin" → Instant report |
| **Update Marketplace** | 3-5 min (edit JSON, sync, validate) | Say "add to marketplace" → Auto-synced |
| **Version Bump** | 5 min (update 3 files, sync, validate) | Say "bump version" → All files updated |
| **Security Audit** | 10-15 min (grep patterns, check secrets) | Say "audit plugin" → Full report |

**Time saved per plugin:** ~40-60 minutes

---

## Technical Details

### Skill Restrictions

All skills use appropriate tool access:

| Skill | Allowed Tools | Purpose |
|-------|--------------|---------|
| Plugin Creator | Read, Write, Grep, Bash | Full creation capabilities |
| Plugin Validator | Read, Grep, Bash | Read-only validation |
| Marketplace Manager | Read, Write, Edit, Grep, Bash | Catalog management |
| Plugin Auditor | Read, Grep, Bash | Read-only auditing |
| Version Bumper | Read, Write, Edit, Grep, Bash | Version management |

### Repository Knowledge

Skills Powerkit understands:
- **Two-catalog system**: marketplace.extended.json (source) → marketplace.json (generated)
- **Directory structure**: plugins/[category]/[plugin-name]/
- **Required files**: plugin.json, README.md, LICENSE
- **Validation scripts**: ./scripts/validate-all.sh, check-frontmatter.py
- **Sync command**: npm run sync-marketplace
- **Valid categories**: 14 plugin categories
- **CLAUDE.md standards**: All repository conventions

---

## Example Conversations

### Creating a Plugin

**You:** "I want to create a new testing plugin for Jest test generation"

**Skills Powerkit:**
1. Activates Plugin Creator skill
2. "I'll create a testing plugin called 'jest-test-generator'. What should it include - commands, agents, or both?"

**You:** "Both commands and agents"

**Skills Powerkit:**
```
✅ Created plugin: jest-test-generator
📁 Location: plugins/testing/jest-test-generator/
📝 Files created:
   - .claude-plugin/plugin.json
   - README.md
   - LICENSE
   - commands/generate.md
   - agents/jest-expert.md
🔍 Validation: PASSED
📦 Marketplace: UPDATED (synced)
✨ Ready to customize and commit!
```

### Validating a Plugin

**You:** "Check if my jest-test-generator plugin is valid"

**Skills Powerkit:**
```
🔍 PLUGIN VALIDATION REPORT
Plugin: jest-test-generator

✅ PASSED (9/10)
- Required files present
- Valid plugin.json
- Proper frontmatter
- Marketplace entry exists
- No security issues

⚠️ WARNINGS (1)
- 1 script missing execute permission
  Fix: chmod +x scripts/generate.sh

OVERALL: PASSED with warnings
```

---

## Integration with Repository Workflow

### Works With Existing Tools

Skills Powerkit **enhances** existing tools:
- Uses `./scripts/validate-all.sh` under the hood
- Calls `npm run sync-marketplace` automatically
- Validates with `jq` and `python3 scripts/check-frontmatter.py`
- Follows same standards as CI/CD

### CI/CD Compatibility

Skills run the **same checks as GitHub Actions**:
- `.github/workflows/validate-plugins.yml` checks
- Security scans match CI patterns
- Validation matches CI requirements
- **Fix issues before CI fails**

---

## Requirements

- Claude Code CLI with Skills support (October 2025+)
- Working in `claude-code-plugins` repository
- Node.js for `npm run sync-marketplace`
- Python 3 for frontmatter validation
- `jq` for JSON validation

---

## Pro Tips

### 💡 Tip 1: Chain Skills
Say: "Create a security plugin, validate it, and add to marketplace"
→ All 3 skills activate automatically in sequence

### 💡 Tip 2: Pre-Commit Check
Say: "Is everything ready to commit?"
→ Validator runs comprehensive check

### 💡 Tip 3: Quality Assurance
Say: "Full audit for featured plugin status"
→ Auditor runs with higher quality thresholds

### 💡 Tip 4: Version Releases
Say: "Bump to minor and update marketplace"
→ Version Bumper + Marketplace Manager work together

---

## Troubleshooting

### "Skills not activating"
- Ensure you're in claude-code-plugins repository
- Check you said trigger keywords ("create plugin", "validate", etc.)
- Verify Skills Powerkit is installed: `/plugin list`

### "Marketplace sync fails"
- Run manually: `npm run sync-marketplace`
- Check marketplace.extended.json syntax with `jq`
- Verify no duplicate plugin names

### "Validation fails"
- Check error message for specific issue
- Run: `./scripts/validate-all.sh plugins/your-plugin/`
- Fix reported issues

---

## Contributing

Found a bug or want to improve Skills Powerkit?

**Report issues:** https://github.com/jeremylongshore/claude-code-plugins/issues

**Improve skills:** Fork, enhance SKILL.md files, submit PR

---

## License

MIT License - See [LICENSE](LICENSE) file

---

## Learn More

- **Agent Skills Documentation:** https://docs.claude.com/en/docs/claude-code/skills
- **Plugin Guide:** https://docs.claude.com/en/docs/claude-code/plugins
- **Repository CLAUDE.md:** [View CLAUDE.md](../../CLAUDE.md)

---

## Changelog

### v1.0.0 (2025-10-16)
- Initial release
- 5 repository-specific Agent Skills
- Plugin Creator, Validator, Marketplace Manager, Auditor, Version Bumper
- Optimized for claude-code-plugins workflow
- Auto-invoked based on conversation context

---

**Ready to supercharge your plugin development workflow?**

```bash
/plugin install skills-powerkit@claude-code-plugins-plus
```

Then just start working on plugins - the skills will help automatically! 🚀
