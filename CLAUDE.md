# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Tons of Skills — Claude Code plugins marketplace. Live at https://tonsofskills.com

**Runtime:** Node `>=20.0.0`, pnpm `>=9.15.9`. Node 18 causes silent workspace-resolution failures.

**Package manager:** `pnpm` everywhere **except** `marketplace/` which uses `npm` (CI-enforced).

**Session protocol lives in `AGENTS.md`** — post-compaction recovery, end-of-session push checklist, and beads workflow. Read it before starting work.

## Essential Commands

```bash
# Before ANY commit — regenerates marketplace.json, plugin package.jsons, README TOC
pnpm run sync-marketplace

# Quick sanity check (~30s)
./scripts/quick-test.sh

# Build & test
pnpm install && pnpm build
pnpm test && pnpm typecheck
pnpm lint
pnpm run verify                   # Full pipeline — what CI's `verify` job runs

# Validator (schema 3.6.0 — see 000-docs/SCHEMA_CHANGELOG.md)
python3 scripts/validate-skills-schema.py --verbose
python3 scripts/validate-skills-schema.py --marketplace --verbose
python3 scripts/validate-skills-schema.py --marketplace --populate-db freshie/inventory.sqlite

# Marketplace website
cd marketplace/ && npm run dev    # localhost:4321
cd marketplace/ && npm run build
cd marketplace/ && npx playwright test

# Single test
cd packages/cli && pnpm test -- --grep "pattern"

# JRig behavioral eval (opt-in, ~$2-5/skill)
j-rig check <skill-dir>           # Tier 3A: deterministic (~seconds, free)
j-rig eval <skill-dir> --models haiku,sonnet,opus --db freshie/inventory.sqlite
```

## Two Catalog System — Critical

| File | Purpose | Edit? |
|---|---|---|
| `.claude-plugin/marketplace.extended.json` | Source of truth | **Yes** |
| `.claude-plugin/marketplace.json` | CLI-compatible, auto-generated | **Never** |

`pnpm run sync-marketplace` regenerates all three derived artifacts: `marketplace.json`, any missing `plugins/**/package.json` files, and the `README.md` AUTO-TOC block. The pre-commit hook runs this automatically when `marketplace.extended.json` is staged.

CI fails if any derived file is out of sync. Never hand-edit auto-generated files.

## Marketplace Build Pipeline

`npm run build` in `marketplace/` runs 7 sequential steps via `scripts/build.mjs`: discover-skills → extract-readme-sections → sync-catalog → enrich-jrig-data → generate-unified-search → build-cowork-zips → astro build.

`discover-skills.mjs` emits two artifacts (schema 3.4.0+): `skills-index.json` (L0, ~97 KB gzipped, metadata only — for trigger-match / browse) and `skills-catalog.json` (L1, ~5.5 MB gzipped, full body HTML). Both carry top-level `schemaVersion` + `level` fields. CLI flag `--level=metadata|full|file` (default `full`).

**Gotcha:** `compressHTML` is disabled in `astro.config.mjs` — iOS Safari fails on lines > 5000 chars. CI enforces this.

Performance budgets (CI-enforced): 40 MB total gzipped, 1 MB largest file, < 30s build, 2,800–4,000 routes.

## Plugin Structure

**AI instruction plugins** (`plugins/[category]/[name]/`): `.claude-plugin/plugin.json` + `README.md` + optional `commands/*.md`, `agents/*.md`, `skills/[name]/SKILL.md`.

**MCP server plugins** (`plugins/mcp/[name]/`): TypeScript source in `src/`, built to `dist/index.js` (must be executable: shebang + `chmod +x`).

**Forge-generated plugins** include a `.forge/` audit trail dir (`research.md`, `ecosystem.md`, `proofs.md`) — build-time only, not used at runtime. Canonical example: `plugins/productivity/plane/`.

### SKILL.md Required Frontmatter (marketplace tier — all 8 fields)

```yaml
---
name: skill-name
description: |
  Capability summary. Use when ... Trigger with "...".
allowed-tools: Read, Write, Edit, Bash(npm:*), Glob
version: 1.0.0
author: Name <email>
license: MIT
compatibility: Designed for Claude Code
tags: [devops, ci]
---
```

