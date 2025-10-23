# Claude Code Plugins - Quick Reference Guide

**Generated:** 2025-10-16  
**Version:** 1.0.39

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Repository Type** | Plugin marketplace + monorepo |
| **Total Plugins** | 226 across 14 categories |
| **Plugin Types** | 221 AI instructions + 5 MCP executables |
| **Build System** | pnpm workspace (Node.js 20+) |
| **Website** | Astro 5 + Tailwind CSS 4 |
| **Deployment** | GitHub Pages + GitHub Actions |
| **License** | MIT |
| **Status** | Public Beta (October 2025) |

---

## Directory Map

```
Root-Level Essentials:
├── .claude-plugin/
│   ├── marketplace.extended.json    ← EDIT THIS for plugin changes
│   └── marketplace.json             ← GENERATED (auto-synced)
├── plugins/                         ← 14 plugin categories
├── marketplace/                     ← Astro website (claudecodeplugins.io)
├── scripts/                         ← Validation & sync tools
├── templates/                       ← Plugin starter templates
└── docs/                            ← User documentation
```

---

## Key Commands

### Development

```bash
# Install dependencies
pnpm install

# Development (all packages)
pnpm dev

# Build all packages
pnpm build

# Test & validate
pnpm test
pnpm lint
pnpm typecheck

# Sync marketplace after editing marketplace.extended.json
pnpm run sync-marketplace
```

### Marketplace Website

```bash
cd marketplace/

npm run dev          # localhost:4321
npm run build        # dist/ folder
npm run preview      # Test production
```

### MCP Specific

```bash
cd plugins/mcp/[plugin-name]/

pnpm dev             # Watch mode
pnpm build           # Compile TypeScript
pnpm test            # Run tests
```

### Validation

```bash
./scripts/validate-all.sh               # Full validation
./scripts/validate-all.sh plugins/mcp/  # MCP only
./scripts/test-installation.sh          # Installation test
python3 scripts/check-frontmatter.py    # Markdown check
```

---

## Plugin Categories (14)

| Category | Path | Count | Examples |
|----------|------|-------|----------|
| DevOps | `plugins/devops/` | 25+ | git-commit-smart, sugar |
| AI/ML | `plugins/ai-ml/` | 25+ | RAG, prompt optimization |
| Security | `plugins/security/` | 25+ | OWASP, compliance |
| API Dev | `plugins/api-development/` | 25+ | OpenAPI, REST |
| Database | `plugins/database/` | 25+ | Schema, Prisma |
| Testing | `plugins/testing/` | 25+ | Unit, E2E, patterns |
| Crypto | `plugins/crypto/` | 25+ | Blockchain, trading |
| Performance | `plugins/performance/` | 25+ | Optimization, profiling |
| Productivity | `plugins/productivity/` | Var | Workflow, tasks |
| Finance | `plugins/finance/` | New | Trading, ROI |
| AI Agency | `plugins/ai-agency/` | 6 | n8n, Zapier, Make |
| Examples | `plugins/examples/` | 3 | hello-world, formatter |
| Packages | `plugins/packages/` | 4 | DevOps pack, Security pack |
| Community | `plugins/community/` | Var | User contributions |

---

## Plugin Types Explained

### Type 1: AI Instruction Plugins (221 plugins)
- Text-based guidance for Claude
- No code execution
- Works through interpretation
- Examples: All category plugins, packs

### Type 2: MCP Executables (5 plugins)
- Real TypeScript/JavaScript code
- Runs as separate Node.js process
- Actual compiled binaries (13-26KB)
- Examples: project-health-auditor, conversational-api-debugger

---

## Plugin Structure (Required)

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # REQUIRED (name, version, description)
├── README.md                # REQUIRED (documentation)
├── LICENSE                  # REQUIRED (MIT or Apache-2.0)
└── [optional components]:
    ├── commands/            # Slash commands (*.md with frontmatter)
    ├── agents/              # Subagents (*.md with frontmatter)
    ├── hooks/               # Event triggers (hooks.json)
    ├── mcp/                 # MCP configs (*.json)
    └── scripts/             # Shell scripts (chmod +x required)
```

---

## Marketplace Catalog Workflow

```
1. Developer edits marketplace.extended.json
   ↓
2. Developer runs: pnpm run sync-marketplace
   ↓
3. marketplace.json is regenerated
   ↓
4. CI verifies no manual edits to marketplace.json
   ↓
