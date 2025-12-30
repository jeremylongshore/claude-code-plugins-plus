# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Task Tracking (Beads / bd)

### Critical Rules
- Use `bd` for ALL tasks/issues (no markdown TODO lists)
- **Git hooks MUST be installed**: Run `bd hooks install` (auto-syncs on commit/merge/push/checkout)
- **Never pollute production DB**: Use `BEADS_DIR` for testing/isolation
- **Landing the Plane is MANDATORY**: Work isn't done until `git push` succeeds

### Session Workflow
- **Start**: `bd ready` (shows ready-to-work tasks)
- **Create**: `bd create "Title" -p 1 --description "Context + criteria"`
- **Update**: `bd update <id> --status in_progress`
- **Close**: `bd close <id> --reason "Completed: <summary>"`
- **End**: `bd sync` (MANDATORY - exports, commits, pulls, pushes)

### Git Hooks (Installed)
- `pre-commit`: Flushes pending changes before commit
- `post-merge`: Imports updates after pulls
- `pre-push`: Exports database before pushing
- `post-checkout`: Ensures consistency on branch switches

### Testing Safety
- Use `BEADS_DIR=/tmp/beads-test` to isolate test workspace
- `BEADS_DB` exists but is deprecated
- Never create test issues in production (prefix "Test" triggers warning)

### Beads upgrades
- After upgrading `bd`, run: `bd info --whats-new`
- If `bd info` warns about hooks, run: `bd hooks install`

---

## ACTIVE PROJECT: 50-Vendor SaaS Skill Packs

**STATUS: In Progress (Dec 2025)**

**If working on SaaS packs, READ THIS FIRST:**
```bash
cat plugins/saas-packs/SAAS-PACKS-CONTEXT.md
```

**Quick Recovery:**
```bash
bd sync && bd list --status in_progress  # What was I doing?
cat plugins/saas-packs/TRACKER.csv | head -20  # Progress check
bd ready | head -10  # What's available?
```

**Key Files:**
- `plugins/saas-packs/SAAS-PACKS-CONTEXT.md` - Post-compaction recovery guide
- `plugins/saas-packs/TRACKER.csv` - Master progress tracking (50 companies)
- `/home/jeremy/.claude/plans/velvet-roaming-crown.md` - Full implementation plan

**Beads Epics:**
- `ccpi-saas` - Master epic (50-Vendor SaaS Skill Packs)
- `ccpi-saas-infra` - Infrastructure epic
- `ccpi-[vendor]` - Per-vendor epics (supabase, vercel, etc.)

---

## Repository Overview

Claude Code plugins marketplace and learning hub. 258 plugins across 22 categories with 239 Agent Skills. Live at https://claudecodeplugins.io/

**Monorepo structure:** pnpm workspaces (v9.15.9+) with:
- 7 MCP server plugins in `plugins/mcp/*` (TypeScript/Node.js)
- 251 instruction-based plugins in `plugins/[category]/*` (Markdown)
- Astro website in `marketplace/` (uses npm, not pnpm)
- Shared packages in `packages/` (CLI, validator, analytics)

**Package Manager Rules:**
- **Root & workspaces:** Use `pnpm` (enforced via CI)
- **Marketplace only:** Use `npm` (separate project)
- **Never use:** `npm` or `yarn` in workspace root (CI fails)

## Learning Lab

**Location:** `workspace/lab/` (git-ignored, safe sandbox for experiments)

**Purpose:** Production agent workflow teaching system with empirical verification patterns - teaches how to build agent systems that use scripts to verify LLM outputs instead of trusting them.

