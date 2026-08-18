<!-- doc-class: record -->

# Epic 2 Documented-Fact Assertions — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 2 beads 2.7 and 2.8
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-hedb.9` (coupled slice — both beads are thin assertions over the facts E2.6 corrected and share one checker)
- **Implementation PR:** [#1260](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1260)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E2.7 + E2.8 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

The two documented facts with the worst rot history are now mechanically pinned to the code by
`scripts/check-doc-fact-assertions.mjs`, wired as `validate:doc-fact-assertions` inside the
`doc-governance` job (blocking via `ci-required`):

1. **E2.7 — the ci-required contract.** CLAUDE.md's enumerated gate-job list (the
   "`` `needs:` `` all N gate jobs (…)" sentence) must equal the actual `needs:` block of the
   `ci-required` job in `validate-plugins.yml` — same count, same names, both directions. In
   addition, CLAUDE.md and GOVERNANCE.md must each name all three required branch-protection
   contexts (`ci-required`, `gitleaks`, `skill-conform`) — the regression guard for the
   two-contexts understatement E2.6 found in GOVERNANCE.md, and for the 19-vs-21 job count the
   reviewer guide carried.
2. **E2.8 — the schema version.** The validator's `SCHEMA_VERSION` literal is the authority;
   CLAUDE.md's "(schema X.Y.Z" reference, 6767-b's "CURRENT SCHEMA" banner, and
   `SCHEMA_CHANGELOG.md`'s newest entry must all equal it. A missing claim surface is reported
   as a moved anchor, never silently passed.

Historical version strings inside dated changelog entries and record-class docs are deliberately
out of scope — assertions cover live claim surfaces only, matching E2.6's correction discipline.

## Verification

- `node --test scripts/check-doc-fact-assertions.test.mjs` — 6/6 pass (needs extraction,
  prose-anchor parse + moved-anchor failure, count/set mismatch reporting in both directions,
  required-context regression guard, schema authority + claim parsing, null-surface fail-closed).
- Live run against the post-E2.6 tree: OK (21 == 21 jobs, name sets equal, three contexts named
  in both files, three schema surfaces == 4.0.0).
- Hosted CI on the implementation PR is the final gate.

## Scope discipline

No documentation content changed in this slice — E2.6 corrected the facts; this slice only pins
them. No plugin, catalog, credential, or release surface touched.

## Follow-up

Epic 2 remaining after this slice: E2.10 (one-owner-per-fact-class authority map) and E2.13
(governed README landing contract).
