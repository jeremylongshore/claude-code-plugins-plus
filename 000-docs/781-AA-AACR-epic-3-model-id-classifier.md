<!-- doc-class: record -->

# Epic 3 Model-Identifier Classifier — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 3 bead 3.7
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-t9s9.4`
- **Implementation PR:** [#1269](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1269)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E3.7 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

The three-way model-identifier classifier is a promoted, single-owner library with a committed
exclusion list, landing BEFORE any bulk rewrite exactly as the blueprint's execution prompt
requires:

1. **`scripts/lib/model-id-classifier.mjs`** — THE classifier. Roles are disjoint by
   construction: `bead-id` (protected), `functional` (E3.8's work list), `prose` (preserved).
   Protection order is load-bearing: exclusion-list and bead-shape checks run before any
   model-family logic, so protection wins every tie — a bead handle classifies `bead-id` even
   on a `model:` or `--model` line, regression-tested.
2. **`schemas/canonical/v0/model-id-exclusions.json`** — 393 live bead-handle prefixes pinned
   by exact string on top of the shape rule, regenerable from `.beads/issues.jsonl` (a test
   asserts the census stays complete; the list is never hand-pruned).
3. **`scripts/classify-model-ids.mjs`** — the CLI emitting the sets: at filing, tree-wide
   **bead-id 3,259 · functional 940 · prose 883**; `--functional` prints E3.8's exact
   file:line work list.
4. **One owner retroactively enforced:** E3.1's measurement script now imports the shared
   library — its local classifier copy and second token scan are gone.

## Classifier refinement disclosed (baseline 778 regenerated)

A trailing-hyphen lookahead stops hyphen-continued tokens (`claude-fable-5`,
`claude-code-plugins`) from leaking prefixes into the protected scan as phantom tokens. The 778
baseline was regenerated through the promoted classifier with a dated correction block:
first-party functional 398 → 404, prose 485 → 493, protected 7,656 → 2,923 (phantoms removed).
The protected class deliberately includes non-model `claude-*` tokens such as the bare harness
name `claude-code` — model-id migration must not touch harness names either; protection wins.

## Verification

- `node --test scripts/classify-model-ids.test.mjs scripts/measure-canonical-surface.test.mjs` —
  7/7: exclusion-list census completeness and shape-disjointness over all 393 handles;
  never-rewritable-on-functional-lines; three-set disjointness on a mixed line; regenerability
  against the live beads export.
- `node scripts/classify-model-ids.mjs` — summary reproduced at filing; hosted CI final.

## Scope discipline

No corpus rewrite of any kind — the classifier and its protections land first, the rewriter
(E3.8) consumes them later. No mirror, catalog, or frontmatter change.

## Follow-up

- E3.8 replaces the functional set in the canonical layer with `model_class` tiers, fail-closed,
  consuming `--functional`'s work list.
- E3.10's vendor-literal gate imports the same library — never a second implementation.
