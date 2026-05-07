# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Tons of Skills — Claude Code plugins marketplace (425 plugins, 2,851 skills, 177 agents). Live at https://tonsofskills.com

**Runtime:** Node `>=20.0.0`, pnpm `>=9.0.0` (pinned to `9.15.9` via `packageManager` field). Developers on Node 18 will hit silent workspace-resolution failures.

**Monorepo structure:** pnpm workspaces (see `pnpm-workspace.yaml` — only 6 directories are actual workspace members)

- `plugins/[category]/*` - AI instruction plugins (Markdown, ~98% of plugins). `plugins/` has 23 top-level entries; most are categories but a few are special: `mcp/`, `saas-packs/`, `packages/`, `examples/`, `jeremy-google-adk/`, `jeremy-vertex-ai/`. Only `mcp/*` and `saas-packs/*-pack` are pnpm workspace members — category dirs are flat collections of plugins.
- `plugins/mcp/*` - MCP server plugins (TypeScript, ~2%)
- `plugins/saas-packs/*-pack` - SaaS skill packs (pnpm workspace members)
- `marketplace/` - Astro 5 website (**uses npm, not pnpm** - CI enforced)
- `packages/cli` - `ccpi` CLI (`@intentsolutionsio/ccpi` on npm)
- `packages/analytics-*` - Analytics daemon and dashboard

> **Session protocol lives in `AGENTS.md`, not here.** Post-compaction recovery (`bd ready`), the mandatory end-of-session push checklist ("Landing the Plane"), and the beads workflow are all in `AGENTS.md`. Read it before starting work — those rules are load-bearing and intentionally not duplicated below.

**Package manager policy (CI-enforced by `scripts/check-package-manager.mjs`):**

- `pnpm` everywhere at root
- `npm` for `marketplace/` only (listed in `pnpm-workspace.yaml` for structural reasons, but uses npm for its own dependencies)

## Essential Commands