5. Claude CLI users see changes after merge to main
```

---

## CI/CD Pipeline

| Trigger | Workflow | Checks |
|---------|----------|--------|
| **PR to main** | validate-plugins.yml | JSON, structure, permissions, frontmatter |
| **Push to main** | validate-plugins.yml + deploy | Same checks + website build + deploy |
| **Any push** | security-audit.yml | CodeQL, npm audit |
| **Manual** | release.yml | Create GitHub releases |

---

## Technology Stack

### Root Level
- **Node.js:** 20+
- **pnpm:** Workspace manager
- **TypeScript:** 5.5.0
- **Vitest:** Testing framework
- **ESLint:** Linting
- **Prettier:** Formatting

### Marketplace
- **Astro:** 5.14.5
- **Tailwind CSS:** 4.1.14
- **React:** (for components)

### MCP Plugins
- **@modelcontextprotocol/sdk:** 0.7.0
- **Zod:** Runtime validation
- **simple-git:** Git operations

---

## Critical Conventions

### Requirement: Portable Paths
```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/process.sh"
}
```
NOT absolute paths!

### Requirement: Script Permissions
```bash
chmod +x scripts/*.sh
```
CI fails if scripts lack `x` flag

### Requirement: Semantic Versioning
- `1.0.0` - Release
- `1.1.0` - Feature
- `1.1.1` - Bugfix
- `2.0.0` - Breaking

### Requirement: JSON Validity
```bash
jq empty file.json  # Must parse
```

### Requirement: Markdown Frontmatter
```yaml
---
title: Command Name
description: What it does
keywords: [tag1, tag2]
---
```

---

## MCP Server Plugins (5)

| Plugin | Size | Tools | Purpose |
|--------|------|-------|---------|
| **project-health-auditor** | 13KB | 4 | Code complexity + churn + tests |
| **conversational-api-debugger** | 26KB | 4 | REST API debugging |
| **domain-memory-agent** | - | 6 | Semantic search knowledge base |
| **design-to-code** | - | 3 | Figma/screenshot → React/Vue |
| **workflow-orchestrator** | - | 4 | DAG task automation |

---

## Plugin Packs (4)

| Pack | Components | Purpose |
|------|-----------|---------|
| **devops-automation-pack** | 25 plugins | Git, CI/CD, Docker, Kubernetes, Terraform |
| **security-pro-pack** | 10 plugins | OWASP, compliance, cryptography |
| **fullstack-starter-pack** | 15 plugins | React, Express/FastAPI, PostgreSQL |
| **ai-ml-engineering-pack** | 12 plugins | Prompts, LLM, RAG, AI safety |

---

## Common Workflows

### Adding a New Plugin

1. Create directory: `plugins/[category]/[plugin-name]/`
2. Add `.claude-plugin/plugin.json`
3. Add `README.md` and `LICENSE`
4. Edit `.claude-plugin/marketplace.extended.json`
5. Run: `pnpm run sync-marketplace`
6. Validate: `./scripts/validate-all.sh`
7. Test: `./scripts/test-installation.sh`
8. Submit: Pull request with template

### Testing Locally

```bash
mkdir -p ~/test-marketplace/.claude-plugin
cat > ~/test-marketplace/.claude-plugin/marketplace.json << 'JSON'
{
  "name": "test",
  "owner": {"name": "Test"},
  "plugins": [{
    "name": "my-plugin",
    "source": "/absolute/path/to/plugins/community/my-plugin"
  }]
}
JSON

/plugin marketplace add ~/test-marketplace
/plugin install my-plugin@test
```

### Deploying Changes

```bash
# 1. Edit marketplace.extended.json
# 2. Sync catalog
pnpm run sync-marketplace

# 3. Validate
./scripts/validate-all.sh

# 4. Commit & push
git add .
git commit -m "feat: add new plugin"
git push origin feature/new-plugin

# 5. Create PR
# 6. Merge to main
# 7. CI automatically deploys
```

---

## File Organization

### Must Have
- `.claude-plugin/plugin.json` - Metadata
- `README.md` - Documentation
- `LICENSE` - License file

### Optional Components
- `commands/` - Slash commands
- `agents/` - AI subagents
- `hooks/hooks.json` - Event automation
- `mcp/` - MCP configurations
- `scripts/` - Shell scripts

### Project Metadata in marketplace.extended.json
- `name` - Unique identifier
- `source` - Path to plugin
- `description` - One-line summary
- `version` - Semantic version
- `category` - Valid category
- `keywords` - Search tags
- `author` - Creator info
- `featured` - Show on homepage
- `mcpTools` - MCP tool count

---

## Validation Checklist (Before PR)

- [ ] JSON files are valid (`jq empty file.json`)
- [ ] `plugin.json` has name, version, description
- [ ] `README.md` exists with examples
- [ ] `LICENSE` file present (MIT or Apache-2.0)
- [ ] Shell scripts executable (`chmod +x *.sh`)
- [ ] Markdown has YAML frontmatter
- [ ] Using `${CLAUDE_PLUGIN_ROOT}` for paths
- [ ] marketplace.extended.json updated
- [ ] Ran `pnpm run sync-marketplace`
- [ ] Ran `./scripts/validate-all.sh`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Commands not showing | Check `plugin.json` syntax, verify `commands/` exists |
| Scripts not running | Verify `chmod +x`, check shebang `#!/bin/bash` |
| Hooks not firing | Validate `hooks.json`, test matcher patterns |
| Path errors | Use `${CLAUDE_PLUGIN_ROOT}` not absolute paths |
| JSON validation fails | Run `jq empty file.json` to debug |
| Marketplace not syncing | Run `pnpm run sync-marketplace` manually |
| CI checks fail | Run local validation: `./scripts/validate-all.sh` |

---

## Important Notes

- **NOT GitHub Marketplace:** Uses custom Claude Code ecosystem
- **All Open Source:** MIT or Apache-2.0 licensed
- **Free Forever:** No monetization built-in (can use alternatives)
- **Beta Status:** Features may evolve (October 2025)
- **Community-Driven:** Accept submissions via PR

---

## Resources

| Resource | Link |
|----------|------|
| **Marketplace** | https://claudecodeplugins.io/ |
| **Official Docs** | https://docs.claude.com/en/docs/claude-code/ |
| **Discord** | https://discord.com/invite/6PPFFzqPDZ |
| **GitHub Issues** | https://github.com/jeremylongshore/claude-code-plugins/issues |
| **Contributing** | See CONTRIBUTING.md |
| **Security** | See SECURITY.md |

---

**Last Updated:** October 16, 2025  
**Quick Reference Version:** 1.0