**Key Resources:**
- `README.md` - 5-minute introduction to the learning lab
- `GUIDE-00-START-HERE.md` - Mental model for agent workflows
- `GUIDE-01-PATTERN-EXPLAINED.md` - Architecture deep dive (15 min)
- `GUIDE-02-BUILDING-YOUR-OWN.md` - Build your own workflow (30 min)
- `GUIDE-03-DEBUGGING-TIPS.md` - Debugging techniques (15 min)
- `ORCHESTRATION-PATTERN.md` - Complete orchestration pattern (60 min)
- `VISUAL-MAP.md` - Visual architecture diagrams
- `BUILT-SYSTEM-SUMMARY.md` - Summary of reference implementation
- `schema-optimization/` - Reference implementation with 5-phase workflow
- `exercises/` - Hands-on exercises

**Interactive Tutorials:** `tutorials/` directory (11 Jupyter notebooks)
- Skills tutorials (5 notebooks) - How Agent Skills work
- Plugins tutorials (4 notebooks) - Plugin development
- Orchestration tutorials (2 notebooks) - Multi-agent workflows
- Available on Google Colab for instant access

**Note:** workspace/ is git-ignored except for committed lab materials. Safe for experimentation.

## Essential Commands

### Most Common Operations
```bash
# Before ANY commit (MANDATORY)
pnpm run sync-marketplace           # Sync catalog files
./scripts/validate-all-plugins.sh   # Full validation (or use quick-test.sh)
git add .claude-plugin/marketplace.json  # Commit BOTH catalog files

# Quick development workflow
pnpm install                        # Fresh install (uses frozen lockfile)
pnpm build                          # Build all packages
pnpm test                           # Run all tests
bash scripts/quick-test.sh          # Fast pre-commit check (~30s)

# Local plugin testing
/plugin marketplace add /home/jeremy/000-projects/claude-code-plugins
/plugin install [plugin-name]@claude-code-plugins-plus
```

### Before ANY Commit (Detailed)
```bash
pnpm run sync-marketplace           # Regenerates marketplace.json from .extended.json
./scripts/validate-all-plugins.sh   # Full validation suite (or quick-test.sh)
```

### Build & Test
```bash
pnpm install                        # Install all dependencies (frozen lockfile in CI)
pnpm build                          # Build all MCP plugins
pnpm test                           # Run all tests
pnpm typecheck                      # TypeScript validation
pnpm lint                           # ESLint
```

### Quick Testing
```bash
bash scripts/quick-test.sh          # Fast validation (~30s)
bash scripts/test-clean-environment.sh  # Full clean environment test (~2-5 min)
bash scripts/test-docker-suite.sh   # Docker-based isolated test (~5-10 min)
```

### Single MCP Plugin Development
```bash
cd plugins/mcp/[plugin-name]/
pnpm build                          # Compile TypeScript → dist/
pnpm test                           # Run plugin tests
pnpm dev                            # Development mode with watch
```

### Marketplace Website
```bash
cd marketplace/
npm run dev                         # Dev server at localhost:4321
npm run build                       # Production build (auto-deploys on push)
npm run preview                     # Test production build locally
```

### Validation Scripts
```bash
./scripts/validate-all-plugins.sh                    # Full validation (all 6 stages)
./scripts/validate-all-plugins.sh plugins/mcp/foo/   # Single plugin validation
python3 scripts/validate-skills-schema.py            # Skills 2025 schema compliance
python3 scripts/validate-frontmatter.py              # Markdown frontmatter validation
node scripts/validate-plugin.js                      # Plugin structure validation
node scripts/check-package-manager.mjs               # Enforce pnpm (CI critical)
node scripts/check-routes.mjs                        # Marketplace route verification
node scripts/check-performance.mjs                   # Website performance budget
```

## Workspace Structure

**pnpm Workspaces** (defined in `pnpm-workspace.yaml`):

```yaml
packages:
  - 'plugins/mcp/*'           # 7 MCP server plugins (independent packages)
  - 'marketplace'             # Astro website (uses npm internally)
  - 'packages/cli'            # CLI tool (published to npm)
  - 'packages/analytics-daemon'  # Analytics service
```

