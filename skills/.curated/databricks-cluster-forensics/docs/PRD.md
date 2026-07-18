# PRD: databricks-cluster-forensics

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-12
**Status:** Active

> Authored to the `templates/skill-docs/` submission standard at the Pack / flagship tier
> (this is a `databricks-pack` skill) as the design record for `databricks-cluster-forensics`,
> per `000-docs/700-DR-GUID-skill-submission-standard.md` §2 ("the same matrix applies to
> Intent Solutions' own skills"). Companion docs beside it: `ADR.md`, `ONE-PAGER.md`.

## Problem

The compute layer is where Databricks breaks at 2 AM, and the platform reports the break
in umbrella codes and elapsed-minute counters that hide the cause. A cold start on a
VNet-injected / no-public-IP (NPIP) workspace stretches into a long PENDING tail, and the
cluster page shows the minutes elapsed but not whether cloud VM allocation, network + DNS
setup, or library and init-script install ate them (D01). A Photon-enabled cluster
silently falls back to row-based Spark on Python/Scala UDFs and other unsupported
operators while still billing the ~2× Photon SKU premium — you pay for the vectorized
engine and get the row engine (D02). And a Databricks Runtime (DBR) bump quietly arms
three landmines that never surface until after the upgrade: the DBR 14.x 500 MB cap on
notebook current-working-directory writes (D03), the 15.1 removal of DBFS-root library
installs plus the JDK-11 drop that breaks JARs built against it (D04), and the 15.4 JDBC
calendar flip that silently shifts pre-1582 dates (D05).

When a cluster refuses to start at all, the termination code is an umbrella:
CLOUD_PROVIDER_LAUNCH_FAILURE and NPIP_TUNNEL_SETUP_FAILURE each hide five distinct real
causes — cloud vCPU quota, subnet IP exhaustion, instance-profile IAM, spot capacity,
egress/DNS/NSG — with a different fix behind each (D06). And on spot fleets a reclaimed
executor loses its shuffle-map output, Spark retries the stage, and enough consecutive
reclaims exhaust `spark.stage.maxConsecutiveAttempts` and abort the job under a message
that blames "stage failure," not spot (D10). The existing v1 skills
(`databricks-common-errors`, `databricks-incident-runbook`) narrate these symptoms; none
correlates a cluster's live events across the control-plane and SQL API surfaces to name
the failure by its actual error code with the version-specific mitigation. The operator
and the cost reviewer stall on the same gap: the code is visible, the cause is not.

## Target users

| User | Context | Primary need |
| ---- | ------- | ------------ |
| Data-platform / SRE on-call | 2 AM — a cluster is down, stuck PENDING, or a job just aborted | A per-stage / per-cause diagnosis that names the error code and the exact fix, not a symptom narration |
| Databricks platform engineer planning a DBR upgrade | About to bump the runtime and needs to know which landmines their code trips | A pre-upgrade scan (CWD writes, JDK-pinned JARs, JDBC calendar exposure) tied to the target DBR version |
| FinOps-minded data engineer | Paying the Photon premium and unsure it is earning it | A Photon-coverage audit that flags jobs falling back to Spark while billed at the Photon rate |
| Workspace admin on a VNet-injected / secure-connectivity workspace | Recurring cold-start and launch-failure sweeps | Decode the NPIP / cloud-provider umbrella codes into the specific network / quota / IAM cause |

## Success criteria

Criteria below are the skill's eval contract — each is written to become a judge criterion
in the skill's `eval-spec.yaml`.

1. Triggers on cluster/compute forensic questions ("cluster won't start", "why is my
   cluster slow to start", "CLOUD_PROVIDER_LAUNCH_FAILURE", "Photon isn't helping",
   "should I upgrade DBR") and does not trigger on unrelated Databricks prompts — eval
   criterion `triggers-on-cluster-forensics-question` (blocker) plus should-not-trigger
   control cases.
2. Cold-start PENDING time is bucketed deterministically by event stage (cloud VM
   allocation / network + DNS / library + init) and the report names WHICH stage spiked
   rather than a lump elapsed time — eval criterion `buckets-pending-time-by-stage`
   (regression-critical).
3. Every diagnosis names the actual error or termination code
   (CLOUD_PROVIDER_LAUNCH_FAILURE, NPIP_TUNNEL_SETUP_FAILURE, the specific stage-abort) and
   its version-specific mitigation, never a generic "check your config and retry" — eval
   criterion `names-error-code-and-version-mitigation` (blocker).
4. The three DBR-version landmines (14.x CWD cap, 15.1 DBFS-root-lib + JDK-11 removal, 15.4
   JDBC calendar flip) are flagged against the target runtime *before* the upgrade, each
   tied to its bundled detector — eval criterion `flags-dbr-landmines-before-upgrade`
   (blocker).
5. The skill diagnoses and recommends; it never restarts, resizes, edits, or terminates a
   cluster — read-only across both MCP planes — eval criterion `never-mutates-the-cluster`
   (regression-critical).

## Functional requirements

The pipeline is **collect events → bucket / scan deterministically → fan out per cause →
name the cause with its fix**.

- **FR-1 (cold-start forensics, D01):** Pull a cluster's lifecycle event stream via
  `databricks-workspace-mcp` `clusters_events` and run the bundled
  `scripts/cluster-coldstart-forensics.py` to split PENDING time into named stages — cloud
  VM allocation, network + DNS setup, library + init-script install — and report the stage
  that spiked; on VNet-injected / NPIP workspaces attribute the network bucket explicitly.
- **FR-2 (Photon fallback audit, D02):** Read Photon coverage from the `system.*` tables
  (via the managed SQL MCP, CLI Statement Execution API as fallback) and flag jobs paying
  the ~2× Photon SKU premium while operators (Python/Scala UDFs, unsupported expressions)
  fall back to row-based Spark — naming `runtime_engine` and the unsupported operators.
- **FR-3 (DBR upgrade landmines, D03/D04/D05):** Against a named target runtime, run
  `scripts/find-cwd-writes.py` (AST scan) for the 14.x 500 MB CWD-write cap, run
  `scripts/scan-jar-jdk.sh` (`javap` class-file-version scan) for the 15.1 DBFS-root-lib
  removal + JDK-11 drop, and flag the 15.4 JDBC calendar flip — all before the bump.
- **FR-4 (termination-code decode, D06):** Decode CLOUD_PROVIDER_LAUNCH_FAILURE and
  NPIP_TUNNEL_SETUP_FAILURE via `references/termination-codes.md` into the specific cause
  (cloud vCPU quota, subnet IP exhaustion, instance-profile IAM, spot capacity,
  egress/DNS/NSG) with the check to confirm each.
- **FR-5 (spot shuffle abort, D10):** Diagnose stage aborts from spot reclaim against
  `spark.stage.maxConsecutiveAttempts`, distinguishing a FetchFailed-driven retry storm
  from a genuine data failure, and recommend the on-demand-floor / retry-bump mitigation.
- **FR-6 (fan-out + dual-plane + advisory fallback):** Dispatch the
  `cluster-event-investigator` subagent to fan out one root-cause thread per cause class
  over the two MCP planes; if a plane is absent, accept pasted `clusters.events` JSON /
  cluster config and still bucket, decode, and name the cause instead of failing.

## Out of scope

- Applying any fix — the skill never restarts, resizes, edits, or terminates a cluster or
  job; every remediation is a recommendation for a human-approved action.
- Authoring cluster policies, spot configs, or autoscale tuning — that is
  `databricks-cost-tuning` / `databricks-performance-tuning`; this skill diagnoses live
  failures and coverage, it does not author config.
- Executing the DBR upgrade — the skill flags the landmines against the target runtime; a
  human runs the bump in a maintenance window.
- Cost-leak FinOps reporting (idle clusters, wrong-SKU jobs, oversized floors) — that is the
  sibling `databricks-cost-leak-hunter`; the Photon read here is scoped to the
  fallback-while-billed leak as a forensic symptom, not a dollar-ranked spend report.
- Non-Databricks Spark (OSS Spark, EMR, Synapse) — the termination codes, DBR version
  landmines, Photon SKU, and NPIP tunnel are Databricks-specific.
