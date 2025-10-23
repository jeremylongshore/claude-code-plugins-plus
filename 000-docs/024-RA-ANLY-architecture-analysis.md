# Claude Code Plugins Repository - Architecture Analysis

**Date:** 2025-10-16  
**Repository:** /home/jeremy/000-projects/claude-code-plugins  
**Current Version:** 1.0.39  
**Status:** Active (Public Beta - October 2025)  
**Plugins:** 226 total across 14 categories

---

## 1. REPOSITORY OVERVIEW

### Purpose
A comprehensive marketplace and educational hub for Claude Code plugins. Serves as:
- Distribution platform for discovering and installing Claude Code plugins
- Educational resource with working examples and templates
- Community contribution platform for plugin developers

### Key Statistics
- **226 marketplace plugins** across 14 categories
- **5 MCP Server plugins** (21 MCP tools total) - executable TypeScript/JavaScript
- **4 plugin packs** (62 AI instruction templates) - guidance-based plugins
- **6 AI agency toolkit plugins** - business automation templates
- **3 example plugins** - learning resources
- **4 plugin templates** - starter scaffolding

---

## 2. MAIN DIRECTORIES & STRUCTURE

### Root-Level Organization

```
claude-code-plugins/
├── .claude-plugin/              # Plugin marketplace catalogs
│   ├── marketplace.extended.json    # Source (comprehensive metadata)
│   └── marketplace.json         # Generated (CLI catalog - synced)
├── .github/                     # CI/CD and automation
│   ├── workflows/               # GitHub Actions
│   └── ISSUE_TEMPLATE/          # Issue templates
├── .claude/                     # Claude-specific configuration
├── plugins/                     # 226 plugins across 14 categories
│   ├── mcp/                     # 5 executable MCP server plugins
│   ├── packages/                # 4 plugin pack collections
│   ├── examples/                # 3 example plugins for learning
│   ├── devops/                  # DevOps + deployment (25+ plugins)
│   ├── ai-ml/                   # AI/ML engineering (25+ plugins)
│   ├── security/                # Security & compliance (25+ plugins)
│   ├── crypto/                  # Blockchain & crypto (25+ plugins)
│   ├── database/                # Database tools (25+ plugins)
│   ├── testing/                 # Testing frameworks (25+ plugins)
│   ├── api-development/         # API design & development (25+ plugins)
│   ├── performance/             # Performance optimization (25+ plugins)
│   ├── productivity/            # Productivity tools
│   ├── ai-agency/               # 6 business automation templates
│   ├── finance/                 # Finance & trading tools
│   └── community/               # Community-contributed plugins
├── marketplace/                 # Astro-based marketplace website
│   ├── src/                     # Website source code
│   │   ├── components/          # Reusable React components
│   │   ├── content/             # Markdown content/pages
│   │   ├── layouts/             # Page layouts
│   │   ├── pages/               # Astro pages
│   │   └── styles/              # Tailwind CSS styles
│   ├── public/                  # Static assets
│   ├── dist/                    # Built site (GitHub Pages deployment)
│   └── package.json             # Astro dependencies
├── templates/                   # 4 plugin starter templates
│   ├── minimal-plugin/          # Bare minimum structure
│   ├── command-plugin/          # With slash commands
│   ├── agent-plugin/            # With AI subagent
│   └── full-plugin/             # All features
├── scripts/                     # Repository maintenance
│   ├── validate-all.sh          # Comprehensive validation
│   ├── sync-marketplace.cjs     # Generate CLI marketplace catalog
│   ├── check-frontmatter.py     # Markdown frontmatter validation
│   ├── test-installation.sh     # Plugin installation testing
│   └── utilities/               # Helper scripts
├── docs/                        # User documentation
│   ├── USER_SECURITY_GUIDE.md   # Safe plugin evaluation
│   ├── creating-plugins.md      # Plugin creation tutorial
│   ├── getting-started.md       # Quick start guide
│   ├── monetization-alternatives.md
│   └── learning-paths/          # Structured learning guides
├── archive/                     # Historical documentation
└── audit-reports/               # Security audits & reports
```

