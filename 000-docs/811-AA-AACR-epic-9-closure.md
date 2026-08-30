<!-- doc-class: record -->

# Epic 9 Closure — Cross-Repo Evidence Boundaries — After-Action Review

- **Date:** 2026-08-30
- **Authority:** Blueprint 727, Epic 9 (§ 13), canonical beads E9.1–E9.14
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Epic bead:** `claude-abgi`
- **Closure bead:** `claude-abgi.21`
- **Machine receipt:** [Epic 9 boundary evidence](810-RA-DATA-epic-9-boundary-evidence.json)
- **Status:** Closure candidate; the parent closes only after this record merges, durable-memory
  read-back succeeds, and an independent exact-head boundary review passes

## Verdict

Epic 9's fourteen canonical implementation tasks are complete, and this closure slice repairs the
two evidence defects that previously prevented an honest parent claim: the repository handbook
still named obsolete kernel/eval pins, and scorecard rows 38 and 39 could not consume retained
registry and shadow-lane evidence. The closure candidate now binds exact package observations,
the one-version dependency result, both kernel-shadow lanes, the six DR-049 conditions, and the
test receipts to the immutable pre-closure tree recorded in document 810.

This is **not** a kernel-authority flip. `scripts/validate-skills-schema.py` remains authoritative.
Both kernel workflows remain advisory and outside the three required branch contexts. The current
strict `authoring/v2` decision metric is `existing-PASS / kernel-FAIL = 0`; moving authority to
`authoring/v1` would therefore remove enforcement without adding a caught defect. The eventual
flip target remains `authoring/v2`, and all six DR-049 conditions remain open.

## Canonical denominator and duplicate reconciliation

Blueprint 727 declares exactly fourteen Epic 9 tasks. Beads contains twenty pre-closure child
records because six later records are duplicate/superseding shells; the physical child count is
not the acceptance denominator.

| Canonical scope               | Canonical bead   | Result                                                       |
| ----------------------------- | ---------------- | ------------------------------------------------------------ |
| E9.1 authority contract       | `claude-abgi.1`  | Doc 806 names one writer per fact class                      |
| E9.2 false badge dark         | `claude-abgi.2`  | Unbacked public verification removed                         |
| E9.3 ledger schema            | `claude-abgi.3`  | Evidence class, pins, artifact identity, and split run IDs   |
| E9.4 unretained demotion      | `claude-abgi.4`  | Missing/mismatched primary artifacts demote to E0            |
| E9.5 primary retention        | `claude-abgi.5`  | Eval JSON retained outside `/dev/shm`; SHA-256 recorded      |
| E9.6 no self-approval         | `claude-abgi.6`  | E2/E3 producer=recorder and local→real-ledger writes refused |
| E9.7 run coherence consumer   | `claude-abgi.7`  | Consumes the closed E5.1 fail-closed export gate             |
| E9.8 grade freshness consumer | `claude-abgi.8`  | Consumes the closed E5.4 tracked-export gate                 |
| E9.9 hermetic-cycle consumer  | `claude-abgi.9`  | Consumes the closed E5.7 scratch-Dolt lifecycle test         |
| E9.10 lockstep pin bump       | `claude-abgi.10` | Core 0.10.0 + JRig CLI 0.2.0; one resolved kernel version    |
| E9.11 harness-pin consumer    | `claude-abgi.11` | Consumes E7.11; audit harness exactly 1.3.1                  |
| E9.12 human-routed staleness  | `claude-abgi.12` | Forced scratch-branch violation reached Slack                |
| E9.13 dual shadow lanes       | `claude-abgi.13` | `authoring/v1` and strict `v2`; decision metric headlined    |
| E9.14 host-fact deduplication | `claude-abgi.19` | Active-doc duplicate count measured 1 → 0                    |

Duplicate records `claude-abgi.14`–`.18` repeat E9.9–E9.13. `claude-abgi.20` repeats E9.14 and
also carries an erroneous supersedes edge to `.14`. They remain closed administrative artifacts
and do not add requirements, erase canonical receipts, or change the fourteen-task denominator.
Future completeness audits must count the canonical table above, not the raw child total.

## Boundary outcomes

### One writer per fact class

[Cross-Repo Authority Contract 806](806-AT-ARCH-cross-repo-authority-contract.md) remains the
binding ownership map. Intent Eval Lab / JRig produces evaluation evidence; this repository only
consumes it. Freshie/Dolt owns inventory and grade history. Intent OS owns host/deploy facts. Beads
owns task state. No implementation in Epic 9 creates a second writer.

### Evidence retention and self-approval

The recorder requires evidence class, producer and recorder identities, artifact URI and SHA-256,
spec/tool/kernel/provider/model bindings, and distinct JRig/discovery run identities. It refuses an
E2/E3 record when producer and recorder match, and refuses a local identity targeting the real
Freshie inventory. The export path demotes a missing, unreadable, or hash-mismatched primary
artifact to E0 instead of minting an unverifiable badge.

The current verification reran the complete focused boundary:

- JRig database boundary: 8/8 tests passed; 10,718 active first-party surfaces checked and 890
  provenance mirrors skipped.
- Recorder: 11/11 tests passed, including producer=recorder refusal, local→real-ledger refusal,
  malformed/stub rejection, `/dev/shm` rejection, and retained-file hash round trip.
