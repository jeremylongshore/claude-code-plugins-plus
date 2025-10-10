# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is **the comprehensive marketplace and learning hub for Claude Code plugins**. It serves as both a distribution platform for plugins and an educational resource for plugin developers.

**Repository Purpose:**
- Marketplace catalog for discovering and installing Claude Code plugins
- Educational hub with working examples and templates
- Community contribution platform for plugin developers

## Repository Structure

```
claude-code-plugins/
├── .claude-plugin/
│   └── marketplace.json                # Main marketplace catalog
├── plugins/
│   ├── examples/                       # 3 fully functional example plugins
│   │   ├── hello-world/               # Basic slash command demo
│   │   ├── formatter/                 # PostToolUse hooks demo
│   │   └── security-agent/            # Subagent demo
│   └── community/                      # Community-contributed plugins
├── templates/                          # 4 plugin starter templates
│   ├── minimal-plugin/                # Bare minimum structure
│   ├── command-plugin/                # With slash commands
│   ├── agent-plugin/                  # With AI subagent
│   └── full-plugin/                   # All features (commands, agents, hooks)
├── docs/                               # Documentation files
├── scripts/                            # Repository maintenance scripts
└── .github/                            # GitHub workflows and templates
```

## Plugin Architecture

Each Claude Code plugin can contain:
- **Slash Commands** (`commands/*.md`) - Custom shortcuts triggered with `/command-name`
- **Subagents** (`agents/*.md`) - Specialized AI agents for specific domains
- **Hooks** (`hooks/hooks.json`) - Event-driven automation (PostToolUse, PreToolUse, etc.)
- **MCP Servers** (`mcp/*.json`) - Connections to external tools/services
- **Scripts** (`scripts/*.sh`) - Shell scripts called by hooks or commands

### Plugin Structure Requirements

Every plugin MUST have:
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json                    # Plugin metadata (REQUIRED)
├── README.md                          # Documentation (REQUIRED)
├── LICENSE                            # License file (REQUIRED)
└── [commands|agents|hooks|mcp|scripts]/ # At least one component
```

### plugin.json Format

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Clear description",
  "author": {
    "name": "Author Name",
    "email": "[email protected]"
  },
  "repository": "https://github.com/username/repo",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"]
}
```

## Common Development Tasks

### Repository Setup

```bash
# Make all scripts executable and initialize git
./setup.sh

# Manual alternative:
find . -type f -name "*.sh" -exec chmod +x {} \;
git init
git add .
git commit -m "Initial commit"
```

### Testing Plugins Locally

```bash
# Create test marketplace
mkdir -p ~/test-marketplace/.claude-plugin

# Create marketplace.json pointing to your local plugin
cat > ~/test-marketplace/.claude-plugin/marketplace.json << 'EOF'
{
  "name": "test",
  "owner": {"name": "Test"},
  "plugins": [{
    "name": "my-plugin",
    "source": "/absolute/path/to/plugins/community/my-plugin"
  }]
}
EOF

# Add test marketplace to Claude Code
/plugin marketplace add ~/test-marketplace

# Install your plugin
/plugin install my-plugin@test

# Test the plugin (commands, agents, hooks)
/my-command
```

### Validating Plugin Structure

```bash
# Check JSON validity
find . -name "*.json" -exec sh -c 'echo "Validating {}"; jq empty {}' \;

# Verify script permissions
find . -name "*.sh" -ls

# Test marketplace.json structure
jq '.plugins[] | select(.name == "plugin-name")' .claude-plugin/marketplace.json
```

### Adding a New Plugin to Marketplace

1. Add plugin directory to `plugins/community/your-plugin/`
2. Update `.claude-plugin/marketplace.json`:
```json
{
  "name": "your-plugin",
  "source": "./plugins/community/your-plugin",
  "description": "Clear description",
  "version": "1.0.0",
  "category": "productivity",
  "keywords": ["keyword1", "keyword2"],
  "author": {
    "name": "Your Name",
    "email": "[email protected]"
  }
}
```
3. Test locally (see above)
4. Submit PR using `.github/PULL_REQUEST_TEMPLATE.md`

## Key Architecture Patterns

### Slash Commands Pattern

Commands are markdown files with YAML frontmatter:
```markdown
---
description: Brief description of command
shortcut: sc
---

# Command Name

Detailed instructions for Claude on what to do when this command is invoked.
Include specific guidance on execution and expected output.
```

### Subagent Pattern

Agents are markdown files defining specialized behavior:
```markdown
---
description: Specialist in X domain
capabilities: ["capability1", "capability2"]
---

# Agent Name

You are a specialized agent for X domain.

## Your Capabilities
- List specific skills
- Define expertise areas

## When to Activate
Describe triggering conditions

## Approach
Outline methodology and output format
```

### Hooks Pattern

