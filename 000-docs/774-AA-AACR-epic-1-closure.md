<!-- doc-class: record -->

# Epic 1 Closure — Repository Cleanup and Measurement Baseline — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 1 (§ 13), 15 blueprint beads E1.0–E1.14
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Epic bead:** `claude-hz8f` (16 children, all closed)
- **Status:** Closure record; the parent bead closes after this filing merges, per the program's filing-then-close transaction

## Verdict

Epic 1 is complete. All 15 blueprint beads are implemented, merged, independently reviewed, and
closed with PR + merge-SHA evidence, and the measurement harness (E1.0) reproduces every exit-rule
row from the committed tree. A pre-closure record audit by the `beads-warden` internal agent
(itself an Epic-adjacent deliverable, PR #1185) found the evidence trail "unusually strong" and
raised exactly one blocker — E1.14 then still in flight — which has since merged and closed, plus
one record clarification, which has been filed as a note on the E1.6 bead.

## Bead-to-evidence map

| Blueprint                      | Child            | Evidence (implementation → AAR)                    |
| ------------------------------ | ---------------- | -------------------------------------------------- |
| E1.0 measurement harness       | `claude-hz8f.4`  | PR #1208 → AAR 743                                 |
| E1.1 catalog shadow            | `claude-hz8f.1`  | PR #1196 → AAR 736                                 |
| E1.2 name uniqueness (471→467) | `claude-hz8f.12` | PR #1235 → AAR 757                                 |
| E1.3 magic-byte sniff          | `claude-hz8f.2`  | PR #1216 → AAR 748                                 |
| E1.4 counterfeit assets        | `claude-hz8f.7`  | PR #1216 (coupled) → AAR 748                       |
| E1.5 corpus resolver           | `claude-hz8f.5`  | PR #1210 → AAR 744                                 |
| E1.6 count cohorts             | `claude-hz8f.13` | PRs #1241, #1243–#1251 → AARs 760–768, closure 769 |
| E1.7 build-data disposition    | `claude-hz8f.9`  | PR #1220 → AAR 750                                 |
| E1.8 projection drift gates    | `claude-hz8f.11` | PRs #1227/#1229/#1237/#1239 → AARs 753/756/758/759 |
| E1.9 single README writer      | `claude-hz8f.6`  | PR #1212 → AAR 745                                 |
| E1.10 stats freshness bound    | `claude-hz8f.14` | PR #1254 → AAR 771                                 |
| E1.11 malformed allowlists     | `claude-hz8f.3`  | PR #1206 → AAR 741                                 |
| E1.12 sources-lock parity      | `claude-hz8f.15` | PR #1255 → AAR 772                                 |
| E1.13 dead-domain retirement   | `claude-hz8f.8`  | PR #1218 → AAR 749                                 |
| E1.14 MCP credential → SOPS    | `claude-hz8f.16` | PR #1256 (+ security follow-up #1257) → AAR 773    |

One extra child, `claude-hz8f.10` (release-note coverage gate, PR #1162 → AAR 752), is
program-maintenance prerequisite work and self-discloses as not one of the 15.

## Blueprint exit rule

§ 13 requires rows 1, 2, 3, 4, 11, 12, 22, 24, 25, 26, 27 re-derived by the harness, none by
hand. Scorecard 742 at this filing: row 2 = 468/468 unique catalog names; row 3 = 0 stale
shadows; row 11 = 36 candidates / 0 mismatches; row 12 = 0 missed promotions; row 22 = 0 tracked
generated outputs without a content-drift gate; row 24 = 5 named cohorts; row 25 = exactly one
README metrics writer; row 26 = 3/3 stats artifacts bounded (`without_valid_bound: 0`); row 27 =
64 == 64 source-lock parity. All satisfied; rows 1/4 informational as designed.

## Owner reshapings recorded against the blueprint

1. **E1.12** — the blueprint said remove the orphan `uizze` source; the owner accepted the mirror
   (PR #1242) on 2026-08-18, so the slice narrowed to lock-baseline + bidirectional parity gate.
2. **E1.14** — owner-gated per § 18.7; the SOPS move was authorized 2026-08-18. The encrypted
   file is deliberately untracked (public repo). Rotation was asked exactly once; the answer
   remains pending and is NOT assumed — the pending ask transfers to Epic 4 bead 4.14, which
   owns the rotation record.

## Residual risks and transfers

- Whop key rotation: pending owner answer (→ E4.14).
- Daily stats automation: `BOT_PR_TOKEN` provisioned during E1.10; the token still needs the
  **Workflows: read/write** permission (owner console action) before the daily PR self-triggers
  required checks whenever workflow files changed between runs.
- Agent-frontmatter debt, mirror-owned allowlist instances, and vendor-literal classes remain
  with their owning epics (E4/E6, E3.3/E4.2) per AAR 741's deferral.

## Verification of this record

Every PR number and SHA above is resolvable in the repository; the warden audit cross-checked
each close reason against `.beads/issues.jsonl` and the scorecard's live values. This AAR was
gated through doc-governance (doc-class, citation, index, scorecard) like every record before it.
