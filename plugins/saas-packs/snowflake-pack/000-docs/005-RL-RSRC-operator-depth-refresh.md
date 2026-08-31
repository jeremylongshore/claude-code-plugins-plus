# Snowflake Operator Depth Research Refresh

**Status:** accepted implementation input
**Date:** 2026-08-31
**Beads:** `claude-zhc5.5`, `claude-zhc5.6`, `claude-zhc5.7`,
`claude-zhc5.8`, `claude-zhc5.11`, `claude-zhc5.12`

## Question

Does the six-skill Snowflake v2 pack meet the Databricks operator bar, and which
additional Snowflake jobs are distinct and evidenced enough to earn public skill
slots?

## Method and evidence boundary

Three independent research lanes and one repository audit were reconciled:

- current Snowflake documentation and Snowflake-maintained repositories defined
  product behavior;
- original CIDR, VLDB, arXiv, and NIST publications informed diagnostic method;
- Stack Overflow, Reddit, practitioner articles, and repository discussions were
  used only to discover recurring complaints, never as product-behavior authority;
- live repository tests, marketplace validation, package dry-runs, and path checks
  established the shipped state.

The Semantic Scholar MCP connector was not exposed in this session. Semantic
Scholar web discovery and its public API were attempted, but the API rate-limited
requests. No unavailable connector is claimed as evidence. Papers were verified at
their original publishers instead.

## Finding: v2 is substantive but not yet integrated

The six live skills are not filler. They average 95.2/A in the marketplace rubric,
and their 50 deterministic tests pass. The remaining quality gap is delivery:

- every workflow begins with manually prepared JSON or pasted evidence;
- the pack has no model-neutral live evidence collector or reusable operator command;
- stale v1 filler still exists in `plugins/saas-packs/skill-databases/snowflake/`,
  where 30 template entries are marked `Production=true` even though their declared
  skill paths do not exist;
- the npm artifact includes ignored Python bytecode and excludes research documents
  linked by the packaged README;
- compatibility metadata describes only Claude Code even though the workflow logic
  and analyzers are model-neutral.

## Existing-skill depth matrix

| Skill | Verified production pain | Required depth work |
| --- | --- | --- |
| `snowflake-cost-leak-hunter` | Query attribution excludes idle time and is not invoice truth; cost and latency objectives conflict. | Add read-only collection, attribution-completeness scoring, query-fingerprint cost/latency tradeoffs, and bounded right-sizing experiments. |
| `snowflake-query-forensics` | Queueing, spill, poor pruning, exploding joins, cache effects, and workload mixing require different remedies. | Correlate operator statistics, Query Insights, warehouse load, query hashes, and pruning evidence; add clustering/search-optimization ROI and rollback thresholds. |
| `snowflake-pipeline-guardian` | Task graphs, dynamic tables, streams, and Snowpipe fail across subsystem boundaries; notifications can duplicate. | Add live collectors, idempotency and overlap checks, skipped-run detection, notification deduplication, replay-risk classification, and post-retry invariants. |
| `snowflake-deploy-medic` | Terraform grant migration, behavior-change bundles, and state drift can turn routine upgrades into destructive churn. | Add a real preflight entry point, current bundle inventory, affected-object mapping, state-backup proof, and zero-change migration receipts. |
| `snowflake-access-guardian` | Role inheritance, direct grants, ownership, managed access, and future-grant precedence produce effective-access drift. | Add grant collection with source timestamps, direct-user and ownership escape paths, future-grant precedence, and positive/negative access proofs. |
| `snowflake-strong-auth-migration-pilot` | Strong-auth rollout can lock out people and workloads when identity types, clients, and recovery paths are incomplete. | Add read-only identity/workload inventory, capability evidence, break-glass verification, canary receipts, and remove unnecessary edit authority. |

## Research-backed net-new jobs

### P0: data-quality sentinel

Snowflake data-quality monitoring requires operators to define data metric functions,
bind expectations, distinguish an unevaluated expectation from a pass, route
notifications, and investigate violations. This is a separate job from pipeline
availability.

Primary sources:

- [Data quality expectations](https://docs.snowflake.com/en/user-guide/data-quality-expectations)
- [Data quality notifications](https://docs.snowflake.com/en/user-guide/data-quality-notifications)
- [`DATA_QUALITY_MONITORING_EXPECTATION_STATUS`](https://docs.snowflake.com/en/sql-reference/local/data_quality_monitoring_expectation_status)

Approved skill: `snowflake-data-quality-sentinel`.

### P0: failover readiness drill

Asynchronous replication, refresh failures, edition constraints, failover-group
coverage, stream Time Travel limits, and task/stream dependencies that cross group
boundaries can invalidate a disaster-recovery plan. This is a readiness and rehearsal
job, not ordinary pipeline incident triage.

Primary sources:

- [Business continuity and disaster recovery](https://docs.snowflake.com/user-guide/replication-intro)
- [Monitoring replication and failover](https://docs.snowflake.com/en/user-guide/account-replication-monitor)
- [Replication considerations](https://docs.snowflake.com/en/user-guide/account-replication-considerations)

Approved skill: `snowflake-failover-readiness-drill`.

### P1: research-gated candidates

`snowflake-observability-assurance` and `snowflake-privacy-policy-engineer` have
credible evidence, but their boundaries overlap existing telemetry, access, and
pipeline work. They do not earn public slots until P0 implementation demonstrates a
distinct trigger, deterministic capability, and output contract. Migration
reconciliation, policy-coverage auditing, and data-share governance remain candidates
for the same reason.

## Supporting research

- [Cost-Intelligent Data Analytics](https://www.vldb.org/cidrdb/papers/2024/p78-zhang.pdf)
  documents the cost/latency tradeoff and limits of manual warehouse sizing.
- [Pruning in Snowflake](https://arxiv.org/abs/2504.11540) provides production
  evidence for pruning-aware query diagnosis.
- [Cloud Analytics Benchmark](https://www.vldb.org/pvldb/vol16/p1413-renen.pdf)
  shows why production fixtures need workload variance, DML, elasticity, latency,
  and monetary cost rather than tutorial queries alone.
- [NIST SP 800-92](https://csrc.nist.gov/pubs/sp/800/92/final) supports explicit log
  coverage, retention, access, and analysis controls.

## CTO implementation decision

1. Preserve the six v2 skills and deepen their actual operator paths.
2. Delete the stale 30-entry Snowflake skill database and prevent regeneration.
3. Build a model-neutral, read-only evidence collection layer before adding public
   slots. Authentication remains in an existing Snowflake CLI profile; collectors
   never accept, print, or persist credentials and never issue mutating SQL.
4. Build only the two P0 net-new skills above.
5. Require deterministic fixtures, negative/adversarial cases, source freshness,
   privilege and edition caveats, dry-run boundaries, machine-readable receipts,
   marketplace A, and Tier-2 green for every changed or new skill.