```bash
# Before ANY commit (MANDATORY)
pnpm run sync-marketplace           # Regenerate ALL catalog-derived files (marketplace.json + plugin package.jsons + README TOC)
pnpm run sync-marketplace:json-only # Just the marketplace.json strip (legacy single-step behavior, rarely needed)
./scripts/quick-test.sh             # Fast validation: build + lint + validate (~30s)

# Build & test
pnpm install && pnpm build          # Install and build all workspace packages
pnpm test && pnpm typecheck         # Run vitest tests and TypeScript checks
pnpm lint                           # ESLint across all packages
pnpm run verify                     # Full verification pipeline (scripts/run-verification-pipeline.mjs) — what CI's `verify` job runs
pnpm run update-metrics             # Refresh plugin/skill/agent counts in README + marketplace data

# Single MCP plugin
cd plugins/mcp/[name]/ && pnpm build && chmod +x dist/index.js

# Universal validator v7.0 / schema 3.0.0 (single source of truth — see 000-docs/SCHEMA_CHANGELOG.md)
python3 scripts/validate-skills-schema.py --verbose                  # Standard tier (Anthropic spec exactly: name + description required)
python3 scripts/validate-skills-schema.py --marketplace --verbose    # Marketplace tier (Anthropic spec + IS polish recommendations + 100-point rubric)
python3 scripts/validate-skills-schema.py --marketplace --populate-db freshie/inventory.sqlite  # Write to DB
python3 scripts/validate-skills-schema.py --marketplace --show-low-grades  # Show D/F skills
python3 scripts/validate-skills-schema.py --skills-only              # SKILL.md files only
python3 scripts/validate-skills-schema.py --commands-only            # commands/*.md only
python3 scripts/validate-skills-schema.py --agents-only              # agents/*.md only
# Migration tool: legacy compatible-with → spec-aligned compatibility (per agentskills.io/specification)
python3 scripts/batch-remediate.py --migrate-compatible-with --root .  # Add --dry-run to preview

# Ecosystem inventory (freshie)
python3 freshie/scripts/rebuild-inventory.py              # Full repo scan → new discovery run
python3 freshie/scripts/rebuild-inventory.py --dry-run    # Preview without writing
python3 freshie/scripts/batch-remediate.py --dry-run      # Preview compliance fixes
python3 freshie/scripts/batch-remediate.py --all --execute  # Apply all auto-fixes

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

| File                                       | Purpose                                | Edit? |
| ------------------------------------------ | -------------------------------------- | ----- |
| `.claude-plugin/marketplace.extended.json` | Source of truth with extended metadata | Yes   |
| `.claude-plugin/marketplace.json`          | CLI-compatible (auto-generated)        | Never |

`pnpm run sync-marketplace` is an orchestrator — running it after any catalog edit regenerates **all three** catalog-derived artifacts in one step:

1. **`.claude-plugin/marketplace.json`** — strips extended-only fields (`featured`, `mcpTools`, `pluginCount`, `pricing`, `components`, `zcf_metadata`, `external_sync`)
2. **`plugins/**/package.json`\*\* — generates npm-tracking artifacts for any plugin missing one (idempotent; only writes new files, never modifies existing)
3. **`README.md` AUTO-TOC sentinel block** — regenerates the browse-by-category nav

CI fails on any of these being out of sync (`validate-catalog-invariants.py`, `generate-readme-toc.mjs --check`, `prettier --check README.md`). The pre-commit hook (`.husky/pre-commit`) auto-runs the chain whenever `marketplace.extended.json` is staged, so most PRs never see the drift.

For the rare case where you only want the JSON-strip step (e.g., debugging the strip logic in isolation), use `pnpm run sync-marketplace:json-only`.

## Auto-Generated Data Files (Never Hand-Edit)

| File                                                                                       | Generated by                                                                                                              |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `.claude-plugin/marketplace.json`                                                          | `pnpm run sync-marketplace` (orchestrator; runs the next two as well)                                                     |
| `plugins/**/package.json`                                                                  | `node scripts/generate-plugin-package-jsons.mjs` (chained from `sync-marketplace`; idempotent — only writes new files)    |
| `README.md` TOC block (between `AUTO-TOC:START`/`AUTO-TOC:END` sentinels)                  | `node scripts/generate-readme-toc.mjs` (chained from `sync-marketplace`; CI-enforced via `--check`)                       |
| `marketplace/src/data/catalog.json`                                                        | `sync-catalog.mjs` (build step 2)                                                                                         |
| `marketplace/src/data/skills-catalog.json`                                                 | `discover-skills.mjs` (build step 1)                                                                                      |
| `marketplace/src/data/unified-search-index.json`                                           | `generate-unified-search.mjs` (build step 3)                                                                              |
| `marketplace/src/data/cowork-manifest.json`                                                | `build-cowork-zips.mjs` (build step 4)                                                                                    |
| `README.md` Killer-Skill block (between `KILLER-SKILL:START`/`KILLER-SKILL:END` sentinels) | `node scripts/render-spotlight.mjs` (CI-enforced via `--check`); source of truth = `marketplace/src/data/spotlights.json` |
| `marketplace/src/data/npm-stats.json` + `README.md` NPM-STATS block                        | `node scripts/fetch-npm-stats.mjs` (daily cron via `update-npm-stats.yml`)                                                |
| Per-plugin `plugins/**/package.json` (for npm tracking)                                    | `node scripts/generate-plugin-package-jsons.mjs` (idempotent; touches only plugins without one)                           |

## Killer Skill of the Week — Editorial Workflow

Single source of truth: **`marketplace/src/data/spotlights.json`** (drives both `KillerSkills.astro` on the homepage and the `KILLER-SKILL` block in README).

**Picking is editorial — not automated.** You decide who/when. The tooling just removes the rotation tedium.

### Promote a new spotlight

1. Write a JSON file (or pipe via stdin) with the new spotlight content. Required fields: `pluginSlug`, `headline`, `author`, `authorGithub`, `grade`, `category`, `link`. Optional: `whyKiller`, `quote`, `skillCount`.
2. Run the promote script:

   ```bash
   node scripts/promote-spotlight.mjs path/to/new-spotlight.json
   # or
   node scripts/promote-spotlight.mjs --stdin < new-spotlight.json
   ```

3. The script atomically rotates: previous `spotlight` → top of `hallOfFame` (tagged with the previous week's ISO label), new content → `spotlight`, `week` → today's ISO week, `meta.lastUpdated` → today, `meta.version` minor-bumped. Then it regenerates the README block via `render-spotlight.mjs`.
4. Commit + PR + merge. CI (`Verify README Killer-Skill block is in sync`) blocks any drift.

### Render-only (no rotation)

Use when you hand-edit `spotlights.json` and just want the README block synced:

```bash
node scripts/render-spotlight.mjs           # write README
node scripts/render-spotlight.mjs --check   # CI: exit 1 if README is out of sync
```

### Why not Changesets / weekly cron / auto-pick

Marketing surface — taste-driven, not metric-driven. The "auto-pick by stars / by latest A-grade / by GitHub star delta" patterns lose editorial control. Tooling here only removes drift between the two render surfaces and the manual JSON-array surgery; humans still curate.

## npm Publish Pipeline

Full operator-facing flow lives in [`RELEASING.md`](./RELEASING.md). Quick reference:

| Workflow                                         | Trigger                                               | What it does                                                                                                                                                                                 |
| ------------------------------------------------ | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.github/workflows/auto-bump-on-pr.yml`          | `pull_request` touching `plugins/**` or `packages/**` | For every plugin whose source changed, bumps `package.json` patch (X.Y.Z → X.Y.Z+1) and commits back to the PR branch. Skipped on `automation/*` branches and PRs marked `[skip auto-bump]`. |
| `.github/workflows/publish-changed-packages.yml` | Push to main touching `plugins/**`                    | For each changed plugin where the declared version isn't yet on npm: `npm publish --provenance` + annotated git tag `@scope/name@version` + GitHub Release with auto-generated notes.        |
| `.github/workflows/cli-publish.yml`              | Tag push `cli-v*.*.*`                                 | Publishes `@intentsolutionsio/ccpi` only (parallel system; not auto-bumped).                                                                                                                 |
| `.github/workflows/publish-all-packages.yml`     | Manual dispatch with `confirm="publish all"`          | One-shot mass publish of every `@intentsolutionsio/*` package; idempotent. Use only for the freeze-fix sweep or recovery.                                                                    |
| `.github/workflows/update-npm-stats.yml`         | Daily cron (00:15 UTC)                                | Refreshes `marketplace/src/data/npm-stats.json` + README NPM-STATS block. Pushes to `automation/npm-stats` and opens a PR (main is branch-protected).                                        |
| `.github/workflows/slack-daily-downloads.yml`    | Daily cron (18:00 UTC = 1pm Central)                  | Posts totals + top-5 to #operation-hired (pings `<@U099CBRE7CL>`) via `SLACK_OPERATION_HIRED_WEBHOOK_URL` secret — per `/slack` skill conventions.                                           |

