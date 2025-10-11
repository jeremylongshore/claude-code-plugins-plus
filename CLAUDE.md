# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is **the comprehensive marketplace and learning hub for Claude Code plugins**. It serves as both a distribution platform for plugins and an educational resource for plugin developers.

**Repository Purpose:**
- Marketplace catalog for discovering and installing Claude Code plugins
- Educational hub with working examples and templates
- Community contribution platform for plugin developers
- Current Stats: 20 marketplace plugins, 62 total plugin components, 4 plugin packs

## Repository Structure

```
claude-code-plugins/
├── .claude-plugin/
│   └── marketplace.json                # Main marketplace catalog (20 plugins)
├── plugins/
│   ├── examples/                       # 3 fully functional example plugins
│   │   ├── hello-world/               # Basic slash command demo
│   │   ├── formatter/                 # PostToolUse hooks demo
│   │   └── security-agent/            # Subagent demo
│   ├── packages/                      # 4 premium plugin packs
│   │   ├── devops-automation-pack/    # 25 DevOps plugins
│   │   ├── security-pro-pack/         # 10 security plugins
│   │   ├── fullstack-starter-pack/    # 15 fullstack plugins
│   │   └── ai-ml-engineering-pack/    # 12 AI/ML plugins
│   ├── mcp/                           # 5 MCP server plugins (21 tools)
│   ├── devops/                        # Production DevOps plugins
│   ├── productivity/                  # Productivity plugins
│   ├── ai-agency/                     # AI agency toolkit (6 plugins)
│   └── community/                      # Community-contributed plugins
├── templates/                          # 4 plugin starter templates
│   ├── minimal-plugin/                # Bare minimum structure
│   ├── command-plugin/                # With slash commands
│   ├── agent-plugin/                  # With AI subagent
│   └── full-plugin/                   # All features
├── docs/                               # Documentation files
├── scripts/                            # Repository maintenance scripts
│   ├── validate-all.sh                # Comprehensive validation
│   ├── test-installation.sh           # Plugin installation testing
│   └── check-frontmatter.py           # Markdown frontmatter validation
└── .github/                            # GitHub workflows and templates
    └── workflows/
        ├── validate-plugins.yml       # CI validation
        ├── release.yml                # Release automation
        └── deploy-marketplace.yml      # GitHub Pages deployment
```

## Common Development Tasks

### Repository Setup and Initialization

```bash
# Initial setup (makes scripts executable, initializes git)
./setup.sh

# Manual alternative:
find . -type f -name "*.sh" -exec chmod +x {} \;
git init
git add .
git commit -m "Initial commit"
```

### Building and Testing

```bash
# Validate all plugins (runs before any deployment)
./scripts/validate-all.sh

# Validate specific directory
./scripts/validate-all.sh plugins/mcp/

# Test plugin installation locally
./scripts/test-installation.sh

# Check markdown frontmatter
python3 scripts/check-frontmatter.py

# For MCP plugins with Node.js (if applicable)
pnpm install
pnpm build
pnpm test
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

# Test the plugin
/my-command  # For slash commands
```

### Adding a New Plugin to Marketplace

1. **Create plugin directory**: `plugins/community/your-plugin/`
2. **Ensure required files**:
   - `.claude-plugin/plugin.json` (metadata)
   - `README.md` (documentation)
   - `LICENSE` (MIT or Apache-2.0)
   - At least one component (commands/, agents/, hooks/, mcp/, or scripts/)

3. **Update marketplace catalog** in `.claude-plugin/marketplace.json`:
```json
{
  "name": "your-plugin",
  "source": "./plugins/community/your-plugin",
  "description": "Clear one-line description",
  "version": "1.0.0",
  "category": "productivity",
  "keywords": ["keyword1", "keyword2"],
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  }
}
```

4. **Validate and test**:
```bash
# Validate structure
./scripts/validate-all.sh plugins/community/your-plugin/

# Test locally
./scripts/test-installation.sh your-plugin
```

5. **Submit PR** using `.github/PULL_REQUEST_TEMPLATE.md`

## Plugin Architecture

### Plugin Components

Each plugin can contain:
- **Slash Commands** (`commands/*.md`) - Custom shortcuts triggered with `/command-name`
- **Subagents** (`agents/*.md`) - Specialized AI agents for specific domains
- **Hooks** (`hooks/hooks.json`) - Event-driven automation (PostToolUse, PreToolUse, etc.)
- **MCP Servers** (`mcp/*.json`) - Connections to external tools/services
- **Scripts** (`scripts/*.sh`) - Shell scripts called by hooks or commands

