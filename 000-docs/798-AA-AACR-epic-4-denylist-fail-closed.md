<!-- doc-class: record -->

# Epic 4 Fail-Closed Denylist Degradation — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 bead 4.13
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-or1m.12`
- **Implementation PR:** [#1286](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1286)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E4.13 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

`disallowed-tools` is enforced by the Claude Code **runtime** only — the repo validates
syntax, and on any other harness the denylist silently does not exist (the register's § 5
finding). `scripts/check-denylist-degradation.mjs` (blocking in `validate` via `ci-required`)
makes that silent drop **unclaimable**:

1. A first-party denylist-bearing skill may not name any non-claude-code harness in its
   `compatibility` prose — a portability claim over a denylist-dependent posture IS the
   silent-drop bug. The harness lexicon is imported from the E3.11 ratchet (one owner).
2. A skill-card `adapters[]` entry beyond claude-code must degrade the denylist
   `fail-closed` (or omit `degradation` — the canonical schema's documented default);
   `skip` / `prompt-in-band` fail for a safety posture even though the schema allows them
   for ordinary capabilities.

Rule 2 is structural today (zero skill-cards exist; zero foreign claims exist thanks to the
E3.11 withdrawal) and arms automatically with card adoption — the same landing pattern as the
adapter-thinness gate.

## Measurement

52 first-party denylist-bearing skills (matching the register's § 5 count), zero violations;
gate tests 4/4 including per-harness catch coverage.

## Register maintenance

790 § 5's `E4.13 target` row flipped to closed in this PR.
