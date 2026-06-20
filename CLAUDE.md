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

# Validator (schema 3.11.0 — see 000-docs/SCHEMA_CHANGELOG.md)
python3 scripts/validate-skills-schema.py --verbose
python3 scripts/validate-skills-schema.py --marketplace --verbose
python3 scripts/validate-skills-schema.py --marketplace --populate-db freshie/inventory.sqlite
python3 scripts/validate-skills-schema.py --agents-only --verbose   # agents only (kernel-strict gate)

# Unicode hygiene gate — Trapdoor / Trojan Source defense for SKILL.md /
# plugin.json / agent / command files. Default mode blocks on tag chars
# (U+E0000-E007F) + bidi overrides (CVE-2021-42574). --strict also blocks
# on zero-width / format chars outside the BOM position.
python3 scripts/validate-unicode-hygiene.py
python3 scripts/validate-unicode-hygiene.py --strict           # tighter
python3 scripts/validate-unicode-hygiene.py path/to/file.md    # one file
python3 -m unittest tests.test_validate_unicode_hygiene -v     # regression suite

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

| File                                       | Purpose                        | Edit?     |
| ------------------------------------------ | ------------------------------ | --------- |
| `.claude-plugin/marketplace.extended.json` | Source of truth                | **Yes**   |
| `.claude-plugin/marketplace.json`          | CLI-compatible, auto-generated | **Never** |

`pnpm run sync-marketplace` regenerates all three derived artifacts: `marketplace.json`, any missing `plugins/**/package.json` files, and the `README.md` AUTO-TOC block. The pre-commit hook runs this automatically when `marketplace.extended.json` is staged.

CI fails if any derived file is out of sync. Never hand-edit auto-generated files.

## Marketplace Build Pipeline

`npm run build` in `marketplace/` runs 7 sequential steps via `scripts/build.mjs`: discover-skills → extract-readme-sections → sync-catalog → enrich-jrig-data → generate-unified-search → build-cowork-zips → astro build.

`discover-skills.mjs` emits two artifacts (schema 3.4.0+): `skills-index.json` (L0, ~97 KB gzipped, metadata only — for trigger-match / browse) and `skills-catalog.json` (L1, ~5.5 MB gzipped, full body HTML). Both carry top-level `schemaVersion` + `level` fields. CLI flag `--level=metadata|full|file` (default `full`).

**Gotcha:** `compressHTML` is disabled in `astro.config.mjs` — iOS Safari fails on lines > 5000 chars. CI enforces this.

Performance budgets (CI-enforced): 40 MB total gzipped, 1 MB largest file, < 30s build, 2,800–4,000 routes.

## Auto-cowork contract

**Author flow.** Add a plugin to `.claude-plugin/marketplace.extended.json` and run `pnpm run sync-marketplace`. That is the entire authoring step. The pre-commit hook regenerates `marketplace.json`, plugin `package.json`s, and the README AUTO-TOC. There is no separate "update the cowork page" step.

**Pipeline (deterministic from the catalog).** `cd marketplace && npm run build` runs `scripts/build.mjs`, which on every invocation:

1. `cowork:zips` (`scripts/build-cowork-zips.mjs`) — wipes `marketplace/public/downloads/{plugins,bundles}` and rebuilds them from `marketplace.extended.json`. Produces individual plugin zips, category bundle zips, the mega-zip, `downloads/manifest.json`, and the Astro-consumed `marketplace/src/data/cowork-manifest.json`. Skips `category: mcp` entries (MCP plugins do not appear in cowork).
2. `cowork:validate` (`scripts/validate-cowork-manifest.mjs`) — drift gate. Fails the build if catalog ↔ manifest ↔ disk fall out of alignment (orphan zips, missing entries, or stale manifest rows). Runs again in CI as a discrete step in `.github/workflows/validate-plugins.yml` so the failure signal is clearly named.
3. `astro build` — copies `marketplace/public/` → `marketplace/dist/`. The `/cowork/` page reads `cowork-manifest.json` at build time and renders the download grid.

**Deploy propagates the wipe.** The VPS force-command script `/usr/local/sbin/deploy-tonsofskills` ends with `rsync -a --delete /srv/tonsofskills/build/marketplace/dist/ /srv/tonsofskills/dist/`, so orphan files removed by the cowork build are also pruned from the served `dist/`. Documented in `intentsolutions-vps-runbook/docs/onboard-new-repo-deploy.md` § "Atomic deploy convention".

