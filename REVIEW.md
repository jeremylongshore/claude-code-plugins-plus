# REVIEW.md

Repository-specific guidance for the automated pull-request reviewer (MiniMax, two advisory lanes).

Catch defects, unsafe claims, mirror/supply-chain drift, and standard violations that CI cannot
phrase for a human. Report only findings introduced by the pull request and verify each against the
surrounding source. The deterministic grade is produced by the validators CI runs
(`validate-skills-schema.py`, the agent validator, `pr-prescreen`); the reviewer's job is to make
that standard legible and to coach contributors to **grade A**.

## Review objective

Tons of Skills is a Claude Code plugins + skills marketplace. Its value is a **trusted, single-standard
catalog**: every listing meets one enforced frontmatter standard, external content is _mirrored and
graded_ rather than blindly trusted, and quality is held to an A bar. Review for standard compliance,
mirror/supply-chain integrity, honest quality claims, and correctness — in that order of risk.

## Authority and truth hierarchy

Read `CLAUDE.md` and `AGENTS.md` first. For schema/standard questions, `000-docs/SCHEMA_CHANGELOG.md`
(the NON-NEGOTIABLES section) and `000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md` govern.

1. `.claude-plugin/marketplace.extended.json` is the **source of truth** for the catalog. `marketplace.json`,
   `plugins/**/package.json`, and the README AUTO-TOC are **generated** by `pnpm run sync-marketplace`.
2. The prose-spec validator (`scripts/validate-skills-schema.py`) is **authoritative** for grading; the
   kernel lanes are advisory soak (never blocking). Do not treat a kernel-shadow result as the grade.
3. Green CI proves only the checks that ran — not that a plugin is high quality, that a mirror matches
   its upstream, or that a claimed grade is real.
4. Historical records (docs, AARs, decision records) describe what was known then; require a dated
   correction or successor, never a silent rewrite.

Flag silent boundary changes, a second source of truth competing with `marketplace.extended.json`, or a
PR description presented as authority.

## The enforced standard (coach contributors to grade A)

Know these rules and pre-empt the validators; tell a contributor exactly what to fix.

- **SKILL.md, marketplace tier — all 8 fields required:** `name`, `description`, `allowed-tools`,
  `version`, `author`, `license`, `compatibility`, `tags`. A missing or renamed field fails the gate.
- **A-grade further needs:** a `description` that says _when to use it_ and a **Trigger** phrase;
  **least-privilege** `allowed-tools` (only what the skill uses); real topical `tags` (not filler); and
  the required body sections. `compatible-with` is deprecated — migrate to free-text `compatibility`.
- **Agents are kernel-strict (errors at every tier):** `name`, `description`, `tools`, `model`
  (`sonnet`/`haiku`/`opus`/`fable`/`inherit`), `color`, `version`, `author`, `tags`; plus
  `disallowedTools`/`skills`/`background` where applicable. Banned fields (`capabilities`,
  `expertise_level`, `activation_priority`, `type`, `category`, `compatible-with`, `when_to_use`) are
  errors. An agent body that invokes an `mcp__server__tool` **not** in its `tools` allowlist is an error.
  Agents use `disallowedTools` (camelCase); skills use `allowed-tools` and optional `disallowed-tools`
  (kebab-case) — do not cross them.
- **New plugin dirs** ship the tiered submission docs (`docs/PRD.md`; + `ADR.md`; + `ONE-PAGER.md` per
  the matrix in `templates/skill-docs/README.md`) **unless** the dir is an external mirror
  (`.source.json` present).

## Mirror and supply-chain integrity (highest-risk boundary)

The catalog mirrors ~57 external sources by default; the guard is _mirror-by-default · never clobber_.

- A plugin carrying a **`.source.json`** is an upstream mirror — the upstream repo governs. **Flag any
  local edit to a pure mirror.** Improvements go upstream, not into the mirror.
- A source marked **`curated: true`** in `sources.yaml` is **FROZEN** — flag any change that reverts it
  toward its upstream stub (a `--force` sync once deleted ~18.9k lines of hardened agents; this is why
  the freeze exists). Note `curated:` (we hardened it) and `verified:` (a maintainer vetted it) are
  **orthogonal** — never let one imply the other.
- Flag secrets, tokens, API keys, or unsafe install payloads (`curl | bash`, unpinned installs) in any
  synced content. **Never reproduce a suspected secret in a comment — name only its location and the
  remediation.** `scan-synced-content` blocks REFUSE patterns; a `sources.yaml`-only change is a
  waivable CHALLENGE, not a free pass.

## Grading, freshie, and Dolt integrity

- **freshie is local-sole-writer.** `inventory.sqlite` is the untracked runtime blob; the versioned
  system of record is Dolt, exported to public DoltHub. Flag anything that would **web-edit DoltHub**,
  merge a DoltHub PR, or export an **incomplete discovery run** (a run with `total_skills IS NULL` must
  hard-fail before any push) — the exporter is one-way and will clobber external edits.
- The tracked `freshie/grades.csv` + `grade-histogram.json` are the human-legible grade diff; the
  `skills/.curated/` mirror is generated (wipe-and-rebuild) — flag hand-edits to either.

## Generated artifacts — never hand-edited

`.claude-plugin/marketplace.json`, every `plugins/**/package.json`, the README AUTO-TOC block,
`marketplace/src/data/*` build artifacts, `skills/.curated/**`, and `marketplace/public/downloads/**`
are all regenerated. Flag hand-edits; direct the change to the source
(`.claude-plugin/marketplace.extended.json`, `sources.yaml`, or the skill/plugin files) instead.

## CI gate architecture (do not restate what it enforces)

The merge gate is exactly `ci-required` (an aggregate of the validate/verify/test/lint jobs) +
`gitleaks`. AI review and the kernel lanes are **advisory and never blocking**. Do not duplicate
markdownlint/eslint/ruff/prettier/gitleaks findings or push a plugin's blocking check into the required
set from a side PR. Report the human-facing "here is what to fix," not the mechanical lint output.

## Claims and evidence integrity (adversarial lane)

Judge quality claims against reality. A grade (A/B) is real only if the validator/freshie pipeline
produced it. "Synced/mirrored" is not "vetted"; "curated" is not "verified"; a README/badge count is
not proof it matches `marketplace.extended.json`; a merged doc is not a working, graded plugin. Flag
unsupported words (`verified`, `production-ready`, `A-grade`, `complete`), silent scope/standard
changes, and a diff that does materially more or less than its description claims.

## Anti-ratchet

On a re-review after new pushes, the bar does not rise: drop findings the update resolved, and do not
invent new objections on unchanged lines you previously accepted. Prefer a few high-conviction findings;
if the change is correct, compliant, and safe, reply `lgtm`. The reviewer is advisory only and never
blocks a merge.