**Versioning is now automated by default.** A code-touching PR auto-bumps the affected plugins' patch versions; merge to main publishes + tags + releases. **For minor or major bumps, hand-edit the version in the same PR** (auto-bumper steps aside when the PR's only plugin-dir change is to its own `package.json`).

**Tag convention:** per-package tags use `@scope/name@version` (e.g. `@intentsolutionsio/langchain-pack@1.1.0`). Repo-wide `vX.Y.Z` tags from before this pipeline (e.g. `v4.28.0`) are left in place but not extended.

**Freeze fix utility:** `scripts/bulk-bump-versions.mjs` is a one-time minor sweep (1.0.0 → 1.1.0 across every package whose declared version matches npm-latest). Used to break the historical 1.0.0 freeze; re-runs are no-ops once everything's bumped.

After editing the catalog (`marketplace.extended.json`), run both syncs:

```bash
pnpm run sync-marketplace
node scripts/generate-readme-toc.mjs
```

## Data Flow

```
marketplace.extended.json (source of truth, edit this)
        ↓ pnpm run sync-marketplace
marketplace.json (auto-generated, never edit)
        ↓ CI deploys to GitHub Pages
tonsofskills.com/catalog.json
        ↓
ccpi CLI fetches and caches locally
```

## Marketplace Build Pipeline