**Don't commit downloads/.** `marketplace/public/downloads/` is gitignored (see `.gitignore:146`). CI checks out fresh and rebuilds from scratch — local state cannot leak to prod. Never commit or hand-edit anything under that directory.

**Don't wire cowork build into `sync-marketplace`.** `sync-marketplace` is the fast (<2s) per-commit hook; `cowork:zips` is the slow (~30s) per-build step. They run on different cadences by design.

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

Beyond the 8 required fields, schema 3.5.0+ adds optional visibility-gating fields, 3.6.0+ adds self-declared config fields, and 3.7.0+ adds `disallowed-tools` — see the Optional frontmatter section below.

`compatible-with` is deprecated. Migrate with: `python3 scripts/batch-remediate.py --migrate-compatible-with`

**Agents use `disallowedTools` (camelCase denylist).** Skills use `allowed-tools` (allowlist) AND optionally `disallowed-tools` (kebab-case denylist, schema 3.7.0+). The two field names are intentionally different — do NOT use camelCase on skills or kebab-case on agents; the validator rejects either mismatch. Agent-only fields: `effort`, `maxTurns`.

**Agent gate is kernel-strict (schema 3.10.0, NOT tier-gated).** Every authored agent must carry the kernel-floor 8 (`name, description, tools, model, color, version, author, tags`) plus the enterprise live set (`disallowedTools`, `skills`, `background`; + `hooks`, `mcpServers`, `permissionMode` on standalone agents) — all **errors** at every tier. Banned fields (`capabilities`, `expertise_level`, `activation_priority`, `type`, `category`, `compatible-with`, `when_to_use`) are errors; `fable` is an accepted model. All 317 in-repo agents are at **A-grade** (least-privilege `tools`, Trigger-bearing descriptions, real tags). **Schema 3.11.0** added a body-vs-allowlist check: an agent whose body invokes `mcp__server__tool` not in its `tools` allowlist is an error (it would runtime-block). Validate with `--agents-only`.

### Optional frontmatter (schema 3.5.0 / 3.6.0 / 3.7.0 — all default to off)

- **Visibility gating (3.5.0):** `requires_env` / `requires_tools` / `fallback_for_env` / `fallback_for_tools` — list-of-strings. Skill hidden unless deps met; fallback form is the inverse. Cross-field overlap (`requires_X` + `fallback_for_X` of same value) is an ERROR.
- **Self-declared config (3.6.0):** `required_environment_variables` (top-level list, each entry needs `name` + `prompt`) and `metadata.intent-solutions.config` (nested list, each entry needs `key` + `description` + `default`). Full reference: `000-docs/264-DR-GUID-skill-config-pattern.md`.
- **Defense-in-depth disallow list (3.7.0):** `disallowed-tools` — kebab-case string or YAML list of tool patterns. Removes those tools from the model while the skill is active. Parallel to (not a replacement for) `allowed-tools`. Cross-field overlap with `allowed-tools` is an ERROR (mirrors the 3.5.0 visibility-gating overlap rule). Defense-in-depth for skills that legitimately need broad `allowed-tools` but should never reach for specific high-risk operations (`rm`, `curl`, `wget`, `.env` writes). Full reference: `000-docs/681-AT-ADEC-claude-code-platform-changelog-impact.md` § Change 1.
- **NON-NEGOTIABLE:** these are optional. `ALWAYS_REQUIRED` is still the 8-field set above. See issue #612 + `000-docs/681-AT-ADEC-claude-code-platform-changelog-impact.md` § Implementation directives before proposing any change to required fields — the 8-field set is preserved; `disallowed-tools` is additive, not required.

## Validation & the kernel SSoT — CI/CD posture

Two things grade frontmatter in this repo today, and the relationship between them is the load-bearing context to preserve.

### The two validators

- **Prose-spec validator (authoritative):** `scripts/validate-skills-schema.py`. This is the canonical gate. It runs at standard and marketplace tiers, it grades both frontmatter AND markdown body sections, and at marketplace tier a missing required field is an **ERROR** (not a warning). It is the one in the branch-protection required-status set. `ALWAYS_REQUIRED` (the IS 8-field set) is hand-authored here and stays **AUTHORITATIVE** — read `000-docs/SCHEMA_CHANGELOG.md` § NON-NEGOTIABLES before touching it. The IS rubric sits on top of Anthropic's permissive spec; the marketplace tier is intentionally strict. Do not reduce the 8-field set, do not demote marketplace errors to warnings, and do not "realign" to Anthropic's floor — any change to required-fields / tier model / error-vs-warning semantics is approval-gated per that doc.

