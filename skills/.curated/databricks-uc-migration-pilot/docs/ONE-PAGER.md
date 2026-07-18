# Databricks UC Migration Pilot

**Audits every Hive Metastore table for Unity Catalog readiness, turns the result into a dependency-ordered per-table migration plan, and traces live UC permissions — before the September 30, 2026 HMS end-of-support deadline.**

## Problem

Every Databricks customer still on the legacy Hive Metastore (HMS) has to move to Unity
Catalog (UC), and **HMS becomes read-only on September 30, 2026** — after which "migrate
later" stops being an option. A `hive_metastore` table list looks migratable until you
check what actually blocks it: managed tables on the DBFS root, external tables on retired
schemes (`adl://`, `wasbs://`), clusters stuck in LEGACY_TABLE_ACL mode, and the
CLONE-drops-Delta-history gotcha that loses time-travel after cutover. Then UC's two-level
identity-plus-grant model breaks access in ways HMS never did, and "why can't user X see
the table?" eats ~90 minutes a ticket. The v1 migration skills are prose that never reads a
single table's storage URI.

## Solution

A **detect → plan → trace → isolate** pipeline. A bundled `audit-hms-readiness.py` reads
every HMS table's real storage URI and classifies it **ready / blocked / orphan** with the
specific blocker; a `migration-planner` subagent turns that CSV into a dependency-ordered
plan with one verb per table (SYNC / deep-clone / rewrite / skip) and flags every
history-lossy CLONE before you run it; a `uc-permission-tracer` subagent diagnoses the
two-level access model down to the missing group and grant; and `/uc-env-pattern-picker`
resolves the one-metastore-per-region constraint into a concrete isolation pattern. It
classifies and plans — it never runs the migration.

## W5

|           |                                                                                                                                            |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Who**   | Data-platform / lakehouse engineers, workspace + metastore admins, and platform architects still running on HMS                            |
| **What**  | Audits every HMS table for UC-migratability, emits a dependency-ordered per-table plan, traces UC access failures, and picks an isolation pattern |
| **When**  | Ahead of the Sept-30-2026 HMS end-of-support deadline; any `hive_metastore.*` table or "why can't user X see the table in UC" moment         |
| **Where** | Claude Code (also Codex-compatible), against a Databricks workspace with a UC metastore already provisioned in-region                       |
| **Why**   | A real readiness audit + dependency-ordered plan + live permission trace — not documentation-cosplay prose — and it classifies, never auto-migrates |

## Stack

| Layer               | Choice                                                                                                       |
| ------------------- | ----------------------------------------------------------------------------------------------------------- |
| Skill runtime       | Claude Code `SKILL.md` (compatibility: Codex)                                                                |
| Readiness audit     | Bundled `scripts/audit-hms-readiness.py` — deterministic storage-URI-scheme classifier → readiness CSV      |
| Metadata data plane | Databricks CLI Statement Execution API over `hive_metastore` inventory + UC `SHOW GRANTS` + `system.*`      |
| IAM data plane      | Read-only AWS IAM introspection (storage-credential / external-location D2 diagnosis)                        |
| Planning + tracing  | Two subagents — `migration-planner` (dependency-ordered plan) and `uc-permission-tracer` (two-level access) |
| Isolation           | `/uc-env-pattern-picker` decision tree for the one-metastore-per-region constraint                          |
| Knowledge           | `references/*.md` loaded on demand (storage schemes, migration verbs, UC access model, isolation patterns)  |

## Differentiators

1. **A real readiness audit, not prose** — the bundled classifier reads every table's
   actual storage URI and returns ready / blocked / orphan with the *specific* blocker
   (`dbfs:/` root, `wasbs://`/`adl://`, LEGACY_TABLE_ACL compute, dangling location), which
   is exactly what the v1 documentation-cosplay migration skills never do.
2. **A dependency-ordered plan with the right verb per table** — SYNC vs deep-clone vs
   rewrite vs skip, ordered so dependencies come out safe, and it flags the
   CLONE-drops-Delta-history tables *before* you lose time-travel, not after.
3. **It traces the live two-level UC access model** — "user X needs group Y membership AND
   grant Z run by metastore admin W" — so access doesn't silently break the morning after
   cutover, and it classifies rather than executing any irreversible migration step.