---

## 3. TECHNOLOGY STACK

### Build System & Package Management

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Workspace** | pnpm (workspace) | - | Monorepo package manager |
| **Root Build** | Node.js | 20+ | Script runtime |
| **CLI Sync** | Node.js CommonJS | - | Marketplace catalog generation |
| **Marketplace** | Astro | ^5.14.5 | Static site generator |
| **Styling** | Tailwind CSS | ^4.1.14 | Utility-first CSS framework |
| **MCP Plugins** | TypeScript | ^5.5.0 | Compiled executables |

### Development Tools

```json
Root package.json devDependencies:
- typescript: ^5.5.0         # TypeScript compiler
- vitest: ^2.0.0             # Testing framework
- eslint: ^9.0.0             # Linting
- prettier: ^3.3.0           # Code formatting
- @types/node: ^20.19.21     # Node.js types
```

### MCP Plugin Stack (Each Plugin)

```json
- @modelcontextprotocol/sdk: ^0.7.0  # MCP server framework
- zod: ^3.23.0                       # Runtime type validation
- glob: ^11.0.0                      # File pattern matching
- simple-git: ^3.25.0                # Git operations
- tsx: watch mode development
- tsc: TypeScript compilation
```

---

## 4. KEY CONFIGURATION FILES

### `.claude-plugin/marketplace.extended.json` (Source)
**Purpose:** Master catalog with comprehensive plugin metadata

**Structure:**
```json
{
  "name": "claude-code-plugins-plus",
  "owner": { "name": "Jeremy Longshore", "url": "..." },
  "metadata": {
    "description": "...",
    "version": "1.0.39",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "sugar",
      "source": "./plugins/devops/sugar",
      "description": "...",
      "version": "2.0.0",
      "category": "devops",
      "keywords": [...],
      "author": {...},
      "featured": true,
      "mcpTools": 7
    },
    // 225 more plugins...
  ]
}
```

**Key Field Categories:**
- `source` - Relative path to plugin directory
- `category` - 14 valid categories (devops, security, ai-ml, etc.)
- `keywords` - Searchable tags
- `featured` - Display on marketplace front page
- `mcpTools` - Number of MCP tools (MCP plugins only)
- `repository` - External GitHub/repo link

### `.claude-plugin/marketplace.json` (Generated - CLI Catalog)
**Purpose:** Generated output synced from `marketplace.extended.json`

**Generation Trigger:** `pnpm run sync-marketplace` or `npm run sync-marketplace`

**Usage:** Claude CLI uses this for `/plugin install` commands

### `pnpm-workspace.yaml`
```yaml
packages:
  - 'plugins/mcp/*'    # All MCP server plugins
  - 'marketplace'      # Astro marketplace website
```

**Purpose:** Defines workspace packages for monorepo

### Root `package.json`
**Workspace Scripts:**
```json
"scripts": {
  "dev": "pnpm --filter '*' dev --parallel",
  "build": "pnpm --filter '*' build",
  "test": "pnpm --filter '*' test",
  "lint": "pnpm --filter '*' lint",
  "typecheck": "pnpm --filter '*' typecheck",
  "sync-marketplace": "node scripts/sync-marketplace.cjs"
}
```

**Critical:** These run across ALL workspace packages (MCP plugins + marketplace)

### Marketplace `package.json`
```json
{
  "name": "marketplace",
  "type": "module",
  "version": "3.0.0",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview"
  },
  "dependencies": {
    "astro": "^5.14.5",
    "tailwindcss": "^4.1.14"
  }
}
```

---

## 5. TESTING & VALIDATION SETUP

### Validation Scripts (shell-based)

#### `validate-all.sh` - Comprehensive Validator
**Function:** Pre-deployment plugin quality checks

**Checks Performed:**
1. **JSON Schema Validation**
   - Parse all JSON files with `jq`
   - Verify `plugin.json` has required fields (name, version, description)

2. **File Structure Validation**
   - Check for `.claude-plugin/plugin.json`
   - Check for `README.md` with metadata
   - Verify `LICENSE` file exists

