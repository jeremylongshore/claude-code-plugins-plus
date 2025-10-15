# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is **the comprehensive marketplace and learning hub for Claude Code plugins**. It serves as both a distribution platform for plugins and an educational resource for plugin developers.

**Repository Purpose:**
- Marketplace catalog for discovering and installing Claude Code plugins
- Educational hub with working examples and templates
- Community contribution platform for plugin developers
- **Current Stats: 220 marketplace plugins across 14 categories** (API development, AI/ML, security, DevOps, crypto, database, testing, performance, and more)

## Repository Structure

```
claude-code-plugins/
├── .claude-plugin/
│   ├── marketplace.extended.json       # Source catalog (full metadata for marketplace site)
│   └── marketplace.json                # Generated CLI catalog (sync via scripts/sync-marketplace.cjs)
├── plugins/                            # 14 plugin categories
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
│   ├── api-development/               # 25 API development plugins
│   ├── ai-ml/                         # 25 AI/ML plugins
│   ├── security/                      # 25 security plugins
│   ├── devops/                        # 25 DevOps plugins
│   ├── crypto/                        # 25 cryptocurrency/blockchain plugins
│   ├── database/                      # 25 database plugins
│   ├── testing/                       # 25 testing plugins
│   ├── performance/                   # 25 performance plugins
│   ├── productivity/                  # Productivity plugins
│   ├── ai-agency/                     # 6 AI agency toolkit plugins
│   └── community/                      # Community-contributed plugins
├── marketplace/                        # Astro-based marketplace website
│   ├── src/                           # Website source code
│   ├── public/                        # Static assets
│   ├── dist/                          # Built site (deployed to GitHub Pages)
│   └── package.json                   # Astro dependencies
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
├── pnpm-workspace.yaml                 # PNPM workspace config for MCP plugins
├── package.json                        # Root package.json for monorepo
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

# Regenerate CLI marketplace catalog after editing marketplace.extended.json
pnpm run sync-marketplace  # or: npm run sync-marketplace

# For MCP plugins with Node.js (if applicable)
pnpm install
pnpm build
pnpm test

# Marketplace website development
cd marketplace/
npm install
npm run dev        # Start dev server at localhost:4321
npm run build      # Build for production
npm run preview    # Preview production build
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

3. **Update marketplace catalog source** in `.claude-plugin/marketplace.extended.json`, then regenerate the CLI catalog with `pnpm run sync-marketplace` (or `npm run sync-marketplace`):
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

```bash
# Regenerate CLI marketplace.json for Claude CLI users
pnpm run sync-marketplace  # or: npm run sync-marketplace
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

### Two Types of Plugins

**1. AI Instruction Plugins** (majority of plugins - 215+)
- Detailed markdown instructions that guide Claude's behavior
- Work entirely through Claude's interpretation
- No external code execution required
- Examples: DevOps pack, security pack, all category plugins

**2. MCP Server Plugins** (5 plugins)
- Real TypeScript/JavaScript applications that run as separate Node.js processes
- Actual compiled code (13-26KB executables)
- Examples: project-health-auditor, conversational-api-debugger

### Plugin Components

Each plugin can contain:
- **Slash Commands** (`commands/*.md`) - Custom shortcuts triggered with `/command-name`
- **Subagents** (`agents/*.md`) - Specialized AI agents for specific domains
- **Hooks** (`hooks/hooks.json`) - Event-driven automation (PostToolUse, PreToolUse, etc.)
- **MCP Servers** (`mcp/*.json`) - Connections to external tools/services (MCP plugins only)
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

### MCP Plugin Development

MCP plugins are TypeScript/Node.js applications built with the `@modelcontextprotocol/sdk`:

```bash
# Initial setup for MCP plugin development
pnpm install  # Install all MCP plugin dependencies (uses pnpm workspace)

# Build specific MCP plugin
cd plugins/mcp/[plugin-name]/
pnpm build

# Test specific MCP plugin
pnpm test

# Build all MCP plugins at once
pnpm build  # From repository root
```

Each MCP plugin has:
- `package.json` - Node.js dependencies (@modelcontextprotocol/sdk, zod, etc.)
- `src/` - TypeScript source code
- `dist/` - Compiled JavaScript (generated by `pnpm build`)
- `tsconfig.json` - TypeScript configuration

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
Valid categories: `productivity`, `security`, `testing`, `deployment`, `documentation`, `analysis`, `integration`, `ai`, `devops`, `debugging`, `code-quality`, `design`, `example`, `api-development`, `database`, `crypto`, `performance`, `ai-ml`, `other`

### Marketplace Website

The marketplace website is built with **Astro 5** and **Tailwind CSS v4**:

```bash
cd marketplace/

# Development
npm run dev        # Starts dev server at localhost:4321

# Production
npm run build      # Builds static site to dist/
npm run preview    # Preview production build locally
```

**Deployment**: Automatically deployed to GitHub Pages via `.github/workflows/deploy-marketplace.yml` on pushes to main branch.

**Live Site**: https://jeremylongshore.github.io/claude-code-plugins/

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
jq '.plugins[] | select(.name == "plugin-name")' .claude-plugin/marketplace.extended.json
```

## Resources

- **Official Docs**: https://docs.claude.com/en/docs/claude-code/plugins
- **Plugin Reference**: https://docs.claude.com/en/docs/claude-code/plugins-reference
- **Discord Community**: https://discord.com/invite/6PPFFzqPDZ (#claude-code channel)
- **GitHub Issues**: https://github.com/jeremylongshore/claude-code-plugins/issues
- **Contributing Guide**: See CONTRIBUTING.md
- **Code of Conduct**: See CODE_OF_CONDUCT.md

---

**Last Updated:** October 2025
**Repository Version:** 3.0.0 (220 plugins!)
**Status:** Active, accepting community contributions

---

## Key Development Principles

When working in this repository:

1. **Validate Before Committing**: Always run `./scripts/validate-all.sh` before committing
2. **Test Locally First**: Use the test marketplace pattern to verify plugins work
3. **Executable Scripts**: All `.sh` files must have execute permissions (`chmod +x`)
4. **JSON Validation**: Use `jq` to validate all JSON files
5. **Frontmatter Required**: All command and agent markdown files need YAML frontmatter
6. **Portable Paths**: Always use `${CLAUDE_PLUGIN_ROOT}` in hooks, never absolute paths
7. **Documentation First**: Every plugin needs comprehensive README.md
8. **Security Conscious**: No hardcoded secrets, validate inputs, minimal permissions