`npm run build` in `marketplace/` runs 6 steps sequentially via `scripts/build.mjs`:

1. `discover-skills.mjs` - Scans all plugins, extracts SKILL.md data into `src/data/`
2. `extract-readme-sections.mjs` - Extracts README sections for plugin pages
3. `sync-catalog.mjs` - Copies catalog JSON into marketplace data
4. `generate-unified-search.mjs` - Builds Fuse.js search index
5. `build-cowork-zips.mjs` - Generates plugin zips, category bundles, mega-zip, and manifest for `/cowork` downloads
6. `astro build` - Static site generation

**Gotcha:** `compressHTML` is disabled in `astro.config.mjs` because iOS Safari fails to render lines > 5000 chars. CI enforces this with a smoke test.

Post-build validation scripts (also run in CI):

- `validate-routes.mjs` - Plugin page routes exist
- `validate-playbook-routes.mjs` - Production playbook routes
- `validate-internal-links.mjs` - No broken internal links in dist (seeds: index, playbooks, explore, skills, cowork, docs)
- `validate-links.mjs` - Skill-to-plugin link integrity
- `validate-cowork-downloads.mjs` - Cowork zip build output (manifest, checksums, download links)
- `validate-cowork-security.mjs` - Zip content security scanner (no secrets, no node_modules)

## Documentation Section (/docs)