3. **Script Permissions**
   - All shell scripts must have execute flag (`chmod +x`)

4. **Markdown Frontmatter**
   - Slash commands require YAML frontmatter
   - Agents require YAML frontmatter

**Usage:**
```bash
./scripts/validate-all.sh              # Validate all plugins
./scripts/validate-all.sh plugins/mcp/ # Validate MCP plugins only
```

**Exit Codes:** Non-zero on error, triggers CI failure

#### `sync-marketplace.cjs` - Catalog Generator
**Function:** Generate CLI marketplace.json from marketplace.extended.json

**Process:**
1. Read `marketplace.extended.json`
2. Apply transformations/filtering
3. Write `marketplace.json`
4. CI verifies no differences (prevents manual edits)

**Trigger:** Must run after editing `marketplace.extended.json`

#### `check-frontmatter.py` - Markdown Validator
**Purpose:** Validate YAML frontmatter in command/agent markdown files

**Checks:**
- YAML format correctness
- Required fields per component type
- Encoding issues

#### `test-installation.sh` - Installation Tester
**Purpose:** Test local plugin installation workflow

**Process:**
1. Create test marketplace
2. Point to local plugin
3. Run plugin installation
4. Verify installation succeeds

### CI/CD Workflows (GitHub Actions)

#### `validate-plugins.yml` - Pull Request Validation
**Triggers:** PRs to main, pushes to main

**Jobs:**
1. Sync CLI marketplace catalog check
2. Validate JSON files syntax
3. Check plugin structure completeness
4. Verify script permissions
5. Markdown frontmatter validation

**Status Check:** Required before merge

#### `release.yml` - Semantic Versioning
**Triggers:** Manual workflow dispatch or version tag push

**Actions:**
- Create GitHub releases
- Generate changelogs
- Apply semantic version tags

#### `deploy-marketplace.yml` - Site Deployment
**Triggers:** Pushes to main

**Deployment:**
- Build Astro site
- Deploy to GitHub Pages
- Live at https://claudecodeplugins.io/

#### `codeql.yml` - Security Analysis
**Purpose:** Detect code vulnerabilities with CodeQL

#### `security-audit.yml` - Dependency Audit
**Purpose:** Check for vulnerable npm/node dependencies

#### `automerge.yml` & `maintainer-ready-automerge.yml`
**Purpose:** Auto-merge approved PRs from maintainers

---

## 6. PLUGIN ARCHITECTURE

### Two Plugin Types

#### 1. AI Instruction Plugins (Majority: 215+)
- **What:** Detailed markdown instructions guiding Claude's behavior
- **How:** Work through Claude's interpretation (no code execution)
- **Examples:** DevOps pack, Security pack, all category plugins
- **Size:** Text-based (varies by complexity)
- **Execution:** Interpreted by Claude

#### 2. MCP Server Plugins (5 plugins)
- **What:** Real TypeScript/JavaScript applications
- **How:** Run as separate Node.js processes Claude can call
- **Examples:** project-health-auditor, conversational-api-debugger
- **Size:** 13-26KB compiled executables
- **Execution:** Compiled, executable code

### Plugin Components (Optional)

Each plugin can contain:

| Component | Location | Purpose | Format |
|-----------|----------|---------|--------|
| **Slash Commands** | `commands/*.md` | Custom shortcuts `/command-name` | Markdown + YAML frontmatter |
| **Subagents** | `agents/*.md` | Specialized AI agents for domains | Markdown + YAML frontmatter |
| **Hooks** | `hooks/hooks.json` | Event-driven automation | JSON (PostToolUse, PreToolUse, etc.) |
| **MCP Servers** | `mcp/*.json` | External tool connections | JSON configurations |
| **Scripts** | `scripts/*.sh` | Shell automation | Bash scripts (require `chmod +x`) |

