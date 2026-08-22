<!-- doc-class: record -->

# Epic 2 Closure — Documentation Authority and Source-of-Truth Consolidation — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 2 (§ 13), 13 blueprint beads E2.1–E2.13
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Epic bead:** `claude-hedb` (11 children, all closed)
- **Status:** Closure record; the parent bead closes after this filing merges, per the program's filing-then-close transaction

## Verdict

Epic 2 is complete. All 13 blueprint beads are implemented, merged, and closed with PR +
merge-SHA evidence across 11 children (two coupled pairs: E2.1+E2.2 landed together at
ratification, E2.7+E2.8 shared one assertion checker). The eight-months-standing pathology the
epic existed to end — eight documents self-declaring AUTHORITATIVE with one linked, and
governing files restating facts that then rotted — is now mechanically unrepeatable: authority
requires a `STANDARDS.md` link (gate), every tracked document carries a machine-readable
lifecycle class (gate), frozen bodies are byte-pinned (gate), the index is generated (gate), the
two most rot-prone facts are asserted equal to the code (gate), and the README is a governed
landing contract with byte budgets (gates).

## Bead-to-evidence map

| Blueprint                                      | Child            | Evidence (implementation → AAR)                                                  |
| ---------------------------------------------- | ---------------- | -------------------------------------------------------------------------------- |
| E2.1 standards freeze (+E2.2 blueprint filing) | `claude-hedb.1`  | PR #1197 → AAR 737; E2.2 satisfied by ratification PR #1186 → record 730         |
| E2.3 authority-pointer gate                    | `claude-hedb.2`  | PR #1200 → AAR 738                                                               |
| E2.4 generated docs index                      | `claude-hedb.3`  | PR #1202 → AAR 739                                                               |
| E2.5 document lifecycle classes                | `claude-hedb.7`  | PR #1253 → AAR 770                                                               |
| E2.6 documented-number corrections             | `claude-hedb.8`  | PR #1259 → the appended E2.6 correction blocks in 727/694/728/729 are the record |
| E2.7 + E2.8 fact assertions (coupled)          | `claude-hedb.9`  | PR #1260 → AAR 775                                                               |
| E2.9 frozen prose-anchor gate                  | `claude-hedb.4`  | PR #1204 → AAR 740                                                               |
| E2.10 authority-map pointers                   | `claude-hedb.10` | PR #1261                                                                         |
| E2.11 cross-system authority                   | `claude-hedb.6`  | PR #1222 → AAR 751                                                               |
| E2.12 supersession record shape                | `claude-hedb.5`  | PR #1214 → AAR 747                                                               |
| E2.13 README landing contract                  | `claude-hedb.11` | PR #1262 (+ review-findings follow-up #1263) → AAR 776                           |

## Blueprint exit criteria

- **"8→3 self-declarations, all linked":** the live tree has exactly **2** effective authority
  claimants (727 and 6767-b), both `STANDARDS.md`-linked — beyond the ≤3 target — verified by
  `check-doc-authority.mjs` (12 canonical-table links, pinned by test). The criterion itself is
  reconciled in 727's E2.6 correction block, item 9 (flagged by the pre-closure warden audit:
  "2" must be read against the criterion on record, never silently).
- **Named gates all green and wired in `doc-governance`:** authority-pointer, doc-class,
  index-drift, schema-version + ci-count (`validate:doc-fact-assertions`), prose-anchor, and the
  README landing contract (R1/R2 at emit inside the single writer; R4/R5/R6/R8/R9 via
  `validate:readme-contract`) — each with fixture red runs.
- **Exit scorecard rows:** row 42 (schema) asserted equal at 4.0.0; row 44 (index) generated and
  drift-gated at parity; row 43 (self-declarations) exceeded; the ci-count prose is asserted
  equal to the workflow both directions.

## Owner reshapings and dispositions

E2.6's blueprint target text predated Epic 1's landings; its operative form (documented in 727's
appended **E2.6 documentation-number correction** block) dispositioned eight spent baselines
rather than "correcting" already-fixed rows. Ratified/locked records received dated correction
appendices, never rewritten rows. E2.13 disclosed three § 6A.2 deviations (spotlight retained,
NPM-STATS retained, badges as single-writer projections) in AAR 776.

## Residual transfers

- Epic 3 replaces E2.13's interim R5 harness-name refusal with the generated `adapters[]`
  registry cross-check and renders the adapter matrix (E3.12).
- Epic 10's `certification-report.json` flips the README CERTIFICATION block to the live split
  automatically; a malformed report fails the generator loudly (hardened in PR #1263).

## Warden audit disposition

The `beads-warden` pre-closure audit raised four blockers and three correcting notes; all are
dispositioned in the closure PR: (1) E2.13's bead closed with full PR #1262 + AAR 776 +
follow-up #1263 evidence after the audit snapshot; (2) every child state was re-read directly
via `bd show` against the live Dolt-backed store (11/11 CLOSED — no rapid-write drop); (3) the
"8→3" criterion is reconciled in 727's E2.6 correction block item 9; (4) CHANGELOG entries for
E2.6, E2.7+E2.8, E2.10, and E2.13 were added under 2026-08-18. Correcting notes were appended to
`claude-hedb.10` (deliberately thin record — pointerization-only slice), `claude-hedb.6`
(title-vs-scope precision), and the parent's progressive-activation narrative.

## Verification of this record

Every PR number and SHA is resolvable; the warden audit plus the `bd show` read-back precede the
parent close. This AAR passes the same doc-governance gates it documents.