Public, SEO-optimized documentation at tonsofskills.com/docs. Uses Astro content collections (not GitHub wiki — wikis are blocked by Google's robots.txt).

**Structure:** 5 sections, 24 pages + hub:

- `getting-started/` (4 pages) — installation, first-plugin, first-skill, cli-reference
- `concepts/` (5 pages) — plugins, skills, agents, commands-and-hooks, mcp-servers
- `guides/` (6 pages) — write-a-skill, build-a-plugin, create-an-agent, saas-skill-packs, mcp-server-plugin, publish-to-marketplace
- `reference/` (5 pages) — skill-frontmatter, plugin-json-schema, plugin-categories, allowed-tools, cli-commands
- `ecosystem/` (4 pages) — marketplace-overview, official-anthropic-docs, community-resources, faq

**Key files:**

- `marketplace/src/content/docs/{section}/{slug}.md` — Content (Astro content collection)
- `marketplace/src/content/config.ts` — `docsCollection` schema
- `marketplace/src/pages/docs/[...slug].astro` — Dynamic route
- `marketplace/src/pages/docs/index.astro` — Hub page
- `marketplace/src/components/DocsTemplate.astro` — Template (sidebar, breadcrumbs, JSON-LD TechArticle, prev/next, related docs, official Anthropic links)
- `marketplace/src/components/DocsSidebar.astro` — Section nav (build-time, no JS)

**Frontmatter schema:** title, description, section (enum), order, keywords, officialLinks (array of {title, url}), relatedDocs (array of slugs like `concepts/skills`).

## Performance Budgets

Enforced by `scripts/check-performance.mjs` in CI:

| Budget                 | Limit       |
| ---------------------- | ----------- |
| Total bundle (gzipped) | 40 MB       |
| Largest file (gzipped) | 1 MB        |
| Build time             | < 30s       |
| Route count            | 2,800–4,000 |

Largest pages: `explore/index.html` (~860KB), `skills/index.html` (~300KB), `compare/index.html` (~250KB). The `/downloads` directory is excluded from the budget. Budgets bumped 2026-03-22 after 63 SaaS pack merge (3,283 routes).

## Marketplace Design System

**Constitution: [`marketplace/DESIGN.md`](marketplace/DESIGN.md)** — single source of truth for visual treatment. Family: Data-Dense Pro (locked 2026-05-06). Read it before any UI work; if a component disagrees with it, the component is wrong.

**Tokens** (`marketplace/src/styles/tokens.css`): values are Data-Dense Pro (`#0a0a0c` canvas / `#181818` panel / `#f4f4f5` ink / `#faff69` signal / `#ff3d6e` alert / `#2a2a2e` rule). Token *names* preserved across the rebrand (`--primary`, `--neutral-900`, `--card-featured-radius`, etc.) so existing components keep compiling. Fluid type via `clamp()` (`--text-xs` through `--text-4xl`). 4pt spacing grid (`--space-1` through `--space-12`). Three card tiers (compact/standard/featured). Motion presets with `prefers-reduced-motion`. Newly explicit breakpoints: `--breakpoint-tablet: 1024px` (was missing).

**Theme system** (`BaseLayout.astro`): Dark default; light via `[data-theme="light"]` on `<html>`. FOUC prevented by inline script before first paint. Legacy `--surface*` / `--brand-*` / `--gold` / `--navy` / `--text*` aliases all map to the new family tokens (`--bg`, `--panel`, `--ink`, `--signal`).

**Font stack**: Inter Tight (display h1/h2), Inter (body, with `font-feature-settings: 'tnum' 1` for tabular numerals), JetBrains Mono (labels/stats/code). All via Google Fonts.

**Key tokens for UI work**: `--bg`, `--panel`, `--rule`, `--ink`, `--ink-2`, `--signal`, `--signal-tint`, `--signal-edge`, `--ink-link`. Old aliases (`--primary`, `--surface`, `--text`, `--border`) remain mapped for back-compat.

**3-viewport screenshot convention**: `marketplace/DESIGN_AUDIT_2026-05-06_before/{desktop,tablet,mobile}/` and `..._after/{desktop,tablet,mobile}/` — every visually significant change captures both states across 1440 / 1024 / 375 px. Validator (Playwright + ui-visual-validator agent) brackets each PR.

**Anti-Slop discipline**: see DESIGN.md § 8 Reject Table. Reject gradients on cards, glassmorphism, drop-shadow stacks, multi-accent palettes, and `hover:scale-105` lift on whole cards. The site reads against Linear / Vercel / Bloomberg, not against Tailwind starters.

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

### SKILL.md Frontmatter (IS Enterprise Standard, Schema v3.3.1)

**Required at marketplace tier — all 8 fields must be present:**

```yaml
---
name: skill-name
description: |
  Capability summary. Use when ... Trigger with "...".
allowed-tools: Read, Write, Edit, Bash(npm:*), Glob
version: 1.0.0
author: Name <email>
license: MIT
compatibility: Designed for Claude Code # free-text per agentskills.io/specification (max 500 chars)
tags: [devops, ci]
---
```

**Other optional fields (Anthropic spec — full reference at `code.claude.com/docs/en/skills#frontmatter-reference`):**

```yaml
# Trigger / discovery
# when_to_use: "Trigger phrases or example requests. Appended to description."  # Combined cap 1,536 chars
# argument-hint: "<file-path>"                # Autocomplete hint
# arguments: issue branch                     # Named positional args ($issue, $branch in body)
# paths: src/**/*.py, tests/**/*.py           # Glob patterns limiting auto-activation

# Invocation control (see "Control who invokes a skill")
# user-invocable: false                       # Hide from / menu (Claude can still invoke)
# disable-model-invocation: true              # Manual /name only — Claude cannot auto-invoke

# Execution
# model: sonnet                               # LLM model override (or inherit / haiku / opus)
# effort: medium                              # low / medium / high / xhigh / max
# context: fork                               # Run in isolated subagent
# agent: Explore                              # Subagent type (with context: fork)
# shell: bash                                 # bash (default) or powershell
# hooks: { PreToolUse: [...] }                # Skill-scoped lifecycle hooks
# metadata: { custom: ... }                   # Free-form key-value (per agentskills.io)
```

**`compatibility` examples** (free-text per `agentskills.io/specification`, max 500 chars):

```yaml
compatibility: "Designed for Claude Code"
compatibility: "Designed for Claude Code, also compatible with Codex and OpenClaw"
compatibility: "Requires Python 3.10+ with uv installed"
compatibility: "Requires git, docker, and jq on PATH"
compatibility: "Node.js >= 18, npm >= 9"
```

**Deprecated:** `compatible-with` (CSV platform list — was an Intent Solutions invention, never in any spec).
Migration: `python3 scripts/batch-remediate.py --migrate-compatible-with`.

**Source citations** (every claim above defensible against published sources):

- `name` + `description` required: `platform.claude.com/docs/en/agents-and-tools/agent-skills/overview`, `...best-practices`, `anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills`, `agentskills.io/specification`, `github.com/anthropics/skills`
- `compatibility` (free-text, optional, max 500 chars): `agentskills.io/specification`
- `metadata` (optional object): `agentskills.io/specification`
- `allowed-tools` optional (not required): `code.claude.com/docs/en/skills`

Valid tools: `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `Task`, `TodoWrite`, `NotebookEdit`, `AskUserQuestion`, `Skill`

Supporting file references (per Anthropic docs):

- Relative markdown links: `[API Reference](reference.md)`, `[Examples](examples/sample.md)` — Claude follows these with Read tool on demand
- In DCI/bash commands: `${CLAUDE_SKILL_DIR}` resolves to the skill's directory at runtime

Path variables:

- `${CLAUDE_SKILL_DIR}` for bash/DCI contexts within skills (not needed for markdown links)
- `${CLAUDE_PLUGIN_ROOT}` for plugin root directory references in hooks
- `${CLAUDE_PLUGIN_DATA}` for persistent plugin state (survives updates/reinstalls, v2.1.78+)

String substitutions (replaced before Claude processes the skill):

- `$ARGUMENTS` / `$0`, `$1`, ..., `$9` — user-provided arguments (pair with `argument-hint` frontmatter)
- `${CLAUDE_SESSION_ID}` — current session identifier

Dynamic context injection (DCI) — runs shell commands at skill activation time:

- Syntax: `` !`command` `` on its own line — output injected verbatim into skill body
- Use for pre-loading discovery data (git status, versions, env detection) to save tool call rounds
- Always add fallbacks: `` !`terraform version 2>/dev/null || echo 'not installed'` ``
- Keep injections small — summaries, not full file contents

### Agent Frontmatter (agents/\*.md)

```yaml
---
name: agent-name
description: "20-200 char description of the agent's specialty"
capabilities: ['capability1', 'capability2']
# Optional fields:
# model: sonnet                         # LLM model override
# effort: low|medium|high               # Model reasoning effort (v2.1.78+)
# maxTurns: 10                          # Max agentic loop iterations (v2.1.78+)
# disallowedTools: ["mcp__servername"]  # Tools to deny (v2.1.78+, denylist — opposite of skills' allowed-tools)
# expertise_level: intermediate|advanced|expert
# activation_priority: low|medium|high|critical
# permissionMode: default               # Permission behavior
---
```

**Key difference from skills:** Agents use `disallowedTools` (denylist) while skills use `allowed-tools` (allowlist). The `effort` and `maxTurns` fields are agent-only — they control autonomous iteration behavior that doesn't apply to skills or commands.

## Adding a New Plugin

1. Copy from `templates/` (minimal, command, agent, skill, or full)
2. Create `.claude-plugin/plugin.json` with required fields
3. Add entry to `.claude-plugin/marketplace.extended.json`
4. `pnpm run sync-marketplace`
5. `python3 scripts/validate-skills-schema.py --enterprise plugins/[category]/[name]/`

## CI Pipeline (validate-plugins.yml)

PRs trigger parallel jobs:

| Job                      | What it checks                                                                                                              |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| `validate`               | JSON validity, plugin structure, catalog sync, secret scanning, dangerous patterns                                          |
| `verify`                 | Verification pipeline + badge generation                                                                                    |
| `test` (matrix)          | MCP plugin builds + vitest, Python pytest, universal validator v7.0 (smoke + marketplace report) + `ccpi validate --strict` |
| `check-package-manager`  | Enforces pnpm/npm policy per directory                                                                                      |
| `marketplace-validation` | Astro build, route validation, link validation, smoke tests, cowork downloads/security, performance budget                  |
| `playwright-tests`       | E2E tests on chromium + webkit + mobile (needs marketplace-validation)                                                      |
| `cli-smoke-tests`        | CLI build, `--help`, `--version`, `npm pack`, no `workspace:` deps                                                          |
| `production-e2e`         | Runs against live site — can be flaky due to GitHub avatar CDN rate limits                                                  |

## Test Organization

**Dev tests** (`marketplace/tests/T*.spec.ts`): T1–T4, T6–T9 covering homepage search, search results, mobile viewport, install CTA, playbooks nav, explore flows, cowork page/integration.

**Production tests** (`marketplace/tests/production/P*.spec.ts`): P1–P8 covering core page smoke tests, search flow, redirects, navigation, cowork downloads, mobile responsive, performance budgets, SEO meta.

**Config** (`playwright.config.ts`): Chromium + WebKit, mobile viewports (iPhone 13 + Pixel 5). CI: 2 retries, 1 worker. Local: no retries, parallel.

## External Plugin Sync

`sources.yaml` defines external repos synced daily via `scripts/sync-external.mjs` (midnight UTC cron). Each source specifies include/exclude globs. Sync writes `.source.json` provenance files and creates PRs (labels: `automated`, `sync`, `external-plugins`). Supports `--dry-run`, `--force`, `--source=NAME`.

## Conventions

- **Hooks:** Use `${CLAUDE_PLUGIN_ROOT}` for portability
- **Scripts:** All `.sh` files must be `chmod +x`
- **Model IDs in skills:** Use `sonnet`, `haiku`, or `opus`
- **README Contributors:** Newest contributors go at the TOP of the list
- **CSS colors:** Use OKLCH values, never hex/rgb. Use tokens from `tokens.css` when possible.

## Git Hooks (`.husky/`)

| Hook         | What it does                                                                                                                                                                                                                                                                                                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `commit-msg` | Runs `commitlint` on the message — enforces conventional commit format (`feat:`, `fix:`, `chore:`, etc.)                                                                                                                                                                                                                                                                              |
| `pre-commit` | Two stages: (1) if `marketplace.extended.json` is staged, runs `pnpm run sync-marketplace` and auto-stages any regenerated derived files (`marketplace.json`, `README.md`, new `plugins/**/package.json`); (2) standard `lint-staged` + `audit-harness verify`. Catches the catalog-drift failure pattern that previously bit PRs across multiple CI rounds.                          |
| `pre-push`   | Warns (does NOT block) when the local branch is behind `origin/main`. Suggests `git pull --rebase origin main && git push --force-with-lease`. Skipped when pushing main itself or when running in CI. Catches the failure pattern where a long-running PR branch falls behind, leading to "patch contents already upstream" surprises during rebase or merge conflicts at push time. |

The hooks live in `.husky/` and are wired by `pnpm install` (husky's `prepare` script). To bypass intentionally, use `git commit --no-verify` or `git push --no-verify` — but doing so means CI catches what the hook would have, just slower.

## Key Identifiers

- **Brand:** Tons of Skills by Intent Solutions
- **Domain:** tonsofskills.com
- **GitHub repo:** `jeremylongshore/claude-code-plugins-plus-skills` (canonical)
- **Marketplace catalog id:** `claude-code-plugins-plus` (the suffix in `plugin@claude-code-plugins-plus` install commands — this is the `name` field in `marketplace.json`)
- **Public install command:** `/plugin marketplace add jeremylongshore/claude-code-plugins` (uses the legacy repo slug, which GitHub 301-redirects to the current repo — kept stable for users' bookmarked commands and CLI cache keys)

These three names are intentionally distinct. Do not "normalize" them without understanding the blast radius: the legacy `claude-code-plugins` slug is hardcoded in `packages/cli/src/utils/constants.ts`, the marketplace Hero install snippet, blog posts, and hundreds of plugin READMEs. A rename is a breaking change to a public API.

## Freshie — Ecosystem Inventory & Compliance

CMDB for the plugin ecosystem at `freshie/`. Versioned discovery runs — old data stays, new data appends.

```
freshie/
├── inventory.sqlite          # Active DB (50 tables, versioned by run_id)
├── scripts/
│   ├── rebuild-inventory.py  # Full repo scan → new discovery run
│   └── batch-remediate.py    # Auto-fix tags, compatible-with, agent fields
├── archives/                 # Read-only baseline snapshots
├── exports/run-N/            # CSV exports per run
└── reports/                  # Data dictionary, baseline reports
```

### Common Queries

```bash
# New inventory scan
python3 freshie/scripts/rebuild-inventory.py

# Compliance validation → DB
python3 scripts/validate-skills-schema.py --enterprise --populate-db freshie/inventory.sqlite

# Grade summary
sqlite3 freshie/inventory.sqlite "SELECT grade, COUNT(*) FROM skill_compliance GROUP BY grade;"

# Stub skills
sqlite3 freshie/inventory.sqlite "SELECT skill_path, score FROM skill_compliance WHERE is_stub=1;"

# Compare runs
sqlite3 freshie/inventory.sqlite "SELECT * FROM discovery_runs;"

# Batch remediation (dry run first, then --execute)
python3 freshie/scripts/batch-remediate.py --dry-run
python3 freshie/scripts/batch-remediate.py --all --execute
```

### Key Tables

| Table                        | Purpose                                           |
| ---------------------------- | ------------------------------------------------- |
| `skill_compliance`           | 100-point rubric scores, grades, stub flags       |
| `agent_compliance`           | Anthropic field analysis, invalid field detection |
| `plugin_compliance`          | Roll-up scores, license/changelog checks          |
| `content_signals`            | Word count, code blocks, placeholder density      |
| `plugins`, `skills`, `packs` | Core entity inventory (versioned by run_id)       |
| `discovery_runs`             | Run history with timestamps and commit hashes     |

## Task Tracking (Beads)

See `AGENTS.md` for full protocol — including the mandatory post-compaction `bd ready` recovery step and "Landing the Plane" end-of-session push checklist. Quick reference:

```bash
bd sync && bd ready                        # Session start: find work
bd update <id> --status in_progress        # Claim task BEFORE starting
bd close <id> --reason "..."               # Complete with evidence
bd sync && git push                        # Session end: MANDATORY
```

## Legacy / Ancillary Files at Root

These exist at repo root but are not part of the active build/deploy path. Do not assume they are live without checking git log:

- `docker-compose.test.yml` + `Dockerfile.test` — test-harness containers (not referenced by any current CI workflow)
- `firebase.json` + `firestore.rules` — Firebase config (marketplace deploys to GitHub Pages via `deploy-marketplace.yml`, not Firebase; these may be legacy)
- `config.zcf.json` — ZCF tool config
- `test_youtube_strategy.py`, `asset_generation*.log`, `setup.sh`, `create-tasks.sh`, `package.json.tmp` — scratch/legacy. If you're tempted to extend them, check whether they should move to `archive/` first.