### Required Plugin Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json                  # REQUIRED: Plugin metadata
├── README.md                        # REQUIRED: Documentation
├── LICENSE                          # REQUIRED: License file (MIT or Apache-2.0)
└── [commands|agents|hooks|mcp|scripts]/  # At least one component
```

### `plugin.json` Schema

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

---

## 7. MCP SERVER PLUGINS (5 Executable Plugins)

### 1. project-health-auditor
**Type:** Executable MCP Plugin  
**Size:** 13KB (TypeScript)  
**Tools:** 4
- `list_repo_files` - Enumerate repository files
- `file_metrics` - Complexity analysis
- `git_churn` - Git change frequency
- `map_tests` - Test coverage mapping

**Purpose:** Multi-dimensional code health analysis

### 2. conversational-api-debugger
**Type:** Executable MCP Plugin  
**Size:** 26KB (JavaScript)  
**Tools:** 4
- `load_openapi` - Parse OpenAPI specs
- `ingest_logs` - Import HTTP logs (HAR)
- `explain_failure` - Root cause analysis
- `make_repro` - Create test cURL commands

**Purpose:** REST API failure debugging

### 3. domain-memory-agent
**Type:** Executable MCP Plugin  
**Tools:** 6
- `store_document` - Add to knowledge base
- `semantic_search` - TF-IDF ranking
- `summarize` - Extractive summaries
- `list_documents` - Browse documents
- `get_document` - Retrieve specific doc
- `delete_document` - Remove from base

**Purpose:** Knowledge base with semantic search

### 4. design-to-code
**Type:** Executable MCP Plugin  
**Tools:** 3
- `parse_figma` - Extract from Figma JSON
- `analyze_screenshot` - Parse UI layouts
- `generate_component` - Output React/Svelte/Vue

**Purpose:** Design to production code conversion

### 5. workflow-orchestrator
**Type:** Executable MCP Plugin  
**Tools:** 4
- `create_workflow` - Define DAG workflows
- `execute_workflow` - Run with dependencies
- `get_workflow` - Retrieve state
- `list_workflows` - All workflows

**Purpose:** DAG-based task automation

### Additional AI-Experiment-Logger (6th Detected)
**Present in:** `/plugins/mcp/ai-experiment-logger/`

---

## 8. PLUGIN CATEGORIES (14 Total)

| Category | Location | Examples | Count |
|----------|----------|----------|-------|
| **DevOps** | `plugins/devops/` | git-commit-smart, sugar, deployment tools | 25+ |
| **AI/ML** | `plugins/ai-ml/` | Prompt optimization, RAG systems, LLM patterns | 25+ |
| **Security** | `plugins/security/` | OWASP audit, compliance, threat modeling | 25+ |
| **API Development** | `plugins/api-development/` | OpenAPI, REST patterns, API design | 25+ |
| **Database** | `plugins/database/` | Schema design, Prisma, PostgreSQL patterns | 25+ |
| **Testing** | `plugins/testing/` | Unit, integration, E2E patterns | 25+ |
| **Crypto** | `plugins/crypto/` | Blockchain, trading, DeFi tools | 25+ |
| **Performance** | `plugins/performance/` | Optimization, profiling, benchmarking | 25+ |
| **Productivity** | `plugins/productivity/` | Workflow, task management | Variable |
| **Finance** | `plugins/finance/` | Trading, ROI, financial analysis | New category |
| **AI Agency** | `plugins/ai-agency/` | n8n, Zapier, Make templates | 6 |
| **Examples** | `plugins/examples/` | hello-world, formatter, security-agent | 3 |
| **Packages** | `plugins/packages/` | DevOps, Security, Fullstack, AI/ML packs | 4 |
| **Community** | `plugins/community/` | User-contributed plugins | Varies |

---

## 9. DOCUMENTATION STRUCTURE

### Root-Level Documentation

| File | Purpose |
|------|---------|
| `README.md` | Main overview, quick start, plugin listings |
| `CONTRIBUTING.md` | Submission guidelines, plugin requirements |
| `SECURITY.md` | Vulnerability reporting, security policy |
| `CHANGELOG.md` | Version history, release notes |
| `CODE_OF_CONDUCT.md` | Community standards, reporting issues |
| `SETUP.md` | Initial setup instructions |

### Docs Directory (`/docs/`)

| File | Purpose |
|------|---------|
| `USER_SECURITY_GUIDE.md` | How to safely evaluate plugins |
| `creating-plugins.md` | Step-by-step plugin creation tutorial |
| `getting-started.md` | Quick start guide for users |
| `monetization-alternatives.md` | Revenue strategies for creators |
| `learning-paths/` | Structured learning guides (beginner→expert) |

### Learning Paths Structure
```
learning-paths/
├── 01-quick-start/              # 15 min: First plugin installation
├── 02-plugin-creator/           # 3 hours: Build first plugin
├── 03-advanced-developer/       # 1 day: Production MCP servers
└── use-cases/
    ├── devops-engineer.md
    ├── security-specialist.md
    ├── ai-ml-developer.md
    └── crypto-trader.md