- **Kernel machine-spec (the SSoT being migrated to):** `@intentsolutions/core` — its `schemas/authoring/v1` family (byte-frozen) plus the strict fork `authoring/v2` — is the single internal source of truth for "what is a valid agent-native artifact." The kernel's `skill-frontmatter` schema encodes the **same** IS 8-field required set as a pure `allOf` of upstream-base + universal folds + the IS overlay. The plan of record is for `validate-skills-schema.py` to **consume the kernel folds** instead of its hand-rolled rule sets. That migration is in progress; the kernel pin is **exactly `0.4.1`** in `package.json` (no `^`/`~`). Contract semantics for `authoring/v1` fields are canonical in the kernel's own changelog — cite it, do not duplicate it (see `000-docs/SCHEMA_CHANGELOG.md` § "Kernel changelog citation").

### Two advisory lanes (never block) running the soak

Both are `continue-on-error: true`, neither is in the required-status set, and neither mutates anything:

- **kernel-shadow soak** — `.github/workflows/kernel-shadow-validation.yml` + `scripts/kernel-shadow-validation.mjs`. Runs the kernel-pinned `skill-frontmatter` schema (from `@intentsolutions/core@0.4.1`) over the same SKILL.md corpus the prose-spec validator grades and logs per-file AGREE / DISAGREE deviation to `scripts/.kernel-shadow/report.json`. This is the DR-049 shadow soak (the "zero-on-corpus shadow signal"). The cutover-relevant number is the **frontmatter-scoped** deviation — a file that fails the prose-spec on missing `[body]` sections but has valid frontmatter is a scope difference, not a kernel gap, and is excluded.
- **kernel-vendor-hash gate** — `.github/workflows/kernel-vendor-hash.yml` + `scripts/kernel-vendor-hash.mjs`. Enforces the version-coupling invariant **V ≤ C ≤ K** (vendored ≤ CCPI-declared ≤ kernel-latest) plus a ≤7-day staleness bound. Soak-aware: it reads the `0.4.1` pin, polices ordering/staleness only, and must never pressure a pin bump or change validator authority.

The validator itself does a kernel-loaded **shadow read** of `ALWAYS_REQUIRED` (`load_kernel_required()` / `--kernel-shadow`) — it compares the kernel's effective required set against the hand-authored one and reports drift. The hand-authored `ALWAYS_REQUIRED` stays authoritative; the shadow read is observational only.

### Do-not-flip soak discipline (do not lose this)

**Keep the kernel pin at exactly `0.4.1` during the soak — do NOT bump it.** Do **NOT** flip the kernel-shadow lane from advisory to authoritative (blocking) until ALL of these hold:

1. ≥99.5% corpus agreement (deterministic folds must be 100%; the 0.5% band is reserved for non-deterministic surfaces only);
2. ≥30 days of advisory soak;
3. zero open P0 blockers;
4. the Rekor superseding-event rollback protocol implemented and tested;
5. governance sign-off from the CTO + CISO + VP-DevRel triple; and
6. a ≥14-day public deprecation-window notice to affected skill authors.

As of now the soak has **not** met the bar — agreement sits below 99.5%, and the open disagreements are real tool-safety / shell-substitution security cases that the prose-spec validator correctly blocks (so flipping early would weaken a real gate). Until every condition above is satisfied, validator authority stays with `validate-skills-schema.py` and both kernel lanes stay advisory. Promotion to blocking is a separate, later cutover step gated by these conditions — never a side effect of an unrelated PR.

### Validator consolidation (already landed)

A recent cleanup removed 74 dead duplicate `validation.sh` stubs, collapsed previously-diverged secondary validators into delegating wrappers around the canonical `validate-skills-schema.py`, and added the kernel-loaded shadow read described above. There is now one canonical validator; secondary entry points delegate to it.

### auto-bump posture for contributors

`.github/workflows/auto-bump-on-pr.yml` auto-bumps changed plugins' patch versions on PRs (only on `plugins/**` / `packages/**` changes). For a docs-only or otherwise non-release PR, put **`[skip auto-bump]`** in the PR title or body so the auto-bumper steps aside. Minor/major bumps stay a deliberate human choice — hand-edit the version in the same PR.

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