- Freshie/Dolt: 61/61 tests passed, including internally inconsistent-run rejection, artifact
  demotion, export allowlist, single writer, and the hermetic scratch cycle.

### Lockstep pins and shadow baseline

The retained npm observation and local graph agree on these exact roots:

| Package                          | Root pin | npm latest observed | Result        |
| -------------------------------- | -------- | ------------------- | ------------- |
| `@intentsolutions/core`          | `0.10.0` | `0.10.0`            | exact/current |
| `@intentsolutions/jrig-cli`      | `0.2.0`  | `0.2.0`             | exact/current |
| `@intentsolutions/audit-harness` | `1.3.1`  | `1.3.1`             | exact/current |

JRig CLI 0.2.0's published manifest still names core 0.9.0 exactly. The root override deliberately
forces core 0.10.0 across the graph; `pnpm list --depth 20` and the lockfile show one resolved core
version. The 26-case coupling suite passed and the current observation was V=C=K=0.10.0.

The exact-head shadow run covered 3,630 skills:

| Signal                                            | Result               |
| ------------------------------------------------- | -------------------- |
| Strict `authoring/v2` existing-PASS / kernel-FAIL | 0 (0.00%)            |
| Strict `authoring/v2` existing-FAIL / kernel-PASS | 546                  |
| `authoring/v1` frontmatter agreement              | 3,624/3,630 (99.83%) |
| Real frontmatter disagreements                    | 6                    |
| Body-only scope differences                       | 544                  |

The compact retained record is sufficient for the closure scorecard; the full per-file report
remains an advisory CI artifact rather than a 13,304-line tracked projection.

## DR-049 authority-flip disposition

| Condition                                         | Current disposition                                                                                                                                     |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ≥99.5% corpus agreement; deterministic folds 100% | **Unmet.** Aggregate v1 frontmatter agreement is 99.83%, but six real disagreements remain and deterministic-fold 100% is not proven for the v2 target. |
| ≥30-day advisory soak                             | **Unmet.** The core 0.10.0 dual-lane re-baseline began 2026-08-27.                                                                                      |
| Zero open P0 blockers                             | **Unmet.** Blueprint P0 work remains open outside Epic 9.                                                                                               |
| Tested Rekor superseding-event rollback           | **Unmet.** No retained complete rollback receipt exists.                                                                                                |
| CTO + CISO + VP-DevRel sign-off                   | **Unmet.** No role-based sign-off receipt is filed.                                                                                                     |
| ≥14-day public deprecation notice                 | **Unmet.** No completed notice window is filed.                                                                                                         |

No line in this AAR, document 810, the scorecard, or the pin update satisfies or waives those
conditions. Pin freshness and validator authority are independent axes.

## Exit scorecard read-back

The regenerated [Epic 1 scorecard](742-RA-DATA-epic-1-scorecard.json) now consumes the retained
boundary record instead of guessing from a local checkout:

| Row | Target evidence                                                                                                                                                |
| --: | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|  38 | Exact roots match the retained npm observation; one core version resolves; ordering tests are blocking inside the advisory workflow; violations route to Slack |
|  39 | A retained exact-head report names core 0.10.0, both authoring lanes, and the integer strict-v2 decision metric                                                |
|  54 | All three legacy forge proofs are classified E0                                                                                                                |
|  55 | Zero unretained E2/E3 claims                                                                                                                                   |
|  56 | Zero public JRig verification claims                                                                                                                           |

Rows 52, 53, 58, and 59 remain the Epic 5 upstream receipts consumed by this boundary. A missing or
pin-mismatched document 810 now makes rows 38/39 fail closed as not reproducible or stale evidence.

## Process exceptions and review boundary

E9.10, E9.12, and E9.13 were integrated directly on `main` under the repository owner's documented
exception rather than the blueprint's preferred one-PR wording. Their implementation receipts are
retained in their canonical beads: exact pins and one-copy graph, scratch-branch forced Slack
violation, and dual-lane advisory run respectively. This AAR records the exception; it does not
generalize direct-main integration or waive current merge gates.

The independent closure reviewer must, on the exact proposed head:

1. reproduce rows 38 and 39 and plant registry/pin drift to observe fail-closed status;
2. force the recorder's self-approval and local-real-ledger refusal tests;
3. confirm both shadow lanes and strict `existing-PASS / kernel-FAIL = 0`;
4. confirm all six DR-049 conditions remain explicitly unmet and authority did not move; and
5. read back all fourteen canonical tasks plus the duplicate-shell disposition.

## Durable memory and rollback

After the tracked candidate passes review, Beads key `kernel-flip-target` must read back exactly:

> kernel-flip-target: authoring/v1 shadow reports existing-PASS/kernel-FAIL = 0 — flipping to v1
> would be a pure loss of enforcement; the flip target is v2 and all six DR-049 conditions remain
> unmet

The memory is a boundary reminder, not evidence that the conditions will remain unmet forever.
Live shadow results and a future authority decision must use new retained evidence.

Rollback is a focused revert of this closure slice: handbook corrections, retained document 810,
scorecard consumption/tests, generated index, and this AAR. It does not revert the already-merged
Epic 9 implementations. If document 810 is removed or mismatches the root pin, scorecard rows 38
and 39 intentionally fall back to a non-target state. No Dolt history, signed evidence, registry
package, or external system is mutated by this record.
