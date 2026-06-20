# 6767-h ↔ kernel `authoring/v1` Mapping

**Document ID**: 690-AT-APIS-6767h-to-kernel-authoring-v1-mapping
**Version**: 1.0.0
**Status**: REFERENCE (advisory — documents prose-spec ↔ machine-spec coherence; non-normative)
**Created**: 2026-06-11
**Authority**: Intent Solutions

**Purpose**: A bidirectional citation table mapping the **prose master spec** —
`000-docs/6767-h-SPEC-DR-STND-claude-code-extensions-master.md` (and its source
section `6767-b §4 YAML Frontmatter Fields`) — to the **machine spec**: the
published `skill-frontmatter` authoring contract in
[`@intentsolutions/core@0.4.1`](https://www.npmjs.com/package/@intentsolutions/core)
under `schemas/authoring/v1/`. This documents where prose ↔ machine agree, and
the small set of **intentional divergences** the kernel-shadow validator
(`scripts/kernel-shadow-validation.mjs`) surfaces on the live corpus.

> **Scope note (cutover step 1).** This is the first artifact of the CCPI consumer
> cutover to the Spec Authority Kernel (SSoT). It is **documentation only** —
> nothing in this doc changes the existing validator
> (`scripts/validate-skills-schema.py`) or the required CI gate
> (`validate-plugins.yml`). The kernel runs in **shadow / advisory** mode only.

---

## 1. The two specs

| | Prose spec (human-authored) | Machine spec (kernel SSoT) |
|---|---|---|
| **Artifact** | `6767-h` master standard; source detail in `6767-b §4` | `@intentsolutions/core@0.4.1` `schemas/authoring/v1/skill-frontmatter.schema.json` |
| **Form** | Markdown prose + the 5,100-line `validate-skills-schema.py` that operationalizes it | JSON Schema 2020-12, pure `allOf` composition of three layers |
| **Enforced by** | `validate-skills-schema.py` (required CI: `validate-plugins.yml`) | `kernel-shadow-validation.mjs` (advisory CI: `kernel-shadow-validation.yml`) |
| **Required set** | IS 8-field marketplace set (`6767-b §4` NON-NEGOTIABLE) | Same 8-field set (effective-required = base ∪ overlay) |

The kernel `skill-frontmatter.schema.json` is a **pure composition** (zero
authored fields of its own) — the `allOf` of:

1. `upstream-base/skill-frontmatter.v1.json` — the agentskills.io + Claude-docs
   floor (`name`, `description` required; `license`, `compatibility`, `metadata`
   optional). Authored by the open standard, vendored as a projection.
2. `marketplace-tier.schema.json#/$defs/universalFolds` — the three universal
   folds (`deprecationRegistry`, `securityChecks`, `disclosureMarkers`).
3. `is-overlay/skill-frontmatter.v1.json` — the Intent-Solutions-only delta
   (promotes 4 upstream-optional fields to required, adds 3 net-new required
   tracking fields, narrows types).

Effective required = base `{name, description}` ∪ overlay
`{allowed-tools, version, author, license, compatibility, tags}` =
the **IS 8-field marketplace required set** — identical to the prose-spec
`ALWAYS_REQUIRED` (`validate-skills-schema.py` line ~406).

---

## 2. Field-by-field bidirectional map

Schema paths below are relative to
`node_modules/@intentsolutions/core/schemas/authoring/v1/` (the pinned 0.4.1
package). "→" = prose citation; "⇐" = the machine layer that owns the rule.

| Field | Prose spec → (`6767-h` / `6767-b`) | Machine spec ⇐ (kernel layer + constraint) | Coherent? |
|---|---|---|---|
| `name` | `6767-h §3.1`; `6767-b §4.1` — required; ≤64 chars; lowercase/digits/hyphen; no reserved words; no XML | `upstream-base` (`required`, `maxLength:64`, `pattern ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`) + `securityChecks` (reserved-word `enum` + `[<>]` ban) | ✅ |
| `description` | `6767-h §3.1`; `6767-b §4.1` — required; non-empty; third-person; **≤1024 chars** (prose); no XML | `upstream-base` (`required`, `minLength:1`) + `disclosureMarkers` (**≤1536 chars**) + `securityChecks` (`<[^>]+>\|\$\{` ban) | ⚠️ §4.1 |
| `allowed-tools` | `6767-h §3.1` — **"MUST be a CSV string"**; `6767-b §4` — "CSV / space-separated / YAML list (all three accepted, v3.3.1)" | `is-overlay` (`required`, **`type:array`, `items:string`**) | ⚠️ §4.2 |
| `version` | `6767-b §4.6` — required; semver `X.Y.Z` | `is-overlay` (`required`, **strict SemVer 2.0.0 `pattern`**) | ⚠️ §4.3 |
| `author` | `6767-h §3.1`; `6767-b §4.6` — required; non-empty | `is-overlay` (`required`, `minLength:1`) | ✅ |
| `license` | `6767-h §3.1`; `6767-b §4.6` — required; non-empty | `is-overlay` (`required`, `minLength:1`) | ✅ |
| `compatibility` | `6767-b §4.5/§4.6` — required; free-text; ≤500 chars | `is-overlay` (`required`, `minLength:1`) + `upstream-base` (`maxLength:500`) | ✅ |
| `tags` | `6767-b §4.6` — required (pure IS invention, zero upstream provenance) | `is-overlay` (`required`, `type:array`, `items:string`) | ✅ |
| `compatible-with` (legacy) | `6767-b §4.5` — deprecated → `compatibility` | `deprecationRegistry` (present key = fold failure; names replacement) | ✅ |
| `when_to_use` (legacy) | `6767-b §4` optional-fields list — folded into `description` | `deprecationRegistry` (deprecated → `description`) | ✅ |
| `requires_env` / `requires_tools` / `fallback_for_env` / `fallback_for_tools` / `required_environment_variables` | `6767-b` IS optional extensions (validator schema 3.5.0/3.6.0) | `is-overlay` optional properties (typed arrays / object array) | ✅ |
| `model`, `effort`, `argument-hint`, `arguments`, `paths`, `shell`, `context`, `agent`, `user-invocable`, `disable-model-invocation`, `hooks`, `metadata` | `6767-b §4` optional Anthropic/AgentSkills.io fields — validated only when present, never required | Not constrained by the `skill-frontmatter` composition (open-world; per-contract schemas own their own closed-world checks) | ✅ |

---

## 3. Intentional divergences (the shadow signal)

These are the cases where the machine spec deliberately differs from the prose
spec. They are the dominant source of the kernel-shadow deviation rate and are
**by design** — the kernel is the convergence target, the prose validator is the
current production floor. Each divergence is a documented coherence gap, not a
bug in either spec.

### §4.1 — `description` length: prose 1024 vs kernel 1536

- **Prose**: `6767-b §4.1` caps `description` at **1024 chars** (the
  agentskills.io soft cap); `validate-skills-schema.py` emits an ERROR above it.
- **Machine**: the `disclosureMarkers` universal fold operates at the IS
  **1536-char** token budget; `upstream-base` intentionally does **not** encode
  the 1024 cap (encoding it would conflict with the 1536 tier and violate the
  monotonic-additive invariant — the base must be the loosest layer).
- **Effect on corpus**: a small number of files with 1024–1536-char descriptions
  are `existing-FAIL / kernel-PASS` (the prose spec is stricter here).
- **Resolution path**: ISEDC Class-1 decision on the canonical cap. Until then,
  the kernel's 1536 budget is the documented machine value; the prose 1024 stays
  the production floor.

### §4.2 — `allowed-tools` type: prose CSV-string vs kernel YAML-array

- **Prose**: `6767-h §3.1` states `allowed-tools` **MUST be a CSV string**;
  `6767-b §4` (validator 3.3.1) relaxed this to accept **three** forms — CSV
  string, space-separated string, **or** YAML list — all passing.
- **Machine**: `is-overlay` **narrows** `allowed-tools` to a **YAML array of
  strings only** (`type:array`); a bare string is a type error. This is a
  permitted narrowing under the monotonic-additive invariant (the open standard
  marks `allowed-tools` EXPERIMENTAL with a space-separated wire form; IS fixes
  the array form).
- **Effect on corpus**: this is the **dominant deviation** — the overwhelming
  majority of the corpus authors `allowed-tools` as a CSV/space string, so those
  files are `existing-PASS / kernel-FAIL` with `/allowed-tools must be array`.
- **Resolution path**: a corpus migration (CSV-string → YAML-list) is the
  precondition for promoting the kernel from shadow to blocking on this field.
  **Not in scope for cutover step 1** — the shadow exists precisely to size this
  migration. The `6767-h §3.1` "MUST be a CSV string" line should be reconciled
  to the `6767-b §4` three-form prose in a follow-up doc edit, with the kernel's
  YAML-array target called out as the convergence direction.

### §4.3 — `version` strictness: prose prefix-match vs kernel strict SemVer

- **Prose**: `6767-b §4.6` requires semver `X.Y.Z`; the legacy validator uses an
  unanchored prefix match (it accepted `1.2.3.4` / `1.2.3-anything`).
- **Machine**: `is-overlay` enforces the **strict SemVer 2.0.0** pattern.
- **Effect on corpus**: marginal — most versions are already clean `X.Y.Z`. A few
  malformed versions could be `existing-PASS / kernel-FAIL`.
- **Resolution path**: fix the malformed versions; the kernel's strict pattern is
  the documented target. The prose validator's prefix-match is the looser floor.

### Backtick-in-`description` (prose-only heuristic)

`validate-skills-schema.py` flags a `description` containing backticks / `$(...)`
as shell-substitution and ERRORs. The kernel `securityChecks` fold only bans XML
tags (`<[^>]+>`) and `${` — it does **not** match bare backticks. A description
with backtick code-spans is therefore `existing-FAIL / kernel-PASS`. This is a
prose-spec heuristic with no machine-spec counterpart; the resolution is to
decide whether the backtick check is a true security rule (then add it to
`securityChecks`) or an over-broad heuristic (then relax the prose validator).
Tracked as a coherence note, not actioned in step 1.

---

## 4. How the mapping is enforced (advisory)

The coherence documented above is **measured continuously** by the kernel-shadow
validator, which runs both specs over the live corpus and reports the per-file
AGREE / DISAGREE deviation rate:

| Layer | File | Mode |
|---|---|---|
| Shadow script | `scripts/kernel-shadow-validation.mjs` | report-only |
| Advisory workflow | `.github/workflows/kernel-shadow-validation.yml` | `continue-on-error`, **not** in required-status set |
| Deviation report | `scripts/.kernel-shadow/report.json` | CI artifact + job summary |

Running the shadow locally (`node scripts/kernel-shadow-validation.mjs`) prints
the deviation rate and lists the disagreeing files with the first kernel error
per file. As of the cutover-step-1 baseline, the dominant deviation bucket is
§4.2 (`allowed-tools must be array`), exactly as predicted by this mapping.

---

## 5. Citations

- Prose master spec: `000-docs/6767-h-SPEC-DR-STND-claude-code-extensions-master.md` §3
- Prose field detail: `000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md` §4 (§4.1, §4.5, §4.6)
- NON-NEGOTIABLES: `000-docs/SCHEMA_CHANGELOG.md`
- Machine spec (pinned 0.4.1):
  - `@intentsolutions/core/schemas/authoring/v1/skill-frontmatter.schema.json` (composition)
  - `.../upstream-base/skill-frontmatter.v1.json`
  - `.../is-overlay/skill-frontmatter.v1.json`
  - `.../marketplace-tier.schema.json` (`#/$defs/universalFolds`)
- Kernel SSoT declaration: `intent-eval-lab/000-docs/045-RR-LAND-single-source-of-truth-and-continuous-spec-compliance-2026-06-09.md`
- Open standard: https://agentskills.io/specification
- Anthropic surfaces: https://code.claude.com/docs/en/skills · https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

---

*This is a reference doc for prose ↔ machine spec coherence during the kernel
consumer cutover. It is advisory and non-normative; the existing validator and
the required CI gate remain the production authority until a later, explicit
blocking-cutover step.*