**Root Scripts** (package.json):
- `pnpm dev` → Runs all workspace dev servers in parallel
- `pnpm build` → Builds all workspace packages
- `pnpm test` → Runs all workspace tests
- `pnpm lint` → Lints all workspace packages
- `pnpm typecheck` → TypeScript validation across workspaces
- `pnpm run sync-marketplace` → **CRITICAL:** Syncs catalog files

**Package Manager Enforcement:**
- **Enforced:** pnpm@9.15.9 (via packageManager field in package.json)
- **CI Check:** `node scripts/check-package-manager.mjs` (fails if npm/yarn used)
- **Exception:** `marketplace/` directory uses npm (separate project)

## Shared Packages

**Location:** `packages/` (pnpm workspace)

### 1. CLI Tool (`packages/cli/`)
- **Package:** `@intentsolutionsio/ccpi`
- **Published to:** npm registry
- **Framework:** Commander 12.1.0
- **Commands:** `ccpi --version`, `ccpi --help`, `ccpi doctor --json`
- **Testing:** Cross-platform (Ubuntu, macOS, Windows) × 3 Node versions
- **Build:** TypeScript → `dist/index.js` (executable with shebang)

### 2. Plugin Validator (`packages/plugin-validator/`)
- **Purpose:** Shared validation logic
- **Used by:** Validation scripts, CI workflows
- **Features:** Schema validation, frontmatter parsing, security scanning

### 3. Analytics Daemon (`packages/analytics-daemon/`)
- **Purpose:** Analytics collection for marketplace
- **Type:** Background service
- **Integration:** Website + plugin installations

## Testing Infrastructure

**Three-tier testing strategy:**

### 1. Quick Test (`scripts/quick-test.sh`)
- **Duration:** ~30 seconds
- **Purpose:** Fast pre-commit validation
- **Checks:** JSON syntax, marketplace sync, basic structure

### 2. Clean Environment Test (`scripts/test-clean-environment.sh`)
- **Duration:** 2-5 minutes
- **Purpose:** Full validation in isolated environment
- **Isolation:** Uses `/tmp/` directory (no Docker)
- **Tests:** Install, build, test, lint, typecheck, validation, security
- **Output:** `test-results/*.log` files
- **Cross-platform:** Linux, macOS, Windows (WSL2)

### 3. Docker Test Suite (`scripts/test-docker-suite.sh`)
- **Duration:** 5-10 minutes (first build), 1-2 min (cached)
- **Purpose:** Completely isolated reproducible testing
- **Dockerfile:** `Dockerfile.test` (multi-stage)
- **Docker Compose:** `docker-compose.test.yml` (3 services)
- **Targets:**
  - `test-full`: Complete build + test + lint + typecheck + validation
  - `test-production`: Minimal production environment (300 MB)
  - `test-validation`: Plugin validation only
- **Usage:**
  ```bash
  bash scripts/test-docker-suite.sh              # Full suite
  bash scripts/test-docker-suite.sh --target production
  bash scripts/test-docker-suite.sh -v --cleanup
  docker-compose -f docker-compose.test.yml up test-full
  ```

**Test Results:** All tests write to `test-results/` directory (git-ignored)

## Critical Architecture: Two Catalog System

**Source of Truth:** `.claude-plugin/marketplace.extended.json`
- Edit this file when adding/updating plugins
- Contains extended metadata: `featured`, `mcpTools`, `pricing`, `components`
- Total size: 258 plugins with full metadata

**Generated File:** `.claude-plugin/marketplace.json`
- Auto-generated by `pnpm run sync-marketplace`
- **NEVER edit directly** - stripped for CLI compatibility
- CI fails if out of sync with extended version

**Why Two Catalogs:**
- Claude CLI enforces strict JSON schema (no extra fields allowed)
- Extended version tracks website-specific metadata (featured status, pricing tiers)
- Sync script (`scripts/sync-marketplace.cjs`) bridges the two systems
- Prevents schema validation failures in production CLI

