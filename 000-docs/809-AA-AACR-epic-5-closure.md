<!-- doc-class: record -->

# Epic 5 Closure — Coherent Freshie Evidence — After-Action Review

- **Date:** 2026-08-30
- **Authority:** Blueprint 727, Epic 5 (§ 13), canonical beads E5.1–E5.13 plus the export-order producer fix
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Epic bead:** `claude-h05s`
- **Closure bead:** `claude-h05s.16`
- **Status:** Closure record; the parent bead closes only after this filing, durable-memory read-back, merge, and independent boundary review

## Verdict

Epic 5's implementation and exit evidence are complete. Its 14 canonical implementation children
and the exit-evidence remediation are closed, and the declared exit scorecard is reproducible from
tracked evidence. The closure transaction remains open until this AAR merges, its durable-memory
receipt is read back, `claude-h05s.16` closes, and the parent receives its final boundary read-back.
The final implementation correction merged normally as
[PR #1387](https://github.com/jeremylongshore/tons-of-skills-marketplace/pull/1387), merge
`78e3580ceeeba0996e4cc7d6ade38a601b71746c`, after 34 reporting checks passed with zero failures.
Required `ci-required`, `gitleaks`, and `skill-conform` contexts passed; all three test matrix
partitions passed; an independent exact-head review returned PASS.

The operational result is fail-closed: an internally inconsistent run cannot export, a lagging or
mutated grade projection cannot pass, unretained behavioral claims remain E0 rather than becoming
badges, and the real Freshie lifecycle executes in blocking CI against isolated scratch state.

## What changed

The old boundary checked whether required run fields were non-null, not whether the header and its
rows described the same run. The blueprint's retained historical finding was stark: every recorded
run 6–11 disagreed with its row count, and the old gate could accept the run-6 shape of 3,000
declared skills with only 19 rows. Current databases no longer retain that contradictory snapshot;
the durable regression therefore reconstructs the historical shape hermetically and proves the CLI
refuses it without touching the coherent live inventory.

The complete correction established five linked invariants:

1. `gate_run_completeness()` compares the run header with same-run rows before export work.
2. The grade histogram, CSV row count, CSV hash, run tag, and immutable Dolt commit identify one
   export rather than adjacent runs.
3. Behavioral-evaluation identity is `jrig_run_id`, separate from discovery-run identity.
4. Evidence class and retention are validity conditions: the three legacy proofs are honestly E0;
   no public verified projection remains.
5. Blocking CI installs a pinned Dolt binary immediately before an exact guarded runner that must
   execute one real hermetic cycle with zero skips, against scratch SQLite/Dolt/filesystem state,
   then prove live-server refusal.

## Canonical bead-to-evidence map

| Scope                        | Bead             | Durable evidence                                                        |
| ---------------------------- | ---------------- | ----------------------------------------------------------------------- |
| E5.1 run completeness        | `claude-h05s.1`  | PR #1369; CI run 33132060360; 3,000/19 hermetic refusal                 |
| E5.2 run identity rename     | `claude-h05s.2`  | `forge_proofs.run_id` → `jrig_run_id`; recorder suite 7/7               |
| E5.3 counterfeit detection   | `claude-h05s.3`  | magic-byte promotion boundary; scorecard row 12                         |
| E5.4 export freshness        | `claude-h05s.4`  | PR #1370; CI run 33134022574; run-12 export receipt                     |
| E5.5 counterfeit disposition | `claude-h05s.5`  | satisfied by Epic 1 asset-integrity PR #1216 and AAR 748                |
| E5.6 promotion fail-closed   | `claude-h05s.6`  | Unconditional-success swallows removed; blocking regression             |
| E5.7 hermetic cycle          | `claude-h05s.8`  | commit `0f40150c3`; scratch DB/fake remote/live-server proof            |
| E5.8 runtime-table allowlist | `claude-h05s.9`  | planted JRig table aborts before Dolt initialization or push            |
| E5.9 single-writer refusal   | `claude-h05s.10` | lockfile plus real port-3308 refusal; four scorecard refusal tests      |
| E5.10 byte reproducibility   | `claude-h05s.11` | commit `18b60b9e5`; corrected receipt: 49 Dolt-sync tests passed        |
| E5.11 evidence standard      | `claude-h05s.12` | [Evaluation Evidence Standard](807-DR-STND-evaluation-evidence.md)      |
| E5.12 honest demotion        | `claude-h05s.13` | three legacy records E0; demotion receipt; public badge dark            |
| E5.13 stranded-tag recovery  | `claude-h05s.14` | commit `849519ee9`; one-time/idempotent recovery regression             |
| Producer-order correction    | `claude-h05s.15` | PR #1368; CI run 33131412924; allowlist runs before Dolt identity setup |

The completion audit added two non-canonical closure children without changing the implementation
scope: `claude-h05s.17` made the exit evidence reproducible and merged as PR #1387;
`claude-h05s.16` owns this AAR, durable memory, and final read-back transaction.

## Exit scorecard read-back

The generated [Epic 1 scorecard](742-RA-DATA-epic-1-scorecard.json) now reports every Epic 5 exit
row at its declared target:

| Row | Result        | Current receipt                                                                             |
| --: | ------------- | ------------------------------------------------------------------------------------------- |
|  12 | measured/pass | magic-byte detector passed all fixed probes; 0 missed                                       |
|  52 | target_met    | run 14: 3,053 declared = 3,053 rows; delta 0                                                |
|  53 | target_met    | run 14: 3,630 compliance rows = 3,630 grade rows; matching SHA-256                          |
|  54 | target_met    | three legacy forge proofs classified E0; zero unclassified                                  |
|  55 | target_met    | zero unretained E2/E3 claims; `retention_percent` remains `null`, not fabricated 100%       |
|  56 | target_met    | zero public JRig verification claims                                                        |
|  58 | target_met    | pinned install, guarded full cycle, fake remote, scratch state, and server refusal all true |
|  59 | measured      | nonblocking lock and live-server mechanical refusal present                                 |

Run 14 is bound to immutable Dolt commit `2ljhn79ge74uj1kd7q2chqgo9ne0tulb`. Its grade CSV SHA-256
is `72fbb289e8451d9a4bbe95cae0b9a1797588c0197589f94ddd1cde48241e4ef0`; the histogram is
A 1,872 / B 1,117 / C 479 / D 157 / F 5.

## Verification and review receipts

- `pnpm run measure:e1:check` — 39 measurement tests passed and the tracked artifact matched its
  exact Git-index regeneration.
- Guarded hermetic runner — one test executed, zero skipped, real cycle passed locally and in the
  `python-tests` CI partition.
- PR #1387 exact reviewed head — `85ca4a1317ea3c28a4f53a33fe45417533dfd798`.
- GitHub run `33303047907` — `ci-required`, `verify`, `test (python-tests)`,
  `test (mcp-plugins)`, and `test (validation-scripts)` passed.
- Required independent workflows — `gitleaks` run `33303047922` and `skill-conform` run
  `33303047885` passed.
- Independent boundary review — PASS after reproducing and closing skipped tests, generator no-op,
  lifecycle replacement, aliased mutation, and post-verification binary-overwrite attacks.

No admin bypass, branch-protection change, Dolt-history rewrite, public-CI DoltHub write, or live
inventory mutation was used for closure.

## Durable memory

Beads key `freshie-run-coherence` stores the blueprint's historical invariant:

> freshie-run-coherence: gate_run_completeness tested only IS NULL; every run 6-11 header
> disagrees with its row count (run 11: 3069 vs 3678)

`bd recall freshie-run-coherence --json` returned the same key and value after the write. The
historical observation is retained as program memory; the current executable source of truth is the
coherence gate plus its hermetic contradictory-run regression, not a mutable old database snapshot.

## Lessons and residuals

- A green test command is not proof that the governed body ran. Exact test count, zero skips, and a
  guarded method invocation are part of the boundary now.
- Verifying a downloaded binary is insufficient if another step can replace it before use. The
  pinned install immediately precedes the exact runner and the measurement contract enforces that
  adjacency.
- Zero E2/E3 claims is a safe state, not a 100% retention measurement. The scorecard correctly
  leaves the percentage null while proving zero unretained claims.
- Historical data claims need a retained snapshot or a hermetic reconstruction. The run-6 3,000/19
  failure is preserved as executable evidence because the present databases are coherent.

Downstream Epics 8–10 may consume the evidence standard and Freshie gates, but they do not reopen
Epic 5. Their remediation cohorts, certification chain, and observation windows remain separately
owned by their own beads.
