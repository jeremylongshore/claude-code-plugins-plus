# Schema Changelog — Claude Code Skills Spec (Intent Solutions)

This file tracks every change to the validator's required-fields set, field
migrations (deprecations, removals, renames), validator script versions, and
master-spec-doc revisions. It is **separate** from the main repo `CHANGELOG.md`
and is versioned independently.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Schema version follows [Semantic Versioning](https://semver.org/) where:

- **MAJOR** — breaking changes to required-fields set, validator API surface,
  or rejected/accepted-fields semantics.
- **MINOR** — additive changes (new optional fields, new tier, additional
  marketplace polish recommendation).
- **PATCH** — clarifications, doc updates, internal refactors with no
  observable change to validator output.

Cross-references:

- Master spec doc: `000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md`
- Validator: `scripts/validate-skills-schema.py`
- Bulk-fix tool: `scripts/batch-remediate.py`
- Repo-level releases: `CHANGELOG.md`

---

## NON-NEGOTIABLES — read before touching this file

Established 2026-04-28 after a one-day schema debacle (see "How we got here"
below). These rules are NOT to be relaxed without explicit written approval
from Jeremy Longshore in the issue/PR thread BEFORE the change lands.

1. **`ALWAYS_REQUIRED` is the IS enterprise 8-field set:**
   ```
   {name, description, allowed-tools, version, author, license, compatibility, tags}
   ```
   This is intentionally stricter than Anthropic's published spec. Do not
   reduce it. Do not reframe it as "marketplace polish" or "tracking
   recommendations." It's the canonical IS rubric.

2. **Marketplace tier produces ERRORS for missing required fields, not
   warnings.** Demoting required-field errors to warnings breaks the
   marketplace gate.

3. **The IS rubric SITS ON TOP of Anthropic's spec.** It does not replace
   Anthropic's spec, and it does not need to match Anthropic's spec floor.
   Anthropic's spec is intentionally permissive (every field is optional);
   the IS marketplace is intentionally strict.

4. **Spec source priority for technical correctness:**
   1. [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) — primary, complete frontmatter reference
   2. [agentskills.io/specification](https://agentskills.io/specification) — open standard Claude Code follows
   3. [platform.claude.com/docs/en/agents-and-tools/agent-skills/overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — API surface
   4. The IS enterprise rubric layered on top — additive, never subtractive

5. **Tracking metadata (version, author, license) is REQUIRED at marketplace
   tier, not optional polish.** Anthropic doesn't track these in their own
   reference repo; that's their stylistic choice. The IS marketplace requires
   them for trust signals, downstream pinning, and legal clarity.

6. **Bug fixes that bring the validator into spec compliance are always OK
   to apply autonomously.** Examples: accepting YAML lists for `allowed-tools`,
   fixing conditional-field rules to match documented defaults, adding
   missing documented fields like `arguments` / `paths` / `shell`. These
   are technical-correctness fixes — not "spec realignment."

7. **Architectural changes (required-fields set, tier model, error vs
   warning semantics) need explicit approval BEFORE the change lands.**

---

## How we got here — the 2026-04-28 schema debacle

This section exists so the same mistake doesn't get re-made. The full
back-and-forth is preserved below in the version-by-version changelog.

**The mistake**: starting from a valid observation ("the IS validator requires
8 fields where Anthropic's published spec only requires 2"), I drove four
schema-version churns trying to "realign" the IS rubric to Anthropic's
permissive floor. Each time, the user pushed back; each time, I added a
correction layer instead of stopping. End state: same enterprise standard
we started with, plus a few genuine technical fixes (compatibility migration,
allowed-tools YAML-list parsing, conditional-field rules), at the cost of
a day of churn and four schema versions.

**Why it was wrong**: the IS enterprise rubric is intentionally stricter than
Anthropic's spec. That's the value-add. Reducing it to match the spec floor
deletes the value. Anthropic's spec being permissive is not a bug we need
to fix in our rubric; it's a feature of the *open* spec that the *enterprise*
layer sits on top of.

**Process failure**: I worked off summaries of the Anthropic spec instead of
reading [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)
line-by-line first. When the user pushed back the first time, I did a deeper
read but kept the "spec realignment" framing instead of recognizing it as
the wrong direction. Each subsequent correction was a half-fix that the user
had to reject again.

**What stuck (the kept changes from the experiments)**:

- `compatible-with` (closed CSV platform list) → `compatibility` (free-text per AgentSkills.io spec). The deprecated alias still parses; `batch-remediate.py --migrate-compatible-with` migrates files in bulk.
- `when_to_use` correctly reclassified as documented Anthropic optional (was wrongly flagged as deprecated in earlier IS rubrics).
- `arguments`, `paths`, `shell` added to schema registry with type validation — all documented Anthropic optional fields that were missing from the registry.
- `effort: xhigh` added to valid values per Anthropic doc (`low/medium/high/xhigh/max`).
- `allowed-tools` now accepts both YAML list and space-separated string per Anthropic spec (was previously rejecting YAML lists and only splitting on commas).
- `agent` field no longer triggers "missing required" warning when absent with `context: fork` (Anthropic doc: "If omitted, uses general-purpose").
- `argument-hint` conditional fixed (no longer falsely suppressed by `disable-model-invocation: true` since the user can still invoke via `/`).
- `${CLAUDE_EFFORT}` added to YAML substitution allow-list.
- New tooling: `scripts/batch-remediate.py` for bulk migrations.
- New doc: this `SCHEMA_CHANGELOG.md` (was no schema-level changelog before).

**What got reverted (the structural changes that should have never happened)**:

- Reducing `ALWAYS_REQUIRED` from 8 fields to {name, description}. Reverted.
- Reframing tier model so marketplace was warnings-only. Reverted to errors-only.
- Reclassifying `version`/`author`/`tags` as `source: 'tracking'` / `'marketplace polish'`. Reverted to `source: 'enterprise'`.
- Rewriting `templates/skill-template.md` as a "supreme canonical form" with placeholders for every documented field. Reverted to enterprise template (8 required fields filled in, optional fields commented).
- Rewriting `frontmatter-spec.md` section 3 as "Tracking & Marketplace Polish Fields." Reverted to "Intent Solutions Enterprise Required Fields."

**The dance not to repeat**: don't try to "realign IS to Anthropic spec." The two
operate at different layers. IS = strict enterprise rubric. Anthropic = permissive
open spec. The validator already knows about both. Bug fixes that improve spec
compliance are welcome; structural changes to the IS rubric are not.

---

## [3.3.1] — 2026-04-28 — Spec-compliance bug fixes (no architectural changes)

After the 3.3.0 restoration, a careful re-read of [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) found three concrete bugs where the validator diverged from Anthropic's documented behavior. All three are pure spec-compliance fixes — no IS architectural changes.

### Fixed

- **`allowed-tools` YAML list form accepted.** Anthropic doc: *"Accepts a space-separated string or a YAML list."* Validator was rejecting YAML lists with the message *"must be a comma-separated string (CSV), not a YAML array"*. Now accepts both forms; YAML list, space-separated string, comma-separated string, and mixed forms all parse correctly.
- **`allowed-tools` space-separated parsing.** Anthropic's canonical example uses space-separated form: `Bash(git add *) Bash(git commit *) Bash(git status *)`. Old parser only split on commas, which would treat the whole string as one tool. New parser is paren-depth-aware so multi-word tools like `Bash(git add *)` stay as one token in space-separated form.
- **`agent` field no longer warns "missing" when defaulting to general-purpose.** Anthropic doc: *"If omitted, uses general-purpose."* Old `CONDITIONAL_FIELDS` rule warned that `agent` was missing whenever `context: fork` was set. Removed.
- **`argument-hint` conditional rule.** Was: `user-invocable=true AND disable-model-invocation=false`. Anthropic doc: `disable-model-invocation: true` only blocks Claude's auto-invocation; the user can still invoke via `/`. So argument-hint is still relevant when `disable-model-invocation: true`. Fixed to: `user-invocable=true` only.

### Added

- **`${CLAUDE_EFFORT}`** added to `YAML_VALUE_ALLOWED_VARS` allow-list. Documented Anthropic substitution variable for the current effort level.

### Backward compatibility

Non-breaking. All existing skills that passed at 3.3.0 still pass at 3.3.1 with same or fewer warnings. Skills that were previously rejected for using YAML-list `allowed-tools` form now pass.

---

## [3.3.0] — 2026-04-28 — Restored 8-field enterprise standard

The 3.0.0–3.2.0 experiments tried to relax the IS enterprise rubric toward an "Anthropic spec floor" of `{name, description}` only. That direction made the standard worse, not better — the marketplace needs full tracking + governance metadata on every shipped skill, not just the two minimal Anthropic-required fields. This release reverts that direction.

### What's restored

- **`ALWAYS_REQUIRED` is back to 8 fields**: `{name, description, allowed-tools, version, author, license, compatibility, tags}`. Missing any of these = ERROR at marketplace tier. Same as the original IS rubric, with the only change being `compatible-with` → `compatibility` (the kept fix from 3.0.0).
- **Marketplace tier presence-check logic** restored to strict-enforcement form. Removed the per-field "tracking-reason" warning text (the warnings became errors again, no commentary needed).
- **`version`/`author`/`tags` `source` label** back to `'enterprise'` from `'tracking'`. They're enterprise-required fields, not optional metadata.
- **Templates and docs** restored to enterprise framing — required = full 8-field set, optional = the documented Anthropic fields you customize on top.

### What's kept from the experiments (genuine improvements only)

- **`compatible-with` → `compatibility` migration** (from 3.0.0). This is the only architectural change retained. Free-text per AgentSkills.io spec, max 500 chars. `compatible-with` remains parsed as a deprecated alias with migration suggestion.
- **`when_to_use` correctly classified as documented Anthropic optional** (from 3.1.0). Earlier IS rubrics treated it as deprecated; that was wrong per `code.claude.com/docs/en/skills`.
- **`arguments`, `paths`, `shell` added to `SKILL_FIELDS`** (from 3.1.0) as documented Anthropic optional fields with type validation.
- **`effort: xhigh`** added to valid values (from 3.1.0) per Anthropic's documented `low/medium/high/xhigh/max`.
- **1,536-char combined cap** validation for `description` + `when_to_use` per Anthropic's documented limit.
- **`scripts/batch-remediate.py --migrate-compatible-with`** tool (from 3.0.0) for bulk migrations.
- **`Skill()` permission rule documentation** in skill-creator references (Skill(name) exact / Skill(name *) prefix).

### What's reverted

- Required-fields reduction to {name, description} → reverted to 8-field enterprise standard
- "Standard tier vs marketplace tier" framing where marketplace was just warnings → reverted to strict-error marketplace tier
- `version/author/tags` reclassification as "tracking metadata" with source='tracking' → reverted to source='enterprise'
- `MARKETPLACE_TRACKING_FIELDS` rename → kept the rename internally but logic uses `ALWAYS_REQUIRED`
- "Supreme canonical template" with placeholders for every documented field → reverted to enterprise template (8 required fields filled, optional fields commented)
- `frontmatter-spec.md` section 3 reframe → restored to "Intent Solutions Enterprise Required Fields"
- `CLAUDE.md` frontmatter section reframe → restored to enterprise required-field listing

### Net result

The validator now enforces the original IS enterprise standard exactly, with these technical corrections layered in:

| Field | Status in 3.3.0 |
|---|---|
| `name` | Required (unchanged) |
| `description` | Required (unchanged) |
| `allowed-tools` | Required (unchanged) |
| `version` | Required (unchanged) |
| `author` | Required (unchanged) |
| `license` | Required (unchanged) |
| `tags` | Required (unchanged) |
| `compatibility` | Required (replaces `compatible-with`) |
| `compatible-with` | **Deprecated alias** — still parsed, warns + suggests migration |
| `when_to_use` | Documented Anthropic optional (was wrongly flagged deprecated in earlier IS rubrics) |
| `arguments`, `paths`, `shell` | Documented Anthropic optional (newly added to schema registry) |
| `effort` valid values | `low / medium / high / xhigh / max` (added xhigh) |

---

## [3.2.0] — 2026-04-28 — Maximum-capability default + supreme canonical template (REVERTED IN 3.3.0)

### Why this release

Two related framing problems in 3.1.0:

1. **Tier model was apologetic.** `version`, `author`, `tags` were classified as `source: 'intent-solutions'` and described as "marketplace polish" — as if tracking metadata were a quirky IS extension instead of how every package manager (npm, PyPI, Cargo, Homebrew) operates. Anthropic's own reference repo *chooses* not to use them, but they're tolerated by the spec and they're how serious skill marketplaces function.
2. **Templates and docs led with the minimal form.** Following Anthropic's reference-repo style of `name + description + license`, the IS template encouraged minimalism. That contradicts what a marketplace operator actually needs — full tracking metadata for every shipped skill.

### Changed

- **Validator design principle now stated explicitly**: "maximum capability by default; users customize down." Every documented Anthropic field is first-class, every AgentSkills.io optional is first-class, every tracking field is first-class. Validator only enforces (a) required-field presence (b) type/value validity (c) security constraints.
- **`version`, `author`, `tags` reclassified** from `source: 'intent-solutions'` → `source: 'tracking'`. Description updated in `SKILL_FIELDS` schema registry to reflect that top-level tracking metadata is the dominant convention across language-ecosystem package managers and that Anthropic doesn't reject it.
- **`MARKETPLACE_RECOMMENDED` renamed to `MARKETPLACE_TRACKING_FIELDS`** (old name kept as alias). The new name reflects what the fields actually are: tracking + governance metadata, not aesthetic "polish."
- **Per-field warning messages** at marketplace tier now surface the *reason* each field matters: `author` → maintainership/contact, `version` → downstream pinning, `license` → legal clarity, `allowed-tools` → security, `tags` → discovery, `compatibility` → runtime requirements. Engineers see the actual cost of omitting each field.
- **`templates/skill-template.md` rewritten as the supreme canonical form** — every documented field present and configured with placeholders. The minimal form (name + description only) is documented as a fallback, not the default.
- **`frontmatter-spec.md` section 5 ("Recommended Field Order") rebuilt as the supreme form** with explicit "customize down, never up" guidance.

### Added

- "Minimal form (only when you genuinely have nothing to add)" subsection clarifying that the Anthropic reference-repo style is *valid* but not the IS standard.

### Backward compatibility

Non-breaking. Skills that pass at 3.1.0 still pass at 3.2.0 with identical errors/warnings. The reframe is purely educational — same fields, same validation rules, clearer naming and richer warning messages.

### What this enables

A user shipping a skill to the IS marketplace gets a frontmatter that:

- Tracks who maintains it (`author`)
- Tracks what version they're on (`version`)
- Documents what license applies (`license`)
- Pre-approves the right tools (`allowed-tools`, scoped)
- Surfaces in marketplace discovery (`tags`)
- States runtime requirements (`compatibility`)
- Documents triggers explicitly (`when_to_use` + `description`)
- Constrains auto-activation when needed (`disable-model-invocation`, `user-invocable`)
- Restricts file-context activation (`paths`)

That's the full first-class set. Customize down by deleting what doesn't apply.

---

## [3.1.0] — 2026-04-28 — Correction: deeper read of Claude Code skills doc

### Why this release

Schema 3.0.0 (earlier the same day) was published before fully reading the Claude Code skills frontmatter reference at [`code.claude.com/docs/en/skills#frontmatter-reference`](https://code.claude.com/docs/en/skills#frontmatter-reference). Several documented optional fields were missing or misclassified:

| Issue | Pre-3.1.0 | Anthropic doc says | Fix |
|---|---|---|---|
| `when_to_use` | Marked DEPRECATED | Documented optional: *"Additional context for when Claude should invoke the skill, such as trigger phrases or example requests. Appended to `description` in the skill listing and counts toward the 1,536-character cap."* | Restored to `SKILL_FIELDS` as documented optional. Removed from `DEPRECATED_FIELDS`. |
| `arguments` | Missing | Documented: *"Named positional arguments for `$name` substitution in the skill content. Accepts a space-separated string or a YAML list."* | Added to `SKILL_FIELDS`. Validated as `string\|array`. |
| `paths` | Missing | Documented: *"Glob patterns that limit when this skill is activated. Accepts a comma-separated string or a YAML list."* | Added to `SKILL_FIELDS`. Validated as `string\|array`. |
| `shell` | Missing | Documented: *"Shell to use for `` !`command` `` and ` ```! ` blocks. Accepts `bash` (default) or `powershell`."* | Added to `SKILL_FIELDS` with valid values `[bash, powershell]`. |
| `effort` valid values | `[low, medium, high, max]` | `low`, `medium`, `high`, **`xhigh`**, `max` | Added `xhigh` to valid values. |

### Added

- **`when_to_use` reclassified as documented optional** per `code.claude.com/docs/en/skills#frontmatter-reference`. Validator no longer warns about it being deprecated. Validator now warns when combined `description` + `when_to_use` length exceeds Anthropic's documented 1,536-character cap on the skill listing entry.
- **`arguments` field** added to schema registry. Type: `string|array`. Accepts space-separated string (e.g. `arguments: issue branch`) or YAML list. Names map to `$name` substitution positions.
- **`paths` field** added to schema registry. Type: `string|array`. Glob patterns limiting auto-activation per file context.
- **`shell` field** added to schema registry. Valid values: `bash` (default), `powershell`. PowerShell on Windows requires `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`.
- **`effort: xhigh`** added to valid values for the `effort` field. Higher than `high`, distinct from `max`.
- **Cross-surface alignment note**: `code.claude.com/docs/en/skills` documents *"All fields are optional. Only `description` is recommended."* — this is more permissive than `platform.claude.com` (API surface) which requires `name` and `description`. The IS validator follows the API + AgentSkills.io stance (name + description required) for marketplace consistency, with `name` accepting the directory-name fallback per Claude Code semantics.

### Changed

- `DEPRECATED_FIELDS` no longer contains `when_to_use`. Earlier IS rubrics treated `when_to_use` as deprecated; that was wrong.
- `SCHEMA_VERSION` constant: `'3.0.0'` → `'3.1.0'`.
- Documentation across `frontmatter-spec.md`, `validation-rules.md`, master spec, and `CLAUDE.md` updated to reflect the corrected field reference.

### Backward compatibility

This release is non-breaking. Files that previously triggered a `when_to_use` deprecation warning now validate cleanly. The four newly-documented optional fields (`arguments`, `paths`, `shell`, plus the corrected `when_to_use`) are accepted when present and silent otherwise.

---

## [3.0.0] — 2026-04-28 — Realigned to Anthropic published sources

### Why this release

Pre-v3 schema required eight fields at the (then-named) "enterprise" tier:
`name`, `description`, `allowed-tools`, `version`, `author`, `license`,
`compatible-with`, `tags`. Six of those eight are not actually required by any
published Anthropic source. As a Claude Enterprise partner positioning Intent
Solutions as a leader in the plugin/skill ecosystem, every public claim about
the SKILL.md spec must be defensible against Anthropic's published spec — which
this schema previously was not.

### Verified across seven authoritative sources (2026-04-28)

| Source | URL | Required fields |
|---|---|---|
| Anthropic platform overview | `platform.claude.com/docs/en/agents-and-tools/agent-skills/overview` | `name`, `description` only |
| Anthropic best practices | `platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices` | `name`, `description` only |
| Claude Code skills doc | `code.claude.com/docs/en/skills` | None required (`description` recommended) |
| Anthropic plugins reference | `code.claude.com/docs/en/plugins-reference` | No SKILL.md fields beyond skills doc |
| Anthropic engineering blog | `anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills` | `name`, `description` only |
| AgentSkills.io open standard | `agentskills.io/specification` | `name`, `description` only; `license`, `compatibility`, `metadata`, `allowed-tools` listed as optional |
| anthropics/skills reference impl | `github.com/anthropics/skills` | `name`, `description` only |

### Changed

- **`ALWAYS_REQUIRED` reduced** from `{name, description, allowed-tools, version, author, license, compatible-with, tags}` → `{name, description}`. Sources: all seven above.
- **Tier renamed**: "Enterprise" → "Marketplace". The `--enterprise` CLI flag and `TIER_ENTERPRISE` constant remain as backward-compat aliases for one minor version. Renaming was needed because the previous label conflated this tier with Anthropic's actual Enterprise plan tier — they are unrelated. The new name reflects the tier's actual purpose: marketplace polish recommendations layered on top of Anthropic's spec.
- **Marketplace polish fields downgraded from ERROR → WARNING**: `allowed-tools`, `version`, `author`, `license`, `tags`, `compatibility` are all optional per Anthropic / AgentSkills.io spec. Validator now warns when any are missing at marketplace tier; no errors. Higher rubric scores still reward inclusion.

### Added

- **`compatibility` accepted as a documented optional field** per `agentskills.io/specification`. Free-text string, max 500 chars. Replaces the deprecated `compatible-with` CSV platform list. Pre-v3 schema rejected this field as INVALID — that was wrong. Examples per the AgentSkills.io spec:

  ```yaml
  compatibility: "Designed for Claude Code"
  compatibility: "Requires Python 3.10+ with uv installed"
  compatibility: "Requires git, docker, and jq on PATH"
  compatibility: "Designed for Claude Code, also compatible with Codex and OpenClaw"
  compatibility: "Node.js >= 18, npm >= 9"
  ```

- **`metadata` accepted as a documented optional field** per `agentskills.io/specification`. Arbitrary key-value mapping. Engineers may nest `version`, `author`, `tags`, etc. under `metadata.*` per the open standard, or keep them top-level (Intent Solutions extension).
- **`compatible-with` reclassified from REQUIRED → DEPRECATED**. Validator continues to parse this field for backward compatibility (3,385 existing public-repo SKILL.md files keep passing immediately) and emits a deprecation warning with a per-file migration suggestion that quotes the user's actual value. Migration tooling: `scripts/batch-remediate.py --migrate-compatible-with`.
- **`scripts/batch-remediate.py`** — new bulk-fix script. The `--migrate-compatible-with` flag implements the translation table:

  | Input | Output |
  |---|---|
  | `compatible-with: claude-code` | `compatibility: Designed for Claude Code` |
  | `compatible-with: claude-code, codex, openclaw` | `compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw` |
  | `compatible-with: ["claude-code"]` | `compatibility: Designed for Claude Code` |
  | (empty `compatible-with`) | field removed |

  Idempotent: running twice on the same file is safe.

- **`SCHEMA_VERSION` constant** in `validate-skills-schema.py`, set to `'3.0.0'`. Validator banner now reads `validator v7.0 / schema 3.0.0`.

### Removed

- **`compatibility` and `metadata` from `INVALID_SKILL_FIELDS`**. Pre-v3 schema rejected both as not-Anthropic. Both are documented optional fields in `agentskills.io/specification`. Removing them as INVALID restores spec alignment. The pre-v3 rejection effectively forced engineers to choose between Intent Solutions' rubric and the open standard — that is no longer the case.
- **`VALID_PLATFORMS` allow-list semantics for `compatible-with`**. The pre-v3 validator restricted `compatible-with` values to a closed set: `{claude-code, codex, openclaw, aider, continue, cursor, windsurf}`. That allow-list was an Intent Solutions invention not present in any published spec. The deprecated alias still parses any value the engineer writes; the warning suggests a `compatibility:` migration target derived from the actual value.

### Migration impact

| Surface | Impact |
|---|---|
| **3,385 public-repo SKILL.md files** under `plugins/` | Zero errors (warnings about `compatible-with` deprecation are expected and OK). Bulk migration tracked in a separate follow-up issue. Not done in this release. |
| **45 personal skills under `~/.claude/skills/`** | Migrated 2026-04-28 alongside this release. ~20 had `compatible-with`; rest unaffected. |
| **CI configs that pass `--enterprise`** | Continue to work. Validator emits a deprecation warning suggesting the rename to `--marketplace`. Removal targeted for the next minor version. |
| **Skills authored after this release** | Should use `compatibility` (free-text per AgentSkills.io). The `compatible-with` field will be removed entirely in schema v4.0.0. |

### Backward compatibility guarantee

This release is **non-breaking** for existing SKILL.md files. Every file that
passed at the previous "enterprise" tier continues to pass at the new
"marketplace" tier. The strict-mode CI gate on `validate-plugins.yml` does not
need changes. Deprecation warnings are emitted but do not fail CI by default
(set `--fail-on-warn` if stricter behavior is desired).

### Master spec doc updates (`000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md`)

- Bumped doc version `2.0.0 → 3.0.0`
- Required Fields section: `name` + `description` only
- New "Marketplace Polish Recommendations" section
- Sources block: all seven verified URLs
- `compatible-with` references replaced with `compatibility` examples
- Inline `compatibility` usage examples added per AgentSkills.io spec

### Tier model

| Tier | Hard requirements | Warnings | Audience |
|---|---|---|---|
| **Standard** (default) | `name`, `description` | none | All skills, all authors. Mirrors Anthropic spec verbatim. |
| **Marketplace** (`--marketplace`) | `name`, `description` | Missing polish fields (`allowed-tools`, `version`, `author`, `license`, `tags`, `compatibility`) | IS marketplace submissions. Adds 100-point rubric. |
| **Deep** (`--deep`) | (delegates to standard or marketplace tier) | (deep-eval engine specific) | Quality analysis, Elo ranking, optional LLM judge. |

### Authors

Jeremy Longshore <jeremy@intentsolutions.io>