**Sync Process:**
1. Edit `.claude-plugin/marketplace.extended.json`
2. Run `pnpm run sync-marketplace`
3. Commit BOTH files (extended + generated)
4. CI verifies they're in sync

## Plugin Types & Structure

### 1. AI Instruction Plugins (98% of marketplace)
- **What they are**: Markdown files with YAML frontmatter, no code execution
- **Location**: `plugins/[category]/[plugin-name]/`
- **Key files**:
  - `.claude-plugin/plugin.json` - Required manifest
  - `README.md` - Plugin documentation
  - `commands/[name].md` - Slash commands (optional)
  - `skills/[name]/SKILL.md` - Agent Skills (optional)
  - `agents/[name].md` - Specialized AI agents (optional)
  - `hooks/hooks.json` - Event hooks (optional)

### 2. MCP Server Plugins (2% of marketplace)
- **What they are**: TypeScript/Node.js applications using MCP SDK
- **Location**: `plugins/mcp/[plugin-name]/`
- **Structure**:
  ```
  plugins/mcp/[plugin-name]/
  ├── src/
  │   ├── index.ts              # MCP server entry (#!/usr/bin/env node)
  │   ├── storage.ts            # Data persistence layer
  │   └── types.ts              # TypeScript type definitions
  ├── dist/                      # Compiled output (chmod +x dist/index.js)
  ├── package.json              # Must include @modelcontextprotocol/sdk
  ├── tsconfig.json             # Target: ES2022, Module: Node16
  └── .claude-plugin/plugin.json
  ```

**MCP Implementation Pattern:**
- Use `@modelcontextprotocol/sdk` version ^1.0.4
- `StdioServerTransport` for IPC communication
- Define tools with Zod schemas for runtime validation
- Export as executable Node.js binary with shebang: `#!/usr/bin/env node`

**Build Requirements:**
- TypeScript compiles to `dist/` directory
- Entry point must be executable: `chmod +x dist/index.js`
- Set `"type": "module"` in package.json for ES modules

### 3. Agent Skills (239 across marketplace plugins)
- **What they are**: Auto-activating capabilities triggered by conversation context
- **Location**: `plugins/[category]/[plugin]/skills/[skill-name]/SKILL.md`
- **How they work**: Claude reads trigger phrases and activates automatically

## Adding a New Plugin

### Quick Start
```bash
# 1. Create structure
mkdir -p plugins/[category]/your-plugin/.claude-plugin
mkdir -p plugins/[category]/your-plugin/commands
mkdir -p plugins/[category]/your-plugin/skills/skill-adapter

# 2. Create required files:
#    - .claude-plugin/plugin.json (see templates/)
#    - README.md
#    - 000-docs/001-BL-LICN-license.txt (MIT or Apache-2.0 recommended)

# 3. Add to marketplace.extended.json
# Edit .claude-plugin/marketplace.extended.json and add entry

# 4. Sync and validate
pnpm run sync-marketplace
./scripts/validate-all-plugins.sh plugins/[category]/your-plugin/

# 5. Test locally
/plugin marketplace add /home/jeremy/000-projects/claude-code-plugins
/plugin install your-plugin@claude-code-plugins-plus
```

**Available Categories:**
- `productivity`, `security`, `devops`, `ai-ml`, `database`, `api-development`
- `crypto`, `finance`, `performance`, `business-tools`, `community`, `mcp`
- `examples`, `life-sciences`, `jeremy-genkit`, `jeremy-google-adk`, `jeremy-vertex-ai`
- Plus category-specific: `ai-agency`, `skill-enhancers`

## Agent Skills (2025 Schema)

**Location:** `plugins/[category]/[plugin]/skills/[skill-name]/SKILL.md`

**Required Frontmatter Format:**
```yaml
---
name: skill-name
description: |
  What this skill does. Include trigger phrases like "create ansible playbook"
  or "deploy infrastructure" that Claude should recognize.
allowed-tools: Read, Write, Edit, Grep, Bash
version: 1.0.0
license: MIT
author: Name <email>
---
```

