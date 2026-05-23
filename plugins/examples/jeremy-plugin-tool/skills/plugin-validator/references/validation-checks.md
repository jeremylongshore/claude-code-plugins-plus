# Validation Checks

## Validation Checks

### 1. Required Files

- ✅ `.claude-plugin/plugin.json` exists
- ✅ `README.md` exists and not empty
- ✅ `LICENSE` file exists
- ✅ At least one component directory (commands/, agents/, skills/, hooks/, mcp/)

### 2. Plugin.json Schema

```bash
# Required fields:
- name (kebab-case, lowercase, hyphens only)
- version (semantic versioning x.y.z)
- description (clear, concise)
- author.name
- author.email
- license (MIT, Apache-2.0, etc.)
- keywords (array, at least 2)

# Optional but recommended:
- repository (GitHub URL)
- homepage (docs URL)
```

### 3. Frontmatter Validation

**For Commands (commands/*.md):**

```yaml
---
name: command-name
description: Brief description
model: sonnet|opus|haiku
---
```

**For Agents (agents/*.md):**

```yaml
---
name: agent-name
description: Agent purpose
model: sonnet|opus|haiku
---
```

**For Skills (skills/*/SKILL.md):**

```yaml
---
name: Skill Name
description: What it does AND when to use it
allowed-tools: Tool1, Tool2, Tool3  # optional
---
```

### 4. Directory Structure

Validates proper hierarchy:

```
plugin-name/
├── .claude-plugin/          # Required
│   └── plugin.json          # Required
├── README.md                 # Required
├── LICENSE                   # Required
├── commands/                 # Optional
│   └── *.md
├── agents/                   # Optional
│   └── *.md
├── skills/                   # Optional
│   └── skill-name/
│       └── SKILL.md
├── hooks/                    # Optional
│   └── hooks.json
└── mcp/                      # Optional
    └── *.json
```

### 5. Script Permissions

```bash
# All .sh files must be executable
find . -name "*.sh" ! -perm -u+x
# Should return empty
```

### 6. JSON Validation

```bash
# All JSON must be valid
jq empty plugin.json
jq empty marketplace.extended.json
jq empty hooks/hooks.json
```

### 7. Security Scans

- ❌ No hardcoded secrets (API keys, tokens, passwords)
- ❌ No AWS keys (AKIA...)
- ❌ No private keys (BEGIN PRIVATE KEY)
- ❌ No dangerous commands (rm -rf /, eval())
- ❌ No suspicious URLs (non-HTTPS, IP addresses)

### 8. Marketplace Compliance

- ✅ Plugin listed in marketplace.extended.json
- ✅ Source path matches actual location
- ✅ Version matches between plugin.json and catalog
- ✅ Category is valid
- ✅ No duplicate plugin names

### 9. README Requirements

- ✅ Has installation instructions
- ✅ Has usage examples
- ✅ Has description section
- ✅ Proper markdown formatting
- ✅ No broken links

### 10. Path Variables

For hooks:

- ✅ Uses `${CLAUDE_PLUGIN_ROOT}` not absolute paths
- ✅ No hardcoded /home/ or /Users/ paths
