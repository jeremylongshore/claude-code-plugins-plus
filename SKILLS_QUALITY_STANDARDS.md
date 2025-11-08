# Claude Code Skills - Quality Standards
**Version:** 1.3.0
**Date:** November 8, 2025
**Status:** Industry-Leading Best Practices

## Overview

This document defines the **best-of-best quality standards** for Claude Code Skills in our marketplace. These standards ensure our skills are professional, reliable, and user-friendly.

---

## 🎯 Core Standards

### 1. SKILL.md Requirements

**MUST HAVE (Required):**
```yaml
---
name: skill-name                  # lowercase, hyphens, max 64 chars
description: |                    # max 1024 chars
  What this skill does and when to use it.
  Include explicit trigger phrases like "analyze performance"
  or "generate tests" so users know when it activates.
allowed-tools: Read, Grep, Bash   # Comma-separated tool list
version: 1.0.0                    # Semantic versioning
---
```

**Content Structure:**
1. **## Overview** - What the skill does (2-3 paragraphs)
2. **## How It Works** - Step-by-step workflow
3. **## When to Use This Skill** - Bulleted activation scenarios
4. **## Examples** - At least 2 real-world examples
5. **## Best Practices** (optional) - Usage tips
6. **## Integration** (optional) - How it works with other tools

---

### 2. Supporting Files Structure

Every skill SHOULD have:

```
skills/
└── skill-name/
    ├── SKILL.md              # Main skill definition (REQUIRED)
    ├── scripts/              # Helper scripts (RECOMMENDED)
    │   ├── validation.sh     # Skill validator
    │   └── helper-template.sh # Automation template
    ├── references/           # Documentation (RECOMMENDED)
    │   ├── examples.md       # Usage examples
    │   └── best-practices.md # Guidelines
    └── assets/               # Static files (OPTIONAL)
        ├── config-template.json  # Configuration
        ├── skill-schema.json     # JSON schema
        └── test-data.json        # Test fixtures
```

**Why This Matters:**
- Scripts enable automation
- References provide context without bloating SKILL.md
- Assets support configuration and testing

---

### 3. Tool Permissions Standards

**Read-Only Analysis** (Security Scans, Monitoring):
```yaml
allowed-tools: Read, Grep, Glob, Bash
```

**Code Generation/Editing** (Generators, Refactoring):
```yaml
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
```

**Web Research** (Documentation, API Discovery):
```yaml
allowed-tools: Read, WebFetch, WebSearch, Grep
```

**Database Operations** (Migrations, Queries):
```yaml
allowed-tools: Read, Write, Bash, Grep
```

**Testing** (Test Runners, Coverage):
```yaml
allowed-tools: Read, Bash, Grep, Glob
```

**Principle:** Use the **minimum tools necessary** for the skill's purpose.

---

### 4. Description Quality Standards

**✅ GOOD Description:**
```yaml
description: |
  Analyzes application performance metrics and identifies bottlenecks.
  Monitors CPU usage, memory allocation, and I/O patterns.

  Use when requesting "analyze performance", "check CPU usage",
  "optimize speed", or "find bottlenecks".

  This skill helps identify inefficient code, memory leaks, and
  algorithmic complexity issues.
```

**Why it's good:**
- Starts with clear "what"
- Includes specific trigger phrases in quotes
- Explains "when" to use
- Under 1024 characters
- Actionable language

**❌ BAD Description:**
```yaml
description: This skill analyzes things.
```

**Why it's bad:**
- Vague ("things")
- No trigger phrases
- Doesn't explain when to use
- Minimal value to users

---

### 5. Trigger Phrase Best Practices

**Include these elements:**
1. **Action verbs:** "analyze", "generate", "scan", "optimize", "monitor"
2. **Domain keywords:** "security", "performance", "database", "testing"
3. **Specific phrases:** Put in quotes - "check CPU usage", "scan for vulnerabilities"

**Example trigger documentation:**
```markdown
## When to Use This Skill

This skill activates when you request:
- "scan for security vulnerabilities"
- "audit authentication mechanisms"
- "check for SQL injection risks"
- "validate input sanitization"
```

---

### 6. Version Management

**Semantic Versioning (MAJOR.MINOR.PATCH):**
- **1.0.0** - Initial release
- **1.1.0** - New feature, backward compatible
- **1.0.1** - Bug fix, no new features
- **2.0.0** - Breaking change

**When to bump version:**
- Description changes → PATCH
- New allowed-tools → MINOR
- Changed tool set (breaking) → MAJOR
- Enhanced functionality → MINOR
- Fixed bugs → PATCH

---

### 7. Script Standards

**All scripts MUST:**
1. Have executable permissions (`chmod +x`)
2. Include shebang line (`#!/bin/bash` or `#!/usr/bin/env python3`)
3. Have usage documentation in comments
4. Handle errors gracefully (`set -e` for bash)
5. Provide helpful error messages

