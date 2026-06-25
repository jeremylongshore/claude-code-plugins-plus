# claude-code-plugins ("Tons of Skills") — review context for Greptile

This repo is the **Tons of Skills** marketplace for Claude Code plugins and skills (live at https://tonsofskills.com). It is three things at once:

1. A **catalog** of AI-instruction plugins, MCP-server plugins, skills, agents, and SaaS skill-packs under `plugins/` (~450 entries).
2. A **validator + CI gate system** (`scripts/validate-skills-schema.py` and friends) that grades every authored artifact against the IS marketplace standard.
3. An **Astro website** (`marketplace/`) that renders the catalog.

## Architecture you must respect

- **Two-catalog system.** `.claude-plugin/marketplace.extended.json` is the **source of truth** (edit this). `.claude-plugin/marketplace.json` is **auto-generated** by `pnpm run sync-marketplace` — never hand-edit it; CI's drift gate rejects divergence. The same step generates plugin `package.json`s and the README AUTO-TOC block.
- **The prose-spec validator is authoritative.** `scripts/validate-skills-schema.py` is the canonical gate. The `@intentsolutions/core` kernel is the SSoT being migrated to, currently in an **advisory soak** — do not promote the kernel CI lanes from advisory to blocking, and do not bump the frozen kernel pin.
- **External-sync pipeline.** `sources.yaml` + `scripts/sync-external.mjs` mirror external plugin repos into `plugins/`; synced plugins carry a `.source.json` marker.
- **Package managers:** pnpm everywhere **except `marketplace/` (npm)**, CI-enforced. Node >= 20 (Node 18 breaks workspace resolution).

## Prioritize (in order)

- **Correctness** — especially in the validator, the sync engine (`scripts/sync-external.mjs`), the marketplace build pipeline, and the CLI (`packages/cli`).
- **Security** — secrets (gitleaks/trufflehog), Unicode trapdoors (Trojan Source / bidi overrides), supply-chain, and prompt/tool safety in agent & skill definitions.
- **Gate integrity** — never weaken a CI threshold, test, or assertion (see the `no-gate-weakening` rule).
- **Catalog & data integrity** — generated-vs-source drift, required-fields / tier semantics, kernel-soak discipline.
- **Regression risk** across the ~450 catalog entries when a change touches shared scripts or config.

## Deprioritize

- Style-only or subjective-naming comments — eslint, prettier, ruff, markdownlint, and the Python validators already cover these.
- Churn on generated files: `.claude-plugin/marketplace.json`, generated `package.json`s, the README TOC, `marketplace/dist/`, `marketplace/public/downloads/`.
- Comments that merely duplicate an existing linter or typechecker.

## Related repos (multi-repo context)

This repo depends on **`@intentsolutions/core`** (the authoring-schema kernel SSoT — a separate package/repo) and deploys to tonsofskills.com via the **intentsolutions-vps-runbook** repo. Greptile's current config schema does not expose a multi-repo `patternRepositories` key, so these are noted here for reviewer context rather than wired into `config.json`.
