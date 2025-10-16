---
name: demo-skills
description: Demonstrates the 5 plugin management Skills for creating, validating, auditing, and managing plugins in claude-code-plugins repository
model: sonnet
---

# Skills Powerkit Demo - Plugin Management Skills

This command demonstrates the 5 Agent Skills designed specifically for managing plugins in the **claude-code-plugins** repository.

## What Is Skills Powerkit?

**Skills Powerkit is a "meta-plugin"** - it helps you BUILD, VALIDATE, AUDIT, and MANAGE other plugins.

Unlike general development skills, these are **repository-specific** - they understand:
- Two-catalog system (marketplace.extended.json → marketplace.json)
- Repository structure and standards
- CLAUDE.md compliance requirements
- Validation and security requirements

---

## 5 Plugin Management Skills

### 1. 🛠️ Plugin Creator
**Auto-invokes when you mention:**
- "create plugin", "new plugin"
- "scaffold plugin"
- "add plugin to marketplace"

**Example request:** "Create a security plugin called 'owasp-scanner' with commands"

**What it automatically does:**
1. Creates directory structure: `plugins/security/owasp-scanner/`
2. Generates plugin.json with proper schema
3. Creates README.md, LICENSE
4. Adds commands/ directory with example
5. Updates marketplace.extended.json
6. Runs `npm run sync-marketplace`
7. Validates everything
8. Reports: "✅ Plugin created and ready!"

**Saves you:** 15-30 minutes of manual setup

---

### 2. ✅ Plugin Validator
**Auto-invokes when you mention:**
- "validate plugin", "check plugin"
- "is plugin ready to commit"
- "plugin errors"

**Example request:** "Validate the skills-powerkit plugin"

**What it automatically does:**
1. Checks required files exist
2. Validates plugin.json schema
3. Checks markdown frontmatter format
4. Verifies script permissions
5. Validates marketplace entry
6. Runs security scans
7. Generates validation report

**Saves you:** 5-10 minutes of manual checking

---

### 3. 📦 Marketplace Manager
**Auto-invokes when you mention:**
- "update marketplace", "sync marketplace"
- "add to marketplace"
- "marketplace catalog"

**Example request:** "Add the new security-scanner to marketplace"

**What it automatically does:**
1. Reads plugin.json for metadata
2. Adds entry to marketplace.extended.json
3. Runs `npm run sync-marketplace`
4. Validates both catalog files
5. Checks for duplicates
6. Reports success

**Saves you:** 3-5 minutes of manual catalog editing

---

### 4. 🔍 Plugin Auditor
**Auto-invokes when you mention:**
- "audit plugin", "security review"
- "best practices check"
- "plugin quality"

**Example request:** "Security audit on the password-manager plugin"

**What it automatically does:**
1. Scans for hardcoded secrets (passwords, API keys)
2. Checks for dangerous commands (rm -rf, eval)
3. Validates security patterns
4. Checks best practices compliance
5. Verifies CLAUDE.md standards
6. Generates quality score
7. Provides recommendations

**Saves you:** 10-15 minutes of manual security review

---

### 5. 🔢 Version Bumper
**Auto-invokes when you mention:**
- "bump version", "update version"
- "release", "new version"
- "major/minor/patch"

**Example request:** "Bump docker-optimizer to minor version"

**What it automatically does:**
1. Reads current version from plugin.json
2. Calculates new version (1.0.0 → 1.1.0)
3. Updates plugin.json
4. Updates marketplace.extended.json
5. Runs `npm run sync-marketplace`
6. Updates CHANGELOG.md (if exists)
7. Can create git tags
8. Reports success

**Saves you:** 5 minutes of manual version updates

---

## How Skills Work

**Skills are MODEL-INVOKED** - Claude automatically decides when to use them.

**Example conversation:**

**You:** "I need a new DevOps plugin for Docker optimization with commands"

**Claude automatically:**
1. Recognizes "new plugin" → Invokes Plugin Creator
2. Recognizes "DevOps" → Sets category
3. Recognizes "with commands" → Creates commands/ directory
4. Creates plugins/devops/docker-optimizer/
5. Generates all files
6. Updates marketplace
7. Validates
8. Reports: "✅ Created docker-optimizer plugin!"

**You didn't run any commands** - Claude understood context and did everything!

---

## Skills vs Commands Comparison

| Feature | Skills (This Plugin) | Slash Commands |
|---------|---------------------|----------------|
| **Invocation** | Auto (Claude decides) | Manual (/command) |
| **Trigger** | Keywords in conversation | Explicit command |
| **Context** | Understands repository | Single purpose |
| **Workflow** | Chains multiple tasks | Single task |
| **Example** | "create and validate plugin" | /create then /validate |

**Skills feel natural** - like talking to a teammate who knows the repo!

---

## Real Workflow Examples

### Workflow 1: Create + Validate + Audit
**You:** "Create a security plugin called 'owasp-scanner', validate it, and run security audit"

**Skills automatically chain:**
1. Plugin Creator → Creates plugin
2. Plugin Validator → Validates structure
3. Plugin Auditor → Security audit
4. Reports all results

### Workflow 2: Update + Sync
**You:** "Bump version to 1.2.0 and update marketplace"

**Skills automatically chain:**
1. Version Bumper → Updates to 1.2.0
2. Marketplace Manager → Syncs catalog
3. Reports success

### Workflow 3: Pre-Commit Check
**You:** "Is everything ready to commit?"

**Skills automatically:**
1. Plugin Validator → Full validation
2. Plugin Auditor → Security check
3. Reports: "✅ PASSED - Ready to commit!"

---

## Repository-Specific Knowledge

Skills Powerkit knows about claude-code-plugins:

**Two-Catalog System:**
- marketplace.extended.json (source - edit this)
- marketplace.json (generated - never edit)
- Auto-runs `npm run sync-marketplace`

**Directory Structure:**
- plugins/[category]/[plugin-name]/
- 14 valid categories
- Required files

**Validation Standards:**
- ./scripts/validate-all.sh
- python3 scripts/check-frontmatter.py
- jq for JSON validation

**CLAUDE.md Compliance:**
- Follows repository conventions
- Uses correct marketplace slug
- Validates against standards

---

## Try It Out!

Test each skill by saying:

1. **"Create a new testing plugin called 'jest-generator'"**
   → Plugin Creator activates

2. **"Validate the jest-generator plugin"**
   → Plugin Validator activates

3. **"Add jest-generator to marketplace"**
   → Marketplace Manager activates

4. **"Security audit on jest-generator"**
   → Plugin Auditor activates

5. **"Bump jest-generator to version 1.1.0"**
   → Version Bumper activates

Claude will automatically use the right skill!

---

## Installation

```bash
/plugin install skills-powerkit@claude-code-plugins-plus
```

Once installed, all 5 skills are active and auto-invoke when relevant.

---

## Time Savings

**Per plugin lifecycle:**
- Create: 15-30 min → 30 seconds
- Validate: 5-10 min → 10 seconds
- Marketplace: 3-5 min → 5 seconds
- Audit: 10-15 min → 15 seconds
- Version: 5 min → 10 seconds

**Total saved: 40-60 minutes per plugin!**

---

## Requirements

- Claude Code CLI with Skills support (Oct 2025+)
- Working in claude-code-plugins repository
- Node.js for marketplace sync
- Python 3 for frontmatter validation
- jq for JSON validation

---

**Need help?** Just ask:
- "What skills do I have available?"
- "How do I create a plugin?"
- "Validate my current plugin"

Skills will respond automatically! 🚀
