# Databricks Cluster Forensics

**Live cluster-lifecycle forensics for the 2 AM compute break — buckets a slow cold start by event stage, decodes umbrella launch-failure codes, audits Photon fallback, and flags DBR-upgrade landmines, naming each failure by its actual error code and version-specific fix.**

## Problem

The compute layer is where Databricks breaks at 2 AM, and the platform reports the break in
umbrella codes and elapsed-minute counters that hide the cause. A cold start on a
VNet-injected / no-public-IP workspace stretches into a long PENDING tail with no per-stage
attribution; a Photon cluster silently falls back to row-based Spark on UDFs while still
billing the ~2× premium; a DBR bump arms three post-upgrade landmines (14.x 500 MB CWD
cap, 15.1 DBFS-root-lib + JDK-11 removal, 15.4 JDBC calendar flip);
CLOUD_PROVIDER_LAUNCH_FAILURE and NPIP_TUNNEL_SETUP_FAILURE each hide five distinct causes;
and spot reclaims abort shuffle stages against `spark.stage.maxConsecutiveAttempts` under a
message that blames "stage failure," not spot. The v1 skills narrate these symptoms; none
correlates a cluster's live events to name the failure by its code with the version-specific
fix.

## Solution

A diagnose → correlate → name-the-cause pipeline. A bundled Python bucketer splits a
cluster's `clusters.events` PENDING time into named stages (cloud VM allocation / network +
DNS / library + init); two scanners (`find-cwd-writes.py` AST, `scan-jar-jdk.sh` `javap`)
catch the DBR landmines before the bump; a termination-codes reference decodes the umbrella
codes into their specific causes; and a `cluster-event-investigator` subagent fans out one
root-cause thread per cause class. Evidence spans two MCP planes — the
`databricks-workspace-mcp` control plane for cluster events and the Databricks managed SQL
MCP for the `system.*` Photon audit — with an advisory-mode fallback that accepts pasted
events / config when an MCP is absent. It diagnoses and recommends; it never mutates a
cluster.

## W5

|           |                                                                                                                                          |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Who**   | Data-platform / SRE on-call, platform engineers planning a DBR upgrade, and admins of VNet-injected workspaces                          |
| **What**  | Correlates a cluster's live lifecycle events across two API planes to name a slow start, a launch failure, a Photon leak, an upgrade landmine, or a spot-shuffle abort by its actual error code + version-specific fix |
| **When**  | 2 AM, a cluster won't start or is crawling; a launch-failure / NPIP code; before a DBR runtime bump; a "Photon isn't helping" review     |
| **Where** | Claude Code (also Codex-compatible), against a Databricks workspace with the workspace MCP registered and a SQL warehouse               |
| **Why**   | Deterministic event bucketing + exact scanners name the cause the cluster page hides — and every line is a read-only diagnosis, never a mutation |

## Stack

| Layer | Choice |
| ----- | ------ |
| Skill runtime | Claude Code `SKILL.md` (compatibility: Codex) |
| Control-plane evidence | `databricks-workspace-mcp` — `clusters_list` / `clusters_get` / `clusters_events` |
| SQL / system evidence | Databricks managed SQL MCP over `system.*` (CLI Statement Execution API fallback) — Photon coverage + node timeline |
| Deterministic analysis | Bundled `cluster-coldstart-forensics.py` (PENDING-time bucketer), `find-cwd-writes.py` (AST), `scan-jar-jdk.sh` (`javap`) |
| Fan-out | `cluster-event-investigator` subagent — one root-cause thread per cause class |
| Knowledge | `references/*.md` loaded on demand (termination-codes decode, DBR version-landmine table, Photon fallback rules, event stages) |

## Differentiators

1. **Names the cause, doesn't narrate the symptom** — decodes
   CLOUD_PROVIDER_LAUNCH_FAILURE / NPIP_TUNNEL_SETUP_FAILURE into one of five specific
   causes each and buckets PENDING time to the exact stage that spiked, where the v1
   `databricks-common-errors` / `databricks-incident-runbook` skills only describe the
   symptom.
2. **The LLM never eyeballs the timeline** — deterministic event bucketing plus AST and
   `javap` scanners produce the same buckets and landmine list every run; the LLM does the
   root-cause reasoning on top, not the arithmetic.
3. **Version-specific mitigations, caught before the bump** — the merged upgrade advisor
   flags the 14.x CWD cap, the 15.1 DBFS-root-lib + JDK-11 removal, and the 15.4 JDBC
   calendar flip against the target DBR before the upgrade, not after cutover.
