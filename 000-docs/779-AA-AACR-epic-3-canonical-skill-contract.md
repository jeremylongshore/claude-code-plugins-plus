<!-- doc-class: record -->

# Epic 3 Canonical Skill Contract — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 3 bead 3.2 (§ 5)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-t9s9.2`
- **Implementation PR:** [#1266](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1266)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E3.2 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

The canonical harness-free skill contract exists as a versioned JSON Schema draft:
`schemas/canonical/v0/skill-contract.schema.json` (Ajv 2020 strict-compiling,
`additionalProperties: false` at every level) with its prose companion
`schemas/canonical/v0/README.md`. It validates `skill-card.yaml` — home **B** of the § 5.1
four-home split — and encodes the § 5.2 shape exactly: abstract capabilities (bare or scoped,
never harness tool spellings), fail-closed constraints, declared side effects,
`requires.services`, `model_class` tiers (`reasoning-high | balanced | fast`, never a vendor
literal), lifecycle/supersession, SPDX-only provenance with resolved-40-hex mirror pins,
`adapters[]` as a registry enum (only `claude-code` registered at v0), `unsupported[]` with
`fail-closed` default degradation, and `compatibility` rejected as an unknown key because it is
a generated projection, never hand-authored.

**`ALWAYS_REQUIRED` is untouched.** Home A (frontmatter) keeps the IS 8 exactly as the
SCHEMA_CHANGELOG NON-NEGOTIABLES govern them; this contract is additive by construction and the
prose companion states the five-one rule.

## Upstream posture

`Status: DRAFT` + `UPSTREAM-PENDING` in the schema's `$comment` and the companion: this
repository must never become its own schema authority. The kernel proposal to
`@intentsolutions/core` (schemas `skill-contract`, `capability`, `eval-spec`) is E3.13's
deliverable, gated on the E3.3/E3.4 drafts existing; the issue number is recorded there when
filed.

## Verification

- `pnpm run validate:canonical-schema` — 8/8 tests: the blueprint § 5.2 example validates; a
  minimal seven-required-field contract validates; red runs for the five failure classes —
  unknown top-level key (closed schema; includes hand-authored `compatibility`), vendor-literal
  model class (`claude-sonnet-4`, `claude-fable-5`, `gpt-5`, `sonnet` all rejected),
  unregistered adapter (`codex`, `openclaw`, empty list), branch-name mirror pin (`main`
  rejected, 40-hex accepted), and harness tool spellings as capabilities (`Bash(jq:*)`,
  `mcp__plane__query`, `Read` all rejected).
- Wired as a `doc-governance` step (blocks via `ci-required`); hosted CI is the final gate.

## Scope discipline

No SKILL.md, frontmatter rule, validator behavior, catalog entry, or mirror file changed. The
schema is a new artifact with tests; nothing consumes it yet — E3.4 extends it against the
corpus, E3.5/E3.10 build the gates, E3.11 backfills declarations.

## Follow-up

- E3.3: `capability-map.json` — the committed vocabulary covering every tool token in the
  corpus under one parser (next activation; owns Epic 4's gate input).
- E3.13: the kernel proposal naming this directory as the draft.