**Allowed-Tools Patterns:**
- **Simple**: `Read, Write, Edit, Grep, Bash` - Full access to basic tools
- **Restricted**: `Bash(diff:*)`, `Bash(api:contract-*)` - Namespace-limited access
- **Read-Only**: `Read, Grep` - Analysis/audit skills with no modifications
- **Security Best Practice**: Prefer minimal tool access for single-purpose skills

**Validation Requirements:**
- Must have YAML frontmatter (starts and ends with `---`)
- `allowed-tools` and `version` are REQUIRED for 2025 compliance
- No `"opus"` model (deprecated) - use `"sonnet"` or `"haiku"`
- Description must include trigger phrases
- Validate with: `python3 scripts/validate-skills-schema.py`

**Skill Count:** 239 skills across 14 skill categories, all 2025-compliant

## Validation Pipeline (6 Stages)

**`./scripts/validate-all-plugins.sh` performs:**

1. **JSON Schema Validation**
   - Required fields: name, version, description, author
   - Valid semver versions
   - Proper plugin.json structure

2. **Markdown Frontmatter Validation**
   - YAML syntax correctness
   - Required frontmatter fields in commands/agents/skills
   - 2025 schema compliance for skills

3. **Duplicate Shortcut Detection**
   - Prevents command conflicts (e.g., `/commit` collision)
   - Warns on similar shortcuts across plugins

4. **File Reference Validation**
   - All paths in plugin.json must exist
   - Commands/agents/hooks referenced correctly
   - No broken file paths

5. **Script Executability**
   - All `.sh` files must have `chmod +x`
   - Shebang lines present
   - No permission errors

6. **Required Documentation**
   - README.md presence and minimum content
   - 000-docs/001-BL-LICN-license.txt file exists
   - Basic documentation standards

**Security Scans (Automatic):**
- Hardcoded secrets: AWS keys (AKIA*), private keys, passwords
- Dangerous commands: `rm -rf /`, `eval`, command injection patterns
- Whitelisted: placeholders (`***`), example values, test data
- **Blocks commits** with real secrets, warns on suspicious patterns

## CI/CD Workflows

**GitHub Actions** (10 workflows):

1. **validate-plugins.yml** - Triggered on PR/push
   - Marketplace catalog sync check (`node scripts/sync-marketplace.cjs`)
   - Full 6-stage validation suite
   - Security scans for secrets/dangerous commands
   - JSON validation for all .json files
   - Plugin structure verification
   - MCP plugin tests (tsc + vitest + typecheck + eslint)
   - Python validation scripts (pytest)
   - Package manager enforcement (pnpm only in workspaces)

