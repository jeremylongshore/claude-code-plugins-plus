<!-- doc-class: record -->

# Epic 3 Kobiton Codex-Fork Deletion — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 3 bead 3.6 (§ 6)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-t9s9.6`
- **Implementation PR:** [#1271](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1271)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E3.6 controls implemented; merge fields are recorded in Beads/Dolt after review

## Disposition reshaping, disclosed

The blueprint row says "convert the Codex fork into a real thin adapter." Section 6's own rules
make a hand conversion impossible to do honestly: **an adapter is GENERATED — hand-authored
adapter content is prohibited** — and the adapter registry holds only `claude-code`. Producing a
hand-written `.codex` artifact "with only the six permitted sections" would recreate the exact
anti-pattern § 6 opens with, and listing a harness with no registered generated adapter violates
the contract schema (E3.2). The § 5.4 rule-2 honest claim is `adapters: [claude-code]` until a
generated Codex adapter and registry entry exist. **The fork is therefore DELETED, not
blessed** — 27 files, all 27 verified byte-identical to canonical at deletion.

## Outcome

- `plugins/testing/kobiton-automate/.codex/` removed (27 files — three `SKILL.md` copies plus
  their trees; the plugin's five canonical skills under `skills/` are untouched).
- The E3.5 waiver is deleted in this same PR — its named removal path
  (`removed_by: 727:epic-3.6`) executed exactly as recorded. The waiver list is now empty, and
  the live-file test asserts shape over whatever waivers exist rather than requiring one.
- The thinness gate now reports `0 adapter file(s); 0 under dated waiver` — the corpus contains
  no adapter subtrees at all, and any future one must satisfy the gate from birth.
- **Freshie double-grading ends at the next inventory run**: the 5 `.codex` compliance rows
  (10 rows for a 5-skill plugin — § 6's measured anti-pattern) lose their source files;
  `grades.csv` is inventory-run-generated and is not hand-edited here. Verified pre-deletion:
  the `.codex` copies were absent from the curated mirror, its manifest, and `skills-index.json`
  (not marketplace-visible), so no build projection changes in this PR beyond tracked-file
  counts.

## Out of scope, recorded

The plugin README's multi-harness prose (Copilot/Gemini/Codex/Cursor install sections) describes
**Kobiton's own distribution channels** (`codex plugin marketplace add kobiton/automate` — their
marketplace, not this repository's portability claim). It stays: E3.11's ratchet owns
frontmatter `compatibility` claims, and editing a sponsor's product documentation is not this
bead's call.

## Verification

- `pnpm run validate:adapter-thinness` — tests 6/6 (updated live-waiver test allows the
  legitimately empty list, still asserting date + removal owner on any entry); live run
  `OK (0 adapter file(s); 0 under dated waiver)`.
- 27 deletions, zero canonical-file diffs; scorecard and docs index regenerated; hosted CI
  final.

## Follow-up

- A real Codex adapter, if ever wanted, arrives as: registry entry + generator in
  `scripts/adapters/` + schema enum extension — the E3.4/E3.11 lineage — never as a directory
  of copies.