**Template:**
```bash
#!/bin/bash
# Script purpose: [What it does]
# Usage: ./script.sh [options]
# Author: [Name]
# Version: 1.0.0

set -e  # Exit on error

# Your code here
```

---

### 8. Reference Documentation Standards

**examples.md Structure:**
```markdown
# Skill Usage Examples

## Basic Usage
[Simple example with user request and result]

## Advanced Patterns
[Complex workflow examples]

## Common Issues
[Troubleshooting guide]

## Tips & Best Practices
[Pro tips for optimal usage]
```

**best-practices.md Structure:**
```markdown
# Skill Best Practices

## For Users
[How to use effectively]

## For Developers
[How to maintain/extend]

## Performance Tips
[Optimization advice]

## Security Considerations
[Security guidelines]
```

---

### 9. Asset Standards

**config-template.json:**
- Valid JSON (test with `jq`)
- Clear comments via field names
- Sensible defaults
- All options documented

**skill-schema.json:**
- JSON Schema Draft 7
- Validates skill frontmatter
- Includes field descriptions
- Enforces required fields

**test-data.json:**
- Real-world test cases
- Expected outputs
- Edge case examples
- Fixtures for testing

---

### 10. Marketplace Integration

**Plugin.json Requirements:**
```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Clear one-line description",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "keywords": ["keyword1", "keyword2"],
  "license": "MIT"
}
```

**Marketplace.extended.json Entry:**
```json
{
  "name": "plugin-name",
  "source": "./plugins/category/plugin-name",
  "description": "One-line description",
  "version": "1.0.0",
  "category": "valid-category",
  "keywords": ["tag1", "tag2"],
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "components": {
    "skills": 1,
    "commands": 0,
    "agents": 0
  }
}
```

---

## 📊 Quality Checklist

Before releasing a skill, verify:

**Structure:**
- [ ] SKILL.md exists with correct frontmatter
- [ ] Name is lowercase, hyphenated, <64 chars
- [ ] Description <1024 chars with trigger phrases
- [ ] allowed-tools specified with minimal set
- [ ] version follows semver (x.y.z)
- [ ] scripts/ directory with helper files
- [ ] references/ with examples and best practices
- [ ] assets/ with templates and schemas

**Content:**
- [ ] Overview explains what skill does
- [ ] Workflow documented step-by-step
- [ ] Activation scenarios listed clearly
- [ ] At least 2 real-world examples
- [ ] Best practices included
- [ ] No hardcoded secrets or credentials

**Testing:**
- [ ] Skill activates with trigger phrases
- [ ] Tool permissions work as expected
- [ ] Scripts are executable
- [ ] JSON files validate with jq
- [ ] Examples actually work

**Documentation:**
- [ ] README.md in plugin root
- [ ] LICENSE file present
- [ ] plugin.json valid
- [ ] Marketplace entry correct

---

## 🏆 Best-of-Best Examples

**Study these for excellence:**
1. `skills-powerkit/plugin-validator` - Comprehensive validation
2. `skills-powerkit/plugin-creator` - Generator with templates
3. `cpu-usage-monitor` - Performance analysis
4. `security-scanner` - Security auditing
5. `unit-test-generator` - Code generation

---

## 🚀 Continuous Improvement

**Monthly:**
- Review user feedback
- Update trigger phrases if activation issues
- Enhance examples based on usage
- Optimize tool permissions

**Quarterly:**
- Audit all skills for compliance
- Update to latest Anthropic schema
- Refresh documentation
- Add new best practices

**Annually:**
- Major version reviews
- Breaking changes if justified
- Complete documentation overhaul
- Benchmark against industry leaders

---

## 📚 Resources

- [Anthropic Skills Docs](https://docs.claude.com/en/docs/claude-code/skills)
- [Official Skills Repo](https://github.com/anthropics/skills)
- [SKILL_ACTIVATION_GUIDE.md](SKILL_ACTIVATION_GUIDE.md) - User guide
- [SKILLS_SCHEMA_2025.md](SKILLS_SCHEMA_2025.md) - Technical spec
- [CLAUDE.md](CLAUDE.md) - Repository standards

---

## 🎖️ Industry-Leading Achievement

**As of v1.3.0:**
- ✅ 175 skills (100% 2025 schema compliant)
- ✅ 175 skills with tool permissions
- ✅ 175 skills with version tracking
- ✅ 75 skill-adapters with professional supporting files
- ✅ First marketplace to achieve 100% compliance
- ✅ Comprehensive user activation guide
- ✅ Professional supporting file structure

**We're not just compliant - we're setting the standard.**

---

**Last Updated:** November 8, 2025
**Maintained By:** Claude Code Plugins Team
**Status:** Active - Living Document