2. **deploy-marketplace.yml** - Auto-deploys website
   - Triggers on push to `marketplace/` directory or workflow changes
   - Skills generation (`npm run skills:generate`)
   - Astro build (`npm run build`)
   - Smoke tests: index.html, line length < 5000 (iOS Safari bug)
   - Deploys to GitHub Pages (https://claudecodeplugins.io)
   - Environment: production

3. **cli-test.yml** - Cross-platform CLI testing
   - Matrix: 3 OS (Ubuntu, macOS, Windows) × 3 runtimes (Node 18/20/22)
   - Deno runtime testing (separate pipeline)
   - CLI commands: `--version`, `--help`, `doctor --json`
   - Artifact uploads: build outputs + logs

4. **cli-publish.yml** - Manual trigger
   - Publish `@intentsolutionsio/ccpi` to npm registry
   - Version validation
   - Distribution builds

5. **release.yml** - Manual dispatch
   - Version bumping (semver)
   - Changelog generation
   - Git tagging
   - GitHub release creation

6. **daily-skill-generator.yml** - Scheduled (daily)
   - Generates Agent Skills via Vertex AI Gemini
   - Batch processing workflow
   - Part of 500 Standalone Skills Initiative

7. **automerge.yml** - Automated PRs
   - Merge Dependabot/contributor PRs
   - Auto-approval workflow

8. **maintainer-ready-automerge.yml** - PRs with label
   - Fast-track maintainer-approved PRs
   - Label-based automation

9. **security-audit.yml** - Scheduled
   - CodeQL scanning
   - npm audit for dependencies
   - Security vulnerability detection

10. **codeql.yml** - PR/push
    - Code quality analysis
    - Security scanning
    - Best practices enforcement

**Critical Pre-Commit Checks:**
```bash
# ALWAYS run before committing:
pnpm run sync-marketplace           # Sync catalogs (CI fails if skipped)
./scripts/validate-all-plugins.sh   # Run full validation
git add .claude-plugin/marketplace.json  # Commit generated file too
```

## Marketplace Website (Astro)

**Tech Stack:**
- Framework: Astro 5.16.6 (static site generator)
- Styling: Tailwind CSS 4.1.18
- Search: Fuse.js 7.1.0 (fuzzy search)
- Deploy: GitHub Pages (auto on push)
- Build command: `npm run build` → `./marketplace/dist/`

**Build Constraints:**
- **HTML Compression:** DISABLED (`compressHTML: false` in astro.config.mjs)
- **Reason:** iOS Safari crashes on lines > 5000 chars
- **Smoke Test:** Verifies line length < 5000 in deployment pipeline
- **Skills Generation:** Runs automatically during build (`npm run skills:generate`)

**Development Workflow:**
```bash
cd marketplace/
npm run dev          # Dev server at localhost:4321
npm run catalog:build  # Regenerate catalog from marketplace.extended.json
npm run build        # Production build
npm run preview      # Test production build locally
```

**Data Source:**
- Reads from `.claude-plugin/marketplace.extended.json`
- Uses extended metadata: `featured`, `pricing`, `mcpTools`, `components`
- Homepage: `src/pages/index.astro`
- Plugin pages: Auto-generated from catalog

**Build Pipeline:**
1. `npm run catalog:build` - Generates catalog JSON for website
2. Astro builds static pages from catalog
3. Search index generated from plugin metadata
4. Deploy to GitHub Pages

## Key Conventions

### File Paths
- **Hooks**: Use `${CLAUDE_PLUGIN_ROOT}` for portability, never hardcode paths
- **Scripts**: All `.sh` files MUST be executable (`chmod +x`)
- **Workspace**: pnpm workspace paths are relative to monorepo root

### Versioning
- **Semver**: All plugins use semantic versioning (1.0.0, 1.1.0, etc.)
- **Sync versions**: Update VERSION file, package.json, marketplace.extended.json together
- **Model IDs**: Use `sonnet` or `haiku` (not `opus` - deprecated in 2025)

### Security
- **No secrets**: Never commit API keys, tokens, or credentials
- **Environment variables**: Use `.env` files (in .gitignore)
- **Validation**: All MCP tools use Zod schemas for runtime validation
- **Permissions**: Skills declare minimal `allowed-tools` required

### Code Quality
- **TypeScript**: Strict mode enabled for all MCP plugins
- **ESLint**: Run `pnpm lint` before commit
- **Testing**: MCP plugins should have test coverage
- **Documentation**: README.md required for all plugins

## Marketplace Identifiers

**Critical Information:**
- **Marketplace Slug**: `claude-code-plugins-plus`
- **GitHub Repo**: `jeremylongshore/claude-code-plugins`
- **Install Command**: `/plugin marketplace add jeremylongshore/claude-code-plugins`
- **Website**: https://claudecodeplugins.io/
- **Owner**: Jeremy Longshore <jeremy@intentsolutions.io>

**Legacy Slug**: `claude-code-plugins` (deprecated, redirects to `-plus`)

## 500 Standalone Skills Initiative

**Location:** `planned-skills/`

**Goal**: Generate 500 standalone Agent Skills separate from plugins
- Current: 239 skills embedded in plugins
- Target: 739 total skills (500 standalone + 239 embedded)

**Structure:**
```
planned-skills/
├── categories/           # 20 categories × 25 skills each
│   └── [id]-[name]/
│       ├── category-config.json
│       └── skills/
├── batches/             # Batch processing groups
├── generated/           # Vertex AI generated skills
├── templates/           # Skill templates
└── scripts/             # Generation/validation scripts
```

**Generation Workflow:**
1. Categories defined in `categories/[id]-[name]/category-config.json`
2. Templates in `templates/` (skill template, category README, Gemini prompt)
3. Batch processing via Vertex AI Gemini 2.0
4. Validation: `scripts/validate-skill.js`
5. Deployment to `/skills/` directory

**Phase Status:**
- Phase 1 (Plan): ✅ Complete - Infrastructure created
- Phase 2 (Generate): Pending - Vertex AI integration
- Phase 3 (Validate): Pending - Quality assurance
- Phase 4 (Deploy): Pending - Production deployment

**Reference Documentation:**
- `planned-skills/SKILLS-STANDARD-COMPLETE.md` - Complete specification
- `planned-skills/SKILLS-REFERENCE-MANUAL.md` - Developer guide
- `planned-skills/STATUS-2025-12-19.md` - Latest status update

## Documentation Filing System

**Location:** `000-docs/` (git-ignored except 6767 standards)

**Naming Convention:**
```
NNN-CC-ABCD-short-description.ext

NNN  = Zero-padded sequence number (001-999)
CC   = Two-letter category code (PP, AT, DR, RA, etc.)
ABCD = Four-letter document type (PROD, GUID, REPT, etc.)
short-description = 1-4 words, kebab-case
```

**Examples:**
- `048-RA-INDX-audit-index.md` - Audit index report
- `061-DR-REFF-vertex-ai-gemini-tiers.md` - Reference documentation
- `086-PP-PLAN-release-v1-2-0.md` - Release plan

**Category Codes:**
- `AA` - Architecture
- `AT` - Automation
- `DR` - Documentation Reference
- `MS` - Master Systems
- `OD` - Operations/DevOps
- `PP` - Project Planning
- `RA` - Research & Audit
- `RL` - Resources & Learning
- `SR` - Status Reports

**Important**: Only `6767*.md` files (canonical standards) are committed to git. All other documentation is private/internal.

## Templates

**Location:** `templates/`

**Available Templates:**
1. **minimal-plugin** - Just plugin.json & README (simple utilities)
2. **command-plugin** - Slash commands (custom workflows)
3. **agent-plugin** - Specialized AI agent (domain expertise)
4. **full-plugin** - Commands + agents + hooks (complex automation)

**Usage:**
```bash
cp -r templates/command-plugin plugins/[category]/my-plugin
cd plugins/[category]/my-plugin
# Edit .claude-plugin/plugin.json
# Edit README.md
# Add to marketplace.extended.json
pnpm run sync-marketplace
./scripts/validate-all-plugins.sh plugins/[category]/my-plugin/
```

## Common Development Tasks

### Add a Plugin to Marketplace
1. Copy appropriate template from `templates/`
2. Edit `.claude-plugin/plugin.json` with plugin details
3. Create README.md with examples and documentation
4. Add 000-docs/001-BL-LICN-license.txt file (MIT recommended)
5. Add entry to `.claude-plugin/marketplace.extended.json`
6. Run `pnpm run sync-marketplace`
7. Validate: `./scripts/validate-all-plugins.sh plugins/[category]/[name]/`
8. Test locally: `/plugin install [name]@claude-code-plugins-plus`

### Update Plugin Version
1. Bump version in `.claude-plugin/plugin.json`
2. Update `VERSION` file if present
3. Update version in `.claude-plugin/marketplace.extended.json`
4. Run `pnpm run sync-marketplace`
5. Update 000-docs/247-OD-CHNG-changelog.md with changes
6. Commit all version changes together

### Add Agent Skill to Plugin
1. Create `plugins/[category]/[plugin]/skills/[skill-name]/SKILL.md`
2. Add required 2025 frontmatter (name, description, allowed-tools, version)
3. Write skill instructions with trigger phrases
4. Update plugin.json to reference skill
5. Validate: `python3 scripts/validate-skills-schema.py`
6. Update marketplace.extended.json with skill count
7. Run `pnpm run sync-marketplace`

### Build MCP Plugin
```bash
cd plugins/mcp/[plugin-name]/
pnpm install                # Install dependencies
pnpm build                  # Compile TypeScript
chmod +x dist/index.js      # Make executable
pnpm test                   # Run tests (if available)
```

### Debug Validation Failures
```bash
# Run specific validation stage
python3 scripts/validate-skills-schema.py           # Skills only
python3 scripts/validate-frontmatter.py             # Frontmatter only
node scripts/validate-plugin.js [path-to-plugin]    # Single plugin

# Check JSON syntax
jq empty .claude-plugin/marketplace.extended.json

# Verify sync status
pnpm run sync-marketplace
git diff .claude-plugin/marketplace.json  # Should be clean
```

### Local Testing Workflow
```bash
# Add local marketplace
/plugin marketplace add /home/jeremy/000-projects/claude-code-plugins

# Install specific plugin
/plugin install [plugin-name]@claude-code-plugins-plus

# Test plugin functionality
# (Use plugin commands/skills)

# Uninstall when done
/plugin uninstall [plugin-name]@claude-code-plugins-plus
```

### Skill Generation & Analysis
```bash
# Analyze skill names for consistency
python3 scripts/analyze-skill-names.py
python3 scripts/analyze-skill-names-gemini.py      # Uses Vertex AI Gemini

# Audit skills quality across all plugins
python3 scripts/audit-skills-quality.py

# Run comprehensive plugin audits
./scripts/audit-run-full.sh                        # Full audit suite
./scripts/audit-plugin-manifests.sh                # Check plugin.json files
./scripts/audit-plugin-commands.sh                 # Audit slash commands
./scripts/audit-plugin-agents.sh                   # Audit agent definitions
./scripts/audit-plugin-directories.sh              # Check directory structure
```

## Statistics (Current)

- **Total Plugins**: 258 across 22 categories
- **Agent Skills**: 239 (embedded in marketplace plugins)
- **MCP Plugins**: 7 (2% of marketplace)
- **AI Instruction Plugins**: 251 (97% of marketplace)
- **Plugin Packs**: 4 major packs (devops, security, api-development, ai-ml)
- **Categories**: 22 total categories
- **2025 Schema**: Validated with scripts/validate-skills-schema.py
- **Website**: https://claudecodeplugins.io/ (Astro 5.16.6 + Tailwind 4.1.18)
- **Monorepo Version**: 4.4.0 (package.json)
- **Release Version**: 4.4.0 (README.md - includes Learning Lab)
- **CLI Tool**: @intentsolutionsio/ccpi (published to npm)
- **Last Updated**: 2025-12-29

## Important Notes

### NOT on GitHub Marketplace
Claude Code plugins do NOT use GitHub Marketplace. They operate in a separate ecosystem using JSON-based marketplace catalogs hosted in Git repositories. This repository IS a Claude Code plugin marketplace.

### No Built-in Monetization
There is currently no monetization mechanism for Claude Code plugins. All plugins are free and open-source. External revenue strategies exist but are not built into the plugin system.

### Beta Status
Claude Code plugins are in **public beta** (October 2025). Features and best practices evolve. This marketplace stays updated with latest changes from Anthropic.

### Agent Skills Launch
Agent Skills feature launched October 16, 2025 by Anthropic. This marketplace was first to implement comprehensive skill support with 239 skills across plugins.
