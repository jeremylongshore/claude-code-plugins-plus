# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Tons of Skills — Claude Code plugins marketplace. Live at https://tonsofskills.com

**Runtime:** Node `>=20.0.0`, pnpm `>=9.15.9`. Node 18 causes silent workspace-resolution failures.

**Package manager:** `pnpm` everywhere **except** `marketplace/` which uses `npm` (CI-enforced).

**Session protocol lives in `AGENTS.md`** — post-compaction recovery, end-of-session push checklist, and beads workflow. Read it before starting work.

## Cross-session coordination — another Claude session may be in this repo

This repo is frequently worked in **parallel** with the `intent-eval-platform` umbrella session (that platform's CCPI validator + jrig-cli + kernel reach into this repo). Sessions are separate processes that share only the filesystem, so stay in sync via the shared surfaces:

- **Read + append the shared journal** on cross-repo work: `~/000-projects/CROSS-SESSION-LOG.md` (append a dated line: what / branch or PR# / status).
- **Durable cross-cutting tasks:** umbrella beads `~/000-projects/.beads/`, label `cross-session` (`bd list --label cross-session`).
- **Guard the working tree:** this repo has ONE checkout; a concurrent session can `git checkout`/`reset` it out from under you and **wipe UNCOMMITTED work** (happened 2026-07-01). Commit early, or do multi-step file work in a `git worktree`.

Full protocol (loaded by every session under `/home/jeremy`): `/home/jeremy/CLAUDE.md` § "Cross-session coordination".

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

# Validator (schema 3.15.0 — see 000-docs/SCHEMA_CHANGELOG.md)
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

# JRig behavioral eval — the published @intentsolutions/jrig-cli (bin `j-rig`),
# pinned as a root devDep. Invoke via `pnpm exec j-rig` so it resolves the
# repo's pinned version (node_modules/.bin/j-rig), NOT a global shim.
pnpm exec j-rig --version         # → 0.1.2 (the real 7-layer CLI)
pnpm exec j-rig check <skill-dir> # Tier 3A: deterministic (~seconds, free, no API key, no DB)

# Real behavioral eval (opt-in, ~$2-5/skill) — needs a provider API key + the
# native better-sqlite3 build (run `pnpm rebuild better-sqlite3` once; the build
# script is not auto-run on install).
DEEPSEEK_API_KEY=...  pnpm exec j-rig eval <skill-dir> \
  --provider deepseek --models deepseek-v4-flash --db freshie/inventory.sqlite
# DEEPSEEK_API_KEY is provisioned via SOPS (intent-eval-lab/.env.sops; see the
# IEP umbrella CLAUDE.md credential table). `deepseek-v4-flash` is a real
# behavioral provider — this is ground truth, replacing the prior dev/stub
# resolution where the global `j-rig` symlink pointed at a local unbuilt CLI.
# Other providers (haiku/sonnet/opus via Anthropic, etc.) remain available.
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

## External Plugin Sync (mirror-by-default)

Adopted model: **mirror by default · upstream improvements · never clobber.** Decision record: `000-docs/694-AT-DECR-external-sync-mirror-by-default-model.md`; pipeline audit + hardening: `000-docs/691-AT-AUDT-sync-external-pipeline-audit-and-hardening.md`.

**Scale first — external is a minority augment, not the core.** 454 plugins total, but only ~51 are externally synced (48 third-party sources + 6 of Jeremy's own repos). The other ~403 (89%) are in-repo Intent Solutions work. The sync is a curated side-channel, not the marketplace — treat external contributors as a respected minority augment, never the center of gravity.

**How sync works.** `sources.yaml` registers each external source. `.github/workflows/sync-external.yml` runs weekly (Mondays 06:00 UTC) and on demand (`workflow_dispatch` / `repository_dispatch`), invoking `scripts/sync-external.mjs` to mirror a source's files into `plugins/` and open an automated PR. A human reviews every auto-PR — historically ~1 in 10 sync PRs merges. The contributor's own repo is the source of truth; we do NOT locally edit a pure-mirror plugin.

**Mirror vs curate.** Default is a pure mirror — the upstream repo governs, and improvements flow by upstreaming (see below), so the mirror becomes A-grade naturally with nothing to revert. Only when we deliberately harden a plugin past its upstream do we mark it `curated:` and freeze it.

**Never-clobber guard (`curated:` freeze).** A source with `curated: true` in `sources.yaml` is FROZEN: `sync-external.mjs` logs `Curated — mirror frozen`, writes no files (no clone, no overwrite, no orphan-prune), and only keeps the catalog entry current — so even a `--force` sync can never revert our edits. `tonone` and `hyperflow` carry `curated: true` today (we A-graded their agents; upstreaming is planned). This guard exists because a prior `--force` run reverted ~100 A-graded agents back to 3-field upstream stubs — the ~18.9k-line deletion that motivated the whole model. Note `curated:` (we hardened it locally) and `verified:` (a maintainer vetted quality/trust) are orthogonal: tonone/hyperflow are `curated: true` but `verified: false`, an honest state and exactly why the two flags are separate.

**Pileup auto-close (≤1 open sync PR).** `sync-external.yml` runs a "Close superseded sync PRs" step before Create-PR: it closes older open `automation/sync-external-*` PRs (with `--delete-branch`), keeping at most one open sync PR. The safe unique-per-run-branch model (from the 691 audit, which fixed an earlier shared-branch clobber) is preserved — this only prunes the pileup that model produced.

**How we upstream respectfully.** Want a plugin at our A-grade bar? We bring THEIR plugin to standard on THEIR repo: a friendly issue first ("we featured your plugin and hardened its frontmatter to our A-grade bar — would you be open to a PR upstreaming it?"), then a PR the contributor owns and merges. No surprise PRs; credit preserved; they decide. Once merged upstream, the mirror is A-grade naturally and `curated:` can be dropped. **Any contributor-facing post (issue or PR body) gets Jeremy's wording sign-off BEFORE posting.**

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

- **Kernel machine-spec (the SSoT being migrated to):** `@intentsolutions/core` — its `schemas/authoring/v1` family (byte-frozen) plus the strict fork `authoring/v2` — is the single internal source of truth for "what is a valid agent-native artifact." The kernel's `skill-frontmatter` schema encodes the **same** IS 8-field required set as a pure `allOf` of upstream-base + universal folds + the IS overlay. The plan of record is for `validate-skills-schema.py` to **consume the kernel folds** instead of its hand-rolled rule sets. That migration is in progress; the kernel pin is **exactly `0.9.0`** in `package.json` (no `^`/`~`). The `authoring/v1` schema family is byte-frozen across kernel package versions, so this pin bump tracks the latest published kernel without changing the `authoring/v1` contract the shadow lane reads. Contract semantics for `authoring/v1` fields are canonical in the kernel's own changelog — cite it, do not duplicate it (see `000-docs/SCHEMA_CHANGELOG.md` § "Kernel changelog citation").

### Two advisory lanes (never block) running the soak

Both are `continue-on-error: true`, neither is in the required-status set, and neither mutates anything:

- **kernel-shadow soak** — `.github/workflows/kernel-shadow-validation.yml` + `scripts/kernel-shadow-validation.mjs`. Runs the kernel-pinned `skill-frontmatter` schema (from `@intentsolutions/core@0.9.0`) over the same SKILL.md corpus the prose-spec validator grades and logs per-file AGREE / DISAGREE deviation to `scripts/.kernel-shadow/report.json`. This is the DR-049 shadow soak (the "zero-on-corpus shadow signal"). The cutover-relevant number is the **frontmatter-scoped** deviation — a file that fails the prose-spec on missing `[body]` sections but has valid frontmatter is a scope difference, not a kernel gap, and is excluded.
- **kernel-vendor-hash gate** — `.github/workflows/kernel-vendor-hash.yml` + `scripts/kernel-vendor-hash.mjs`. Enforces the version-coupling invariant **V ≤ C ≤ K** (vendored ≤ CCPI-declared ≤ kernel-latest) plus a ≤7-day staleness bound. Soak-aware: it reads the `0.9.0` pin, polices ordering/staleness only, and must never pressure a pin bump or change validator authority.

The validator itself does a kernel-loaded **shadow read** of `ALWAYS_REQUIRED` (`load_kernel_required()` / `--kernel-shadow`) — it compares the kernel's effective required set against the hand-authored one and reports drift. The hand-authored `ALWAYS_REQUIRED` stays authoritative; the shadow read is observational only.

### Do-not-flip soak discipline (do not lose this)

**The kernel pin and the authority flip are two SEPARATE axes — do not conflate them.** The pin tracks the latest published kernel (currently exactly `0.9.0`, no `^`/`~`); bumping it keeps the shadow lane reading a current, byte-frozen `authoring/v1` contract and is a routine governance/coupling update, not an authority change. What stays frozen is the **authority**: do **NOT** flip the kernel-shadow lane from advisory to authoritative (blocking) until ALL of these hold:

1. ≥99.5% corpus agreement (deterministic folds must be 100%; the 0.5% band is reserved for non-deterministic surfaces only);
2. ≥30 days of advisory soak;
3. zero open P0 blockers;
4. the Rekor superseding-event rollback protocol implemented and tested;
5. governance sign-off from the CTO + CISO + VP-DevRel triple; and
6. a ≥14-day public deprecation-window notice to affected skill authors.

As of now the soak has **not** met the bar — agreement sits below 99.5%, and the open disagreements are real tool-safety / shell-substitution security cases that the prose-spec validator correctly blocks (so flipping early would weaken a real gate). Until every condition above is satisfied, validator authority stays with `validate-skills-schema.py` and both kernel lanes stay advisory. Promotion to blocking is a separate, later cutover step gated by these conditions — never a side effect of an unrelated PR.

**Alignment note (`@intentsolutions/jrig-cli`).** The `j-rig` behavioral-eval CLI is a root devDep pinned to **exactly `@intentsolutions/jrig-cli@0.1.2`**, which depends on **`@intentsolutions/core@0.9.0` (exact)** — the same version the **root** `@intentsolutions/core` pin carries — so they resolve to one shared root-hoisted copy and the kernel-shadow + kernel-vendor lanes read it directly. (The `0.1.2` cut carries the eval→Evidence-Bundle bridge `j-rig eval --emit-bundle` [jrig #172], a functional-exec `max_tokens` / length-truncation fix [jrig #173], `j-rig scaffold-spec` from a `SKILL.md` [jrig #174], and a judge-verdict recovery from truncated / fenced JSON that had inflated NO-SHIP [jrig #175]; it also retains the per-test-case `criteria_ids` scoping fix [jrig #162], so `pnpm exec j-rig eval` scopes each criterion to its own test case. A transitive dep, `@intentsolutions/refiner-core@0.2.0`, still peer-wants `core@^0.8.0`; pnpm surfaces that as a non-fatal warning until refiner-core widens its peer range.) The pin bump is a coupling update only; the authority flip and the root-pin cutover to `authoring/v2` remain the separate, gated steps above.

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

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:7510c1e2 -->

## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:

   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```

5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**

- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