Hooks trigger scripts on events:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/process.sh"
          }
        ]
      }
    ]
  }
}
```

**Important:** Use `${CLAUDE_PLUGIN_ROOT}` for portable paths in hooks.

## Development Workflow

### Creating a New Plugin

```bash
# 1. Choose and copy template
cp -r templates/command-plugin plugins/community/my-plugin
cd plugins/community/my-plugin

# 2. Edit plugin.json with your metadata

# 3. Create your components
# - Add commands to commands/
# - Add agents to agents/
# - Add hooks to hooks/hooks.json
# - Add scripts to scripts/ (make executable!)

# 4. Write comprehensive README.md

# 5. Test locally (see Testing Plugins Locally above)

# 6. Update marketplace catalog
# Edit ../../.claude-plugin/marketplace.json

# 7. Submit PR
git checkout -b add-my-plugin
git add plugins/community/my-plugin/
git add .claude-plugin/marketplace.json
git commit -m "Add my-plugin: Brief description"
git push origin add-my-plugin
```

### Plugin Submission Checklist

Before submitting a PR:
- [ ] Valid `.claude-plugin/plugin.json` (test with `jq`)
- [ ] Comprehensive README.md with examples
- [ ] LICENSE file (MIT or Apache-2.0 recommended)
- [ ] All scripts are executable (`chmod +x scripts/*.sh`)
- [ ] No hardcoded secrets or credentials
- [ ] Tested locally and working
- [ ] Marketplace.json updated
- [ ] PR uses template

## Important Conventions

### Script Permissions
All shell scripts MUST be executable:
```bash
chmod +x scripts/*.sh
```

### Path Variables
Use `${CLAUDE_PLUGIN_ROOT}` in hooks for portable paths:
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/format.sh
```

### Versioning
Follow semantic versioning (MAJOR.MINOR.PATCH):
- **1.0.0** - Initial release
- **1.1.0** - New feature, backward compatible
- **1.1.1** - Bug fix, backward compatible
- **2.0.0** - Breaking change

### Plugin Categories
- `productivity` - Workflow optimization, automation
- `security` - Security analysis, vulnerability scanning
- `testing` - Test automation, QA tools
- `deployment` - CI/CD, infrastructure
- `documentation` - Docs generation, API docs
- `analysis` - Code analysis, metrics
- `integration` - External service integrations
- `ai` - AI/ML tooling
- `example` - Educational/tutorial plugins
- `other` - Doesn't fit above categories

## Marketplace Installation

Users add this marketplace to Claude Code with:
```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
```

Then install plugins:
```bash
/plugin install hello-world@claude-code-plugins
/plugin install formatter@claude-code-plugins
/plugin install security-agent@claude-code-plugins
```

## Security Best Practices

1. **Never hardcode secrets** - Use environment variables
2. **Validate inputs** - All script inputs should be validated
3. **Use portable paths** - Always use `${CLAUDE_PLUGIN_ROOT}`
4. **Minimal permissions** - Scripts should request minimum necessary access
5. **No destructive operations** - Without explicit user confirmation
6. **Executable scripts only** - All `.sh` files must have `chmod +x`

## Documentation Standards

### README.md Requirements
Every plugin must include:
1. **Installation** - How to install the plugin
2. **Usage** - Clear examples with code blocks
3. **Requirements** - Dependencies, tools needed
4. **Files** - Explanation of plugin components
5. **License** - License information

### Code Comments
- Use clear variable names in scripts
- Add comments explaining complex logic
- Include error messages in scripts
- Document hook matchers and triggers

## Testing Guidelines

### Local Testing Workflow
1. Create test marketplace pointing to local plugin directory
2. Install plugin in Claude Code
3. Test all commands, agents, and hooks
4. Verify scripts execute correctly
5. Check edge cases and error handling
6. Test with different file types (if applicable)

### Common Issues
- **Commands not appearing** → Check plugin.json syntax, verify `commands/` directory
- **Scripts not executing** → Verify `chmod +x`, check shebang `#!/bin/bash`
- **Hooks not firing** → Validate hooks.json, test matcher patterns
- **Path errors** → Use `${CLAUDE_PLUGIN_ROOT}` instead of absolute paths

## Project-Specific Notes

- This repository uses **GitHub** for hosting, NOT GitHub Marketplace
- Plugins are **free and open-source** (no monetization built into system)
- Beta status: Features may evolve, keep documentation updated
- Community-driven: Accept quality contributions via PR
- Educational focus: All examples should teach concepts clearly

## Resources

- **Official Docs:** https://docs.claude.com/en/docs/claude-code/plugins
- **Plugin Reference:** https://docs.claude.com/en/docs/claude-code/plugins-reference
- **Discord:** https://discord.com/invite/6PPFFzqPDZ (#claude-code channel)
- **Contributing:** See CONTRIBUTING.md for detailed guidelines

---

**Last Updated:** October 2025
**Repository Status:** Active, accepting community contributions
