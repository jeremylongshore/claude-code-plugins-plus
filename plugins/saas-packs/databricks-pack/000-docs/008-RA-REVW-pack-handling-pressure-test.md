# Pressure Test: Pack Handling (Version Bump In Place)

**Verdict: MODIFY.** Keep the slug, but the decision is incomplete in two material ways: (a) the breaking-change communication plan is one CHANGELOG line where reality demands a deprecation lane, and (b) the 1.x skill directories need to be retained as tombstones (or explicitly redirected), not deleted from disk on upgrade. Without those two adjustments, the in-place version bump silently nukes user workflows.

## Where the decision is right

Renaming the pack (Option A) is correctly rejected. The repo CLAUDE.md "Key Identifiers — Do Not Normalize" block is explicit that `databricks-pack` is in catalog URLs, install instructions, and downstream user systems. A rename is a breaking API change that costs more than it buys. Options B/C/D are correctly rejected — the synthesis (`databricks-rebuild-synthesis.md:110`) shows 5 current skills genuinely have spirit-of survivors in the rebuild; treating the rebuild as a fresh pack pretends those threads don't exist.

## Where the decision breaks

**1. Backwards-compat reality is worse than "major version = breaking, done."**

Claude Code's marketplace honors auto-update (Claude Code CHANGELOG 2.0.72: "Added auto-update toggle for plugin marketplaces"). Plugin uninstall only started actually removing files in 2.0.30 ("Fixed plugin uninstall not removing plugins"). The interaction: a user on 1.x with `databricks-cost-tuning` referenced in CLAUDE.md or a saved workflow will, on next marketplace sync, find that skill directory gone — no warning, no migration prompt. Claude Code does not surface "this skill no longer exists" to the user at upgrade time; it surfaces silently as "skill not found" the next time it's invoked. This is the same failure class as a library deleting public symbols on a minor bump.

**2. The slug-stability argument hides a content-substitution problem.**

Per the synthesis line 112, 15 of 24 skills are deleted outright and 5 are absorbed. That is 83% of the surface area changing. The user-facing question is not "did the slug change" — it's "does `databricks-pack` still mean what it meant last week." It does not. The catalog description in `marketplace.extended.json` ("24 skills covering Delta Lake, MLflow, notebooks...") is not just stale — it advertises a product that won't exist. MLflow and notebooks are not in the proposed 8-skill set at all. A semver-major bump is technically correct but ethically thin given the iPhoto→Photos analog: Apple renamed because the substitution was honest. Here, the slug carries forward branding that the contents no longer earn.

**3. CHANGELOG-as-communication is insufficient.**

For 15 deletions with no in-product warning surface, the honest minimum is a deprecation release first: ship `databricks-pack@1.1.0` with the existing 24 skills plus deprecation banners in the to-be-cut SKILL.md descriptions ("This skill will be removed in 2.0. See `databricks-cost-leak-hunter`."), then ship 2.0.0 a defined window later (2-4 weeks). This gives auto-updaters a chance to see the warning before the files vanish. One-line CHANGELOG + slug-stable major bump is the npm-package answer; this is end-user-facing content, not a library API.

**4. Tombstone files are missing from the plan.**

The 15 deleted skill directories should ship in 2.0.0 as stubs containing only a `SKILL.md` that says "moved to X." Cost: ~15 tiny markdown files. Benefit: every `databricks-cost-tuning` reference in a user's saved CLAUDE.md, prompt, or workflow gets a redirect instead of a 404. This is the same pattern as HTTP 301s for the slug rename problem, applied internally.

## Anthropic precedent

No first-party Anthropic plugin in the local mirror (`anthropic/claude-code/plugins/*`) has shipped a 2.0.0 yet — all sit at 1.0.0. There is no observable precedent for how Anthropic handles major restructures of a shipped plugin. Absence of precedent means caution, not freedom.

## Required modifications

1. Ship `1.1.0` deprecation release first with banners on the 15 doomed skills. Wait 2-4 weeks.
2. In `2.0.0`, retain the 15 deleted skill dirs as redirect-stub SKILL.md files. Delete them in `2.1.0` once telemetry (or absence of complaints) confirms migration.
3. Rewrite the catalog description and keywords to match the new shape before the 2.0.0 tag — don't carry MLflow/notebooks claims forward.
4. CHANGELOG + dedicated blog post + Plane CONTENT issue tagged `databricks-rebuild` announcing the change with the migration table.

File: `plugins/saas-packs/databricks-pack/000-docs/research/pressure-test-pack-handling.md`
