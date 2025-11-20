# Agent Skills System

**Last Updated:** November 15, 2025
**Current Status:** 185 Agent Skills (100% 2025 schema compliant)

## Overview

This repository uses **Agent Skills** - model-invoked capabilities that activate automatically based on conversation context and trigger phrases. Unlike commands (which users invoke explicitly), skills are intelligent assistants that Claude Code activates when needed.

## 2025 Schema Compliance

All 185 skills have been migrated to the 2025 schema standard:

### Required Fields

```yaml
---
name: skill-name                    # lowercase, hyphens, max 64 chars
description: |                      # Clear "what" and "when", max 1024 chars
  What this skill does and when to use it.
  Include trigger phrases like "analyze performance" or "optimize code"
  so users know when this skill will activate.
allowed-tools: Read, Write, Bash    # Comma-separated list of permitted tools
version: 1.0.0                      # Semantic versioning (x.y.z)
---
```

### Tool Categories

Skills are restricted to specific tool sets for security and performance:

- **Read-only analysis**: \`Read, Grep, Glob, Bash\`
- **Code editing**: \`Read, Write, Edit, Grep, Glob, Bash\`
- **Web research**: \`Read, WebFetch, WebSearch, Grep\`
- **Database operations**: \`Read, Write, Bash, Grep\`
- **Testing**: \`Read, Bash, Grep, Glob\`

## Current Metrics

- **Total Plugins**: 253
- **Plugins with Agent Skills**: 185 (73%)
- **2025 Schema Compliance**: 100%
- **Average SKILL.md Size**: 3,210 bytes (17x Anthropic examples)
- **Total Skills**: 185 unique skills

## Skills Generation System

### Automated Pipeline

1. **Database Tracking** (\`backups/skills_generation.db\`)
   - SQLite database tracking all 253 plugins
   - Status: pending → processing → completed → failed
   - Metadata: skill size, generation timestamp, error logs

2. **Daily Automation** (\`.github/workflows/daily-skill-generator.yml\`)
   - Runs via GitHub Actions
   - Uses Vertex AI Gemini 2.0 Flash API
   - Automatic backups before generation
   - Safety checks and validation

3. **Manual Generation** (\`./scripts/next-skill.sh\`)
   - Interactive script for on-demand generation
   - Reads plugin README and manifest
   - Prompts Vertex AI with plugin context
   - Validates YAML frontmatter
   - Updates database with results

## Plugin Developer Guide

### Adding Skills to Your Plugin

1. Create skill directory: \`plugins/your-plugin/skills/skill-adapter/\`
2. Create SKILL.md with 2025 schema frontmatter
3. Validate: \`python3 scripts/validate-skills-schema.py\`
4. Test locally with plugin

### Best Practices

1. **Clear Trigger Phrases**: Include 3-5 example phrases in description
2. **Minimal Tool Set**: Only request tools you actually need
3. **Version Tracking**: Increment version on updates (semantic versioning)
4. **Step-by-step Workflows**: Break complex tasks into phases
5. **Real Examples**: Include actual usage scenarios

## Validation Tools

### Plugin Validator Package (NEW in v1.3.2)

```bash
# Validate your plugin (includes skills validation)
npx claude-plugin-validator ./your-plugin

# Auto-fix common issues
npx claude-plugin-validator ./your-plugin --fix

# Scan all installed plugins
npx claude-plugin-validator --installed
```

### Schema Validation Scripts

```bash
# Validate all skills comply with 2025 schema
python3 scripts/validate-skills-schema.py

# Generate skills for next plugin in queue
./scripts/next-skill.sh
```

## Resources

- **GitHub Issues**: https://github.com/jeremylongshore/claude-code-plugins/issues
- **Discord**: https://discord.com/invite/6PPFFzqPDZ (#claude-code channel)
- **Documentation**: \`scripts/SKILLS_AUTOMATION.md\`

---

**Note:** All 185 Agent Skills follow the 2025 schema standard for consistent quality and security.
