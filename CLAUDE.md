# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Claude Code plugins marketplace (270+ plugins, 1500+ skills). Live at https://claudecodeplugins.io/

**Monorepo structure:** pnpm workspaces (v9.15.9+)
- `plugins/[category]/*` - AI instruction plugins (Markdown, ~98% of plugins)
- `plugins/mcp/*` - MCP server plugins (TypeScript, ~2%)
- `plugins/saas-packs/*-pack` - SaaS skill packs (pnpm workspace members)
- `marketplace/` - Astro 5 website (**uses npm, not pnpm** - CI enforced)
- `packages/cli` - `ccpi` CLI (`@intentsolutionsio/ccpi` on npm)
- `packages/analytics-*` - Analytics daemon and dashboard

**Package manager policy (CI-enforced by `scripts/check-package-manager.mjs`):**
- `pnpm` everywhere at root
- `npm` for `marketplace/` only (it's excluded from pnpm workspace)

## Essential Commands

```bash
# Before ANY commit (MANDATORY)
pnpm run sync-marketplace           # Regenerate marketplace.json from .extended.json
./scripts/validate-all-plugins.sh   # Full plugin validation (JSON, frontmatter, refs, permissions)
./scripts/quick-test.sh             # Fast validation: build + lint + validate (~30s)

# Build & test
pnpm install && pnpm build          # Install and build all workspace packages
pnpm test && pnpm typecheck         # Run vitest tests and TypeScript checks
pnpm lint                           # ESLint across all packages

# Single MCP plugin
cd plugins/mcp/[name]/ && pnpm build && chmod +x dist/index.js

# Skills validation with 100-point grading
python3 scripts/validate-skills-schema.py --verbose      # All content (skills + commands + agents)
python3 scripts/validate-skills-schema.py --skills-only   # SKILL.md files only
python3 scripts/validate-skills-schema.py --commands-only  # commands/*.md only

# CLI package
cd packages/cli && pnpm test -- --grep "pattern"  # Run single test
cd packages/cli && pnpm build && node dist/index.js validate --strict  # ccpi validate

# Marketplace website
cd marketplace/ && npm run dev                    # Dev server at localhost:4321
cd marketplace/ && npm run build                  # Full build pipeline (see below)
cd marketplace/ && npm run validate               # Route + link validation
cd marketplace/ && npx playwright test            # E2E tests (chromium + webkit)
```

## Two Catalog System (Critical)

| File | Purpose | Edit? |
|------|---------|-------|
| `.claude-plugin/marketplace.extended.json` | Source of truth with extended metadata | Yes |
| `.claude-plugin/marketplace.json` | CLI-compatible (auto-generated) | Never |

`sync-marketplace` strips extended-only fields: `featured`, `mcpTools`, `pluginCount`, `pricing`, `components`, `zcf_metadata`, `external_sync`.

Run `pnpm run sync-marketplace` after editing `.extended.json`. CI fails if out of sync.

## Data Flow

```
marketplace.extended.json (source of truth, edit this)
        ↓ pnpm run sync-marketplace
marketplace.json (auto-generated, never edit)
        ↓ CI deploys to GitHub Pages
claudecodeplugins.io/catalog.json
        ↓
ccpi CLI fetches and caches locally
```

## Marketplace Build Pipeline

`npm run build` in `marketplace/` runs 5 steps sequentially via `scripts/build.mjs`:

1. `discover-skills.mjs` - Scans all plugins, extracts SKILL.md data into `src/data/`
2. `sync-catalog.mjs` - Copies catalog JSON into marketplace data
3. `generate-unified-search.mjs` - Builds Fuse.js search index
4. `build-cowork-zips.mjs` - Generates plugin zips, category bundles, mega-zip, and manifest for `/cowork` downloads
5. `astro build` - Static site generation

**Gotcha:** `compressHTML` is disabled in `astro.config.mjs` because iOS Safari fails to render lines > 5000 chars. CI enforces this with a smoke test.

Post-build validation scripts (also run in CI):
- `validate-routes.mjs` - Plugin page routes exist
- `validate-playbook-routes.mjs` - Production playbook routes
- `validate-internal-links.mjs` - No broken internal links in dist (seeds: index, playbooks, explore, skills, cowork)
- `validate-links.mjs` - Skill-to-plugin link integrity
- `validate-cowork-downloads.mjs` - Cowork zip build output (manifest, checksums, download links)
- `validate-cowork-security.mjs` - Zip content security scanner (no secrets, no node_modules)

## Plugin Structure

### AI Instruction Plugins
```
plugins/[category]/[plugin-name]/
├── .claude-plugin/plugin.json    # Required fields: name, version, description, author
├── README.md                     # Required
├── commands/*.md                 # Slash commands (YAML frontmatter)
├── agents/*.md                   # Custom agents (YAML frontmatter)
└── skills/[skill-name]/SKILL.md  # Auto-activating skills
```

### MCP Server Plugins
```
plugins/mcp/[plugin-name]/
├── .claude-plugin/plugin.json
├── src/*.ts                      # TypeScript source
├── dist/index.js                 # Must be executable (shebang + chmod +x)
├── package.json
└── .mcp.json
```

`plugin.json` only allows these fields: `name`, `version`, `description`, `author`, `repository`, `homepage`, `license`, `keywords`. CI rejects any others.

### SKILL.md Frontmatter (2026 Spec)
```yaml
---
name: skill-name
description: |
  When to use this skill. Include trigger phrases.
allowed-tools: Read, Write, Edit, Bash(npm:*), Glob
version: 1.0.0
author: Name <email>
---
```

Valid tools: `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `Task`, `TodoWrite`, `NotebookEdit`, `AskUserQuestion`, `Skill`

## Adding a New Plugin

1. Copy from `templates/` (minimal, command, agent, or full)
2. Create `.claude-plugin/plugin.json` with required fields
3. Add entry to `.claude-plugin/marketplace.extended.json`
4. `pnpm run sync-marketplace`
5. `./scripts/validate-all-plugins.sh plugins/[category]/[name]/`

## CI Pipeline (validate-plugins.yml)

PRs trigger 5 parallel jobs:

| Job | What it checks |
|-----|---------------|
| `validate` | JSON validity, plugin structure, catalog sync, secret scanning, dangerous patterns |
| `test` (matrix) | MCP plugin builds + vitest, Python pytest, `ccpi validate --strict` + frontmatter |
| `check-package-manager` | Enforces pnpm/npm policy per directory |
| `marketplace-validation` | Astro build, route validation, link validation, smoke tests, cowork downloads/security validation, performance budget |
| `playwright-tests` | E2E tests on chromium + webkit + mobile (T1-T9, needs marketplace-validation) |
| `cli-smoke-tests` | CLI build, `--help`, `--version`, `npm pack`, no `workspace:` deps |

## Conventions

- **Hooks:** Use `${CLAUDE_PLUGIN_ROOT}` for portability
- **Scripts:** All `.sh` files must be `chmod +x`
- **Model IDs in skills:** Use `sonnet`, `haiku`, or `opus`
- **README Contributors:** Newest contributors go at the TOP of the list
- **External plugin sync:** `sources.yaml` defines repos synced daily via `scripts/sync-external.mjs`

## Key Identifiers

- **Slug:** `claude-code-plugins-plus`
- **Install:** `/plugin marketplace add jeremylongshore/claude-code-plugins`

## Task Tracking (Beads)

See `AGENTS.md` for full protocol. Quick reference:

```bash
bd sync && bd ready                        # Session start: find work
bd update <id> --status in_progress        # Claim task BEFORE starting
bd close <id> --reason "..."               # Complete with evidence
bd sync && git push                        # Session end: MANDATORY
```