### Required Plugin Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json                    # Plugin metadata (REQUIRED)
├── README.md                          # Documentation (REQUIRED)
├── LICENSE                            # License file (REQUIRED)
└── [commands|agents|hooks|mcp|scripts]/ # At least one component
```

### plugin.json Schema

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Clear description",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "repository": "https://github.com/username/repo",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"]
}
```

## MCP Server Plugins

The repository includes 5 MCP server plugins providing 21 tools total:

1. **project-health-auditor** (4 tools) - Code complexity, git churn, test coverage analysis
2. **conversational-api-debugger** (4 tools) - OpenAPI/HAR debugging with root cause analysis
3. **domain-memory-agent** (6 tools) - TF-IDF semantic search knowledge base
4. **design-to-code** (3 tools) - Figma/screenshot to React/Svelte/Vue conversion
5. **workflow-orchestrator** (4 tools) - DAG-based workflow automation

MCP plugins may require additional setup:
```bash
# For Node.js based MCP servers
cd plugins/mcp/[plugin-name]/
npm install
npm run build
```

## Critical Conventions

### Path Variables
Always use `${CLAUDE_PLUGIN_ROOT}` in hooks for portable paths:
```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/process.sh"
}
```

### Script Permissions
All shell scripts MUST be executable:
```bash
chmod +x scripts/*.sh
find . -type f -name "*.sh" -exec chmod +x {} \;
```

### Versioning
Follow semantic versioning (MAJOR.MINOR.PATCH):
- `1.0.0` - Initial release
- `1.1.0` - New feature, backward compatible
- `1.1.1` - Bug fix
- `2.0.0` - Breaking change

### Plugin Categories
Valid categories: `productivity`, `security`, `testing`, `deployment`, `documentation`, `analysis`, `integration`, `ai`, `devops`, `debugging`, `code-quality`, `design`, `example`, `other`

## GitHub Workflows

### Automated Validation (CI)
- **File**: `.github/workflows/validate-plugins.yml`
- **Triggers**: Push to main, PRs
- **Validates**: JSON syntax, required files, script permissions

### Release Process
- **File**: `.github/workflows/release.yml`
- **Creates**: GitHub releases with changelog
- **Tags**: Semantic versioning

### Marketplace Deployment
- **File**: `.github/workflows/deploy-marketplace.yml`
- **Deploys**: GitHub Pages site (if configured)

## Security Requirements

1. **Never hardcode secrets** - Use environment variables
2. **Validate all inputs** in scripts
3. **Use `${CLAUDE_PLUGIN_ROOT}`** for portable paths
4. **Request minimal permissions**
5. **No destructive operations** without explicit user confirmation
6. **All `.sh` files must be executable** (`chmod +x`)

## Marketplace Usage

Users install plugins from this marketplace with:
```bash
# Add marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install plugins
/plugin install devops-automation-pack@claude-code-plugins
/plugin install project-health-auditor@claude-code-plugins
/plugin install git-commit-smart@claude-code-plugins
```

## Important Notes

- **NOT GitHub Marketplace**: Claude Code plugins use their own ecosystem
- **Free and open-source**: No built-in monetization
- **Beta status**: Features may evolve (October 2025 public beta)
- **Community-driven**: Accepting quality contributions via PR
- **Educational focus**: Examples should teach concepts clearly

## Troubleshooting

### Common Issues
- **Commands not appearing** → Validate `plugin.json` syntax, check `commands/` exists
- **Scripts not executing** → Verify `chmod +x`, check shebang `#!/bin/bash`
- **Hooks not firing** → Validate `hooks.json`, test matcher patterns
- **Path errors** → Use `${CLAUDE_PLUGIN_ROOT}` not absolute paths
- **JSON validation fails** → Run `jq empty file.json` to check syntax

### Validation Commands
```bash
# Check all JSON files
find . -name "*.json" -exec sh -c 'echo "Checking {}"; jq empty {}' \;

# Verify script permissions
find . -name "*.sh" -ls | grep -v rwx

# Test marketplace entry
jq '.plugins[] | select(.name == "plugin-name")' .claude-plugin/marketplace.json
```

## Resources

- **Official Docs**: https://docs.claude.com/en/docs/claude-code/plugins
- **Plugin Reference**: https://docs.claude.com/en/docs/claude-code/plugins-reference
- **Discord Community**: https://discord.com/invite/6PPFFzqPDZ (#claude-code channel)
- **GitHub Issues**: https://github.com/jeremylongshore/claude-code-plugins/issues
- **Contributing Guide**: See CONTRIBUTING.md

---

**Last Updated:** October 2025
**Repository Version:** 1.1.0
**Status:** Active, accepting community contributions