`compatible-with` is deprecated. Migrate with: `python3 scripts/batch-remediate.py --migrate-compatible-with`

**Agents use `disallowedTools` (denylist); skills use `allowed-tools` (allowlist).** Agent-only fields: `effort`, `maxTurns`.

### Optional frontmatter (schema 3.5.0 + 3.6.0 — all default to off)

- **Visibility gating (3.5.0):** `requires_env` / `requires_tools` / `fallback_for_env` / `fallback_for_tools` — list-of-strings. Skill hidden unless deps met; fallback form is the inverse. Cross-field overlap (`requires_X` + `fallback_for_X` of same value) is an ERROR.
- **Self-declared config (3.6.0):** `required_environment_variables` (top-level list, each entry needs `name` + `prompt`) and `metadata.intent-solutions.config` (nested list, each entry needs `key` + `description` + `default`). Full reference: `000-docs/264-DR-GUID-skill-config-pattern.md`.
- **NON-NEGOTIABLE:** these are optional. `ALWAYS_REQUIRED` is still the 8-field set above. See issue #612 before proposing any change to required fields.

## Adding a New Plugin

**Hand-authored:** copy from `templates/`, add catalog entry to `marketplace.extended.json`, run `pnpm run sync-marketplace`, validate with `--marketplace`.

**Forge-generated:** `/skill-creator --forge <api-name>` — runs 8-gate workflow, requires a NOI (Name of Identity), produces Grade-A skill + `.forge/` audit trail + catalog entry.

To regenerate against a current API: `/skill-creator --reforge <plugin-name>`.

## Design System

Constitution: `marketplace/DESIGN.md` (Data-Dense Pro family, locked 2026-05-06). If a component disagrees with it, the component is wrong.

Key tokens (`marketplace/src/styles/tokens.css`): `--bg`, `--panel`, `--rule`, `--ink`, `--signal`. Old aliases (`--primary`, `--surface`, `--text`, `--border`) remain mapped for back-compat. CSS colors: **OKLCH only, never hex/rgb**.

Reject: gradients on cards, glassmorphism, drop-shadow stacks, `hover:scale-105` on whole cards.

## Killer Skill of the Week

Editorial — Jeremy picks manually. Tooling only syncs two render surfaces.

```bash
# Promote a new spotlight
node scripts/promote-spotlight.mjs path/to/new-spotlight.json

# Sync README block only (no rotation)
node scripts/render-spotlight.mjs
```

Source of truth: `marketplace/src/data/spotlights.json`.

## Key Identifiers — Do Not "Normalize"

- **GitHub repo (canonical):** `jeremylongshore/claude-code-plugins-plus-skills`
- **Marketplace catalog id:** `claude-code-plugins-plus`
- **Public install slug:** `jeremylongshore/claude-code-plugins` (legacy, GitHub 301s to canonical — hardcoded in CLI, Hero snippet, hundreds of READMEs — renaming is a breaking API change)

## Freshie Inventory

CMDB at `freshie/inventory.sqlite`. Key commands:

```bash
python3 freshie/scripts/rebuild-inventory.py                         # New discovery run
python3 scripts/validate-skills-schema.py --enterprise --populate-db freshie/inventory.sqlite
sqlite3 freshie/inventory.sqlite "SELECT grade, COUNT(*) FROM skill_compliance GROUP BY grade;"
python3 freshie/scripts/batch-remediate.py --dry-run && python3 freshie/scripts/batch-remediate.py --all --execute
```

Key tables: `skill_compliance` (scores, grades, JRig columns), `forge_proofs` (drives JRig-Verified badges on plugin detail pages).

## npm Publish Pipeline

Patch version bumps happen automatically on PR (via `auto-bump-on-pr.yml`). For minor/major bumps, hand-edit the version in the same PR. Merge to main triggers publish + tag + GitHub Release via `publish-changed-packages.yml`. See `RELEASING.md` for the full operator flow.

## Legacy Root Files

Not part of the active build: `docker-compose.test.yml`, `Dockerfile.test`, `firebase.json` + `firestore.rules` (tonsofskills.com migrated to Contabo VPS 2026-05-06 via `deploy-vps.yml`; `deploy-firebase.yml` is renamed `.disabled`), `config.zcf.json`, scratch scripts.
