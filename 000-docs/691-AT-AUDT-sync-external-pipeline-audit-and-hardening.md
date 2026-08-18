<!-- doc-class: record -->

# External-Plugin Sync Pipeline — Audit & Hardening

**Date:** 2026-06-24
**Scope:** `scripts/sync-external.mjs`, `.github/workflows/sync-external.yml`, and the validate gates that grade synced output.
**Trigger:** A real sync of the `beads-dolt` plugin failed repeatedly and could not be landed through the pipeline (it was ultimately vendored directly). This audit determined why and hardened the pipeline.

## Method

A multi-agent audit was run (55 sub-agents, ~6.3M tokens):

1. **6 parallel auditors**, one per failure dimension — file-mode/`+x` preservation, post-sync onboarding, branch/force-push concurrency, PR-create + auto-bump lifecycle, catalog/version integrity, and a completeness critic.
2. **Synthesis** — deduped into a definitive, evidence-grounded bug list.
3. **Adversarial verification** — each proposed fix hit by 3 independent skeptics (does it solve the bug / does it regress the ~60 other synced plugins / is there a simpler-safer fix). **0 first-pass fixes survived clean** — every one was refined.

### Traps the adversarial pass caught (why the triple-check mattered)

- The `+x` fix coupled a Buffer read that left the change-detector comparing Buffer-to-string → would mark **all ~60 plugins "modified" every run**. Revised to a Buffer-safe `.equals()`.
- The markdownlint "durable fix" used a **non-existent `--ignore` flag**. Revised to a drift-checked codegen.
- A proposed `catalog == package.json` version invariant would have **hard-failed 433/452 plugins** on the first unrelated PR. Rejected.
- The catalog-seam "robust" full-rewrite would have blown the **+400-line catalog-format CI budget**. Revised to a 1-char newline insert.

## The 16 bugs

| Severity | ID                                                      | Summary                                                                                           | Status                 |
| -------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------- |
| blocker  | `synced-sh-loses-executable-bit`                        | Synced `scripts/*.sh` lose `+x` → "Check plugin structure" fails                                  | ✅ fixed               |
| blocker  | `binary-files-corrupted-not-skipped`                    | utf8 read+write corrupts binaries (e.g. kobiton's bundled binary)                                 | ✅ fixed (Buffer read) |
| blocker  | `workflow-runs-cjs-only-no-package-json`                | Workflow runs only `sync-marketplace.cjs` → no `package.json` → catalog-invariant fails           | ✅ fixed               |
| blocker  | `workflow-runs-cjs-only-stale-readme-toc`               | Same → README TOC stale → "Verify README TOC" fails                                               | ✅ fixed               |
| blocker  | `markdownlint-ignores-drift-beads-dolt`                 | Hand-maintained markdownlint `ignores` drifts; new synced `.md` fails                             | 📋 tracked             |
| blocker  | `ruff-no-synced-dir-exclusion`                          | `ruff` scans synced `.py` with no synced-dir exclusion → fails                                    | 📋 tracked             |
| blocker  | `shared-branch-force-push-clobbers-prior-sync`          | Force-push of shared `sync/external-plugins` clobbers concurrent runs / manual fixes              | ✅ fixed               |
| blocker  | `pr-create-guard-matches-merged-pr`                     | `gh pr view <branch>` matches an old **merged** PR → skips opening a new one                      | ✅ fixed               |
| high     | `auto-bump-fires-on-sync-pr-version-drift`              | auto-bump bumps synced plugin while catalog version stays → drift + `action_required` stall       | ✅ fixed               |
| high     | `catalog-entry-malformed-seam`                          | `ensureCatalogEntry` jams `},    {` onto one line → catalog-format flag                           | ✅ fixed               |
| high     | `synced-gitignored-files-dropped`                       | Synced files matching `.gitignore` silently dropped by `git add -A` (e.g. slack-channel `.npmrc`) | 📋 tracked             |
| medium   | `package-json-generator-pollutes-nested-synced-plugins` | Generator scaffolds `package.json` for nested upstream sub-manifests                              | 📋 tracked             |
| medium   | `mode-only-change-never-corrected`                      | A wrong-mode synced script never self-heals (compare is content-only)                             | 📋 tracked             |
| medium   | `no-orphan-prune-on-upstream-removal`                   | Sync is additive-only → never deletes files upstream removed/renamed                              | 📋 tracked             |
| medium   | `partial-sync-shipped-as-clean-full-sync`               | A source that errors / finds 0 files is still committed + PR'd as clean                           | 📋 tracked             |
| low      | `matchespattern-no-extglob-silent-noop`                 | Patterns using bash extglob/brace/char-class semantics silently no-op                             | 📋 tracked             |

## Fixed in this change (8)

**`scripts/sync-external.mjs`**

- `walkFiles` reads file content as a **Buffer** (not utf8) and captures the upstream `mode`. Fixes binary corruption; enables `+x` restore.
- Change-detection compares **Buffer `.equals()`** (not `!==` against a string), so unchanged files are not re-written every run. _Regression-tested:_ a dry-run of an already-synced source reports "No changes detected."
- After write, `fs.chmodSync(target, mode & 0o777)` restores the upstream rwx bits — executable scripts stay `100755`; non-executable files keep their mode.
- `ensureCatalogEntry` inserts a newline so the seam is `},\n    {` instead of `},    {`.

**`.github/workflows/sync-external.yml`**

- The post-sync step runs the **full `pnpm run sync-marketplace`** (catalog + `generate-plugin-package-jsons.mjs` + `generate-readme-toc.mjs`), not just the `.cjs` catalog step.
- The PR branch is now a **unique per-run `automation/sync-external-<run_id>`**: no force-push of a shared branch (no clobber), the `automation/` prefix makes `auto-bump-on-pr.yml` skip it (no version drift — that workflow already excludes `automation/*`), and a unique name can never collide with an old merged PR (the `gh pr view` guard now reliably opens a fresh PR).
- A `concurrency: { group: sync-external, cancel-in-progress: false }` block serializes runs.

## Tracked follow-ups (8) — verified fixes available

- **markdownlint / ruff synced-dir exclusion drift** (2 blockers): add `scripts/sync-lint-ignores.mjs` deriving the `.markdownlint-cli2.jsonc` `ignores` block **and** `ruff.toml` `extend-exclude` from `.source.json` dirs, with a `--check` CI drift gate; wire it into the sync workflow so a new source self-registers. (Skeptic note: `markdownlint-cli2 --ignore` is not a real flag; keep the config authoritative.)
- **`synced-gitignored-files-dropped`** (high): scope a `.gitignore` negation for genuinely-synced files (e.g. `!plugins/mcp/slack-channel/.npmrc`) and have the engine `git check-ignore` synced paths and warn loudly on a silent drop.
- **`package-json-generator-pollutes-nested-synced-plugins`**, **`mode-only-change-never-corrected`**, **`no-orphan-prune-on-upstream-removal`**, **`partial-sync-shipped-as-clean-full-sync`**, **`matchespattern-no-extglob-silent-noop`** (medium/low): see the full audit record for each refined fix.

## Note on `beads-dolt`

beads-dolt was **vendored** directly (`plugins/mcp/beads-dolt`) rather than waiting on these fixes. Its `sources.yaml` entry remains as the upstream-of-record; once `markdownlint`/`ruff` exclusion drift is closed, the sync can manage it like any other external plugin.