```

---

## 10. BUILD & DEPLOYMENT

### Development Workflow

```bash
# Install dependencies (monorepo)
pnpm install

# Development mode (all packages)
pnpm dev

# Build all packages
pnpm build

# Test all packages
pnpm test

# Lint code
pnpm lint

# Type checking
pnpm typecheck

# Sync marketplace catalog (must run after editing marketplace.extended.json)
pnpm run sync-marketplace
```

### Marketplace-Specific Build

```bash
cd marketplace/

# Development server
npm run dev          # localhost:4321

# Production build
npm run build        # generates dist/

# Preview production
npm run preview
```

### MCP Plugin Build (Individual)

```bash
cd plugins/mcp/[plugin-name]/

# Development with watch
pnpm dev

# Compile to JavaScript
pnpm build

# Run tests
pnpm test
```

### CI/CD Pipeline (GitHub Actions)

1. **Push to main** or **Pull Request** → Trigger CI
2. **validate-plugins.yml** runs:
   - JSON validation
   - Plugin structure check
   - Script permissions check
   - Markdown frontmatter validation
3. **If all pass** → Allow merge
4. **On merge to main** → 
   - Run security scans (CodeQL, audit)
   - Deploy marketplace (GitHub Pages)

---

## 11. CRITICAL CONVENTIONS & CONSTRAINTS

### Path Variables
All plugins use portable paths:
```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/process.sh"
}
```
NOT absolute paths - ensures cross-platform compatibility

### Script Permissions
**REQUIREMENT:** All shell scripts MUST be executable
```bash
chmod +x scripts/*.sh
find . -type f -name "*.sh" -exec chmod +x {} \;
```
**CI Check:** Fails if any scripts lack execute permission

### Versioning
Follow semantic versioning (MAJOR.MINOR.PATCH):
- `1.0.0` - Initial release
- `1.1.0` - New feature, backward compatible
- `1.1.1` - Bug fix
- `2.0.0` - Breaking change

### JSON Validation
All JSON must be valid:
```bash
jq empty file.json  # Validate syntax
```

### Markdown Frontmatter (Commands & Agents)
**Required for:** Any command or agent markdown file

**Format:**
```yaml
---
title: Command Name
description: What it does
keywords: [tag1, tag2]
---
Command content...
```

### Plugin.json Requirements
**REQUIRED fields:**
- `name` - Unique identifier
- `version` - Semantic version
- `description` - 1-line summary

**OPTIONAL fields:**
- `author` - Creator info
- `repository` - Source code URL
- `license` - License type
- `keywords` - Search tags

---

## 12. MONOREPO ARCHITECTURE

### Workspace Structure (pnpm-workspace.yaml)

```yaml
packages:
  - 'plugins/mcp/*'    # All 5-6 MCP executable plugins
  - 'marketplace'      # Astro website
```

### Implications

1. **Shared Dependencies:** Root `package.json` defines devDependencies for all packages
2. **Root Scripts Run Everywhere:** `pnpm dev`, `pnpm build`, etc. execute in all packages
3. **Filtered Execution:** `pnpm --filter package-name` targets specific package
4. **Shared TypeScript:** All MCP plugins use root `tsconfig.json` or their own

### Commands

```bash
# Run script in specific package
pnpm --filter project-health-auditor build

# Run in all packages
pnpm build

# Run in parallel
pnpm --parallel dev
```

---

## 13. SECURITY & COMPLIANCE

### Security Review (GitHub Actions)
- **CodeQL scanning** - Detects code vulnerabilities
- **Dependency audit** - npm audit for vulnerable packages
- **Script validation** - No dangerous shell patterns

### Plugin Requirements
- **No hardcoded secrets** - Use environment variables
- **Input validation** - Sanitize all external inputs
- **Portable paths** - Use `${CLAUDE_PLUGIN_ROOT}`
- **No destructive operations** - Without user confirmation

### Threat Model (from SECURITY.md)
- Plugin hijacking prevention
- Supply chain security
- Malicious plugin detection
- User data protection

---

## 14. DEPLOYMENT & DISTRIBUTION

### Marketplace Catalog Distribution

**How plugins reach users:**

1. **Source:** `marketplace.extended.json` (in repo)
2. **Generation:** `pnpm run sync-marketplace` → `marketplace.json`
3. **Distribution:** Users add marketplace:
   ```bash
   /plugin marketplace add jeremylongshore/claude-code-plugins
   ```
4. **Installation:** Claude CLI reads marketplace.json:
   ```bash
   /plugin install plugin-name@claude-code-plugins-plus
   ```

### Website Deployment

**Marketplace Website:**
- **Build:** `npm run build` in marketplace/
- **Output:** `dist/` directory
- **Deploy:** GitHub Pages via `deploy-marketplace.yml`
- **Live:** https://claudecodeplugins.io/

---

## 15. KEY METRICS & STATS

| Metric | Value |
|--------|-------|
| **Total Plugins** | 226 |
| **MCP Executables** | 5-6 |
| **Plugin Packs** | 4 (62 components) |
| **Categories** | 14 |
| **Plugin Templates** | 4 |
| **Example Plugins** | 3 |
| **Marketplace Version** | 3.0.0 |
| **Repository Version** | 1.0.39 |
| **Node.js Version** | 20+ |
| **Astro Version** | ^5.14.5 |
| **TypeScript Version** | ^5.5.0 |

---

## 16. NOTABLE FEATURES

### Plugin Pack System
Pre-bundled collections of related plugins:
- **DevOps Automation Pack** (25 plugins)
- **Security Pro Pack** (10 plugins)
- **Fullstack Starter Pack** (15 plugins)
- **AI/ML Engineering Pack** (12 plugins)

### AI Agency Toolkit
Business automation templates:
- n8n workflow designer
- Make.com scenario builder
- Zapier zap builder
- Discovery questionnaire
- SOW generator
- ROI calculator

### Learning Paths
Structured progression:
- Quick Start (15 min)
- Plugin Creator (3 hours)
- Advanced Developer (1 day)
- Use case specific paths

### Community-Driven
- Accept plugin submissions via PR
- 1 external contributor already (cdnsteve/sugar)
- Active GitHub discussions
- 40K+ member Discord community

---

## SUMMARY

This is a **production-grade plugin marketplace** with:

✅ **Comprehensive Structure:** 226 plugins across 14 categories  
✅ **Dual Plugin Types:** AI instruction + executable MCP servers  
✅ **Quality Assurance:** Multi-layer validation (JSON, structure, permissions)  
✅ **CI/CD Automation:** GitHub Actions for validation and deployment  
✅ **Monorepo Architecture:** pnpm workspace managing MCP plugins + website  
✅ **Educational Focus:** Templates, examples, and structured learning paths  
✅ **Professional Website:** Astro + Tailwind marketplace at claudecodeplugins.io  
✅ **Community Ready:** Clear submission guidelines and contribution templates  
✅ **Security Conscious:** Audits, dependency checks, threat modeling  
✅ **Scalable Design:** Extensible catalog system, plugin discovery

The repository follows software engineering best practices with clear organization, automated testing, semantic versioning, and professional documentation.

