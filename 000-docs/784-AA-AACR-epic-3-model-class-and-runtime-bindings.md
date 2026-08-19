<!-- doc-class: record -->

# Epic 3 Adapter Toolchain: Compatibility Projection, Model-Class Tiers, Runtime Bindings — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 3 beads 3.4, 3.8, and 3.9 (§ 5.2–5.4, § 6)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-t9s9.7` (coupled slice — the three beads are the generated-adapter
  toolchain: the compatibility projection plus the claude-code adapter's two resolution seams)
- **Implementation PR:** [#1271](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1271) (shared with E3.6 — the fork deletion and the toolchain landed together after the root-cause loop below)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E3.4 + E3.8 + E3.9 controls implemented; merge fields are recorded in Beads/Dolt after review

## E3.4 — the compatibility projection

`scripts/adapters/generate-compatibility.mjs` is the ONLY sanctioned writer of the frontmatter
`compatibility` string for card-carrying skills: a deterministic projection of `adapters[]` +
`requires.services[]` + `unsupported[]` (schema fields shipped in E3.2), beginning with the
`Declared adapters:` marker so E3.11's ratchet can distinguish generated projections from legacy
prose. `compatibility` stays one of the IS 8 REQUIRED frontmatter fields — only its provenance
changes. 5/5 tests including the no-adapters red run and the fail-closed degradation projection.

## Outcome

`scripts/adapters/claude-code-adapter.mjs` is the claude-code harness's resolution seam, and it
**fails closed** on both axes (§ 5.4 rule 4):

1. **E3.8 — model classes.** Canonical carries `model_class ∈ {reasoning-high, balanced, fast}`
   (schema-enforced since E3.2, vendor literals rejected with red runs). The adapter resolves
   tiers to the harness's own model aliases — `reasoning-high → opus`, `balanced → sonnet`
   (the corpus default), `fast → haiku` — and an unresolvable tier **throws**: silent
   substitution is a schema violation, proven by a red run covering vendor literals, bare
   aliases, unknown tiers, and undefined.
2. **E3.9 — runtime bindings.** Canonical bodies write the portable `${SKILL_DIR}` /
   `${PLUGIN_ROOT}`; the adapter emits `${CLAUDE_SKILL_DIR}` / `${CLAUDE_PLUGIN_ROOT}`. Three
   refusals are pinned by red runs: harness-branded variables already present in canonical
   input (double-branding), unknown portable directory variables (no silent pass-through), and
   — passing untouched — ordinary env-var interpolations, which are not runtime bindings.

**Validator retarget (the E3.9 acceptance's second half).** `${SKILL_DIR}` and
`${PLUGIN_ROOT}` join `YAML_VALUE_ALLOWED_VARS` in `validate-skills-schema.py` as the
harness-free spellings of the already-allowed branded forms — the anti-absolute-path posture is
unchanged. This is an observable validator change, so the full four-surface lockstep ran:
`SCHEMA_VERSION` 4.0.0 → **4.0.1**, a SCHEMA_CHANGELOG entry, the 6767-b banner, and CLAUDE.md's
schema reference — with `validate:doc-fact-assertions` (E2.8) green across all four, which is
precisely the drift class that assertion exists to police. No required field, tier semantics, or
error class changed.

## Verification

- `node --test scripts/adapters/claude-code-adapter.test.mjs` — 6/6 (three resolutions, three
  red-run classes).
- `pnpm run validate:doc-fact-assertions` — OK at 4.0.1 across all four claim surfaces.
- `python3 -m py_compile scripts/validate-skills-schema.py` — clean; hosted CI (including the
  full validator suite) final.
- Wired as `validate:claude-code-adapter` in `doc-governance`.

## Scope discipline

No corpus rewrite: the seams land before any consumer. `ALWAYS_REQUIRED`, tier model, and
error-vs-warning semantics untouched (the 4.0.1 change is an allowlist addition — a
spec-compliance-level change under the SCHEMA_CHANGELOG NON-NEGOTIABLES' autonomy rule,
version-bumped and disclosed as required).

## Follow-up

- E3.10's vendor-literal gate refuses `${CLAUDE_*}` in canonical-layer files — the inverse of
  this adapter's emission, sharing the same variable inventory.
- E3.4's compatibility generator + these seams together constitute the generated-adapter
  toolchain E3.11's backfill and any future harness registration build on.
