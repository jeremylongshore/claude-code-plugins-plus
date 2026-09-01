# Snowflake v2.2 Operator Parity Decision

**Status:** accepted implementation authority
**Date:** 2026-08-31
**Owner:** marketplace CTO
**Beads:** `claude-zhc5.9`, `claude-na0m`, `claude-na0m.1`

## Decision

Keep all eight Snowflake v2.1 skills. None is filler. The v2.2 objective is to
make their evidence more complete and their operator entry points easier to use,
not to rebuild the generic 30-skill taxonomy or chase a larger catalog count.

The obsolete Snowflake skill database, including `snowflake-hello-world`, was
already removed and guarded against regeneration in v2.1. A future change that
restores generic setup, checklist, SDK, architecture, error-catalog, or static
limit-table skills violates this decision.

## Evidence boundary

Three independent research/audit lanes were reconciled with root verification:

- Snowflake documentation, release notes, and Snowflake-maintained repositories
  define product behavior.
- Original research discovered through scholarly search informs diagnostic method,
  but does not override current product documentation.
- Reddit, Stack Overflow, dbt issues, and other practitioner channels establish
  recurrence and vocabulary only; they are not product-behavior authority.
- Repository tests, validators, package inspection, and the Databricks comparison
  establish the shipped implementation state.

The Semantic Scholar MCP connector was not exposed in this session. Semantic
Scholar web discovery and original publisher pages were available. This record does
not claim an MCP call that did not occur.

## Baseline: strong core, weaker ergonomics

The current Snowflake pack has eight operator skills, 32 references, deterministic
analyzers, a shared read-only collector, eight eval specifications, and 127 passing
focused tests. All eight skills grade A. The retired 30-skill filler database is
absent and permanent redirects cover former public slugs.

The Databricks comparison has five skills, nine command wrappers, four agents, five
hooks, and richer per-skill operator documents, but no skill-level tests were found
and one skill currently grades B. Therefore the gap is not that Snowflake lacks
substantive logic. The gap is current-state evidence coverage and discoverable
operator interfaces.

## Pain-to-capability decisions

| Operator pain | Verified platform boundary | v2.2 decision |
| --- | --- | --- |
| Cost attribution is mistaken for invoice truth | Query attribution excludes idle time and other spend domains; warehouse budgets and usage views have different attribution and latency boundaries. | Upgrade `snowflake-cost-leak-hunter` to reconcile warehouse, idle, serverless, storage, transfer, budget/monitor, Adaptive Warehouse, and Cortex AI evidence while separating attributable, unattributable, estimated, delayed, and invoice-only amounts. |
| Historical grants are mistaken for effective access now | Effective access can flow through role inheritance, direct user grants, `PUBLIC`, ownership, secondary roles, managed access, and future-grant precedence. | Upgrade `snowflake-access-guardian` with a sanitized current snapshot and current-versus-history reconciliation. Missing or stale paths block least-privilege conclusions. |
| Strong-auth migration can lock out people and workloads | Identity type, client support, auth/network/session policy precedence, login-history latency, workload bindings, and recovery paths differ. | Upgrade `snowflake-strong-auth-migration-pilot` with an owner-bound migration denominator, enforcement dates, client evidence, canary results, and break-glass proof. |
| Query symptoms have different causes and incomplete observability | Operator statistics have query-age/visibility bounds; Query Insights omits several query classes. | Upgrade `snowflake-query-forensics` with a bounded query-ID collection path, aligned comparisons, explicit limitations, and completeness receipts. |
| Pipeline history omits current graph state | Stream staleness, task state, dynamic-table reinitialization, pipe status, replay semantics, and dbt definition drift can disagree with history. | Upgrade `snowflake-pipeline-guardian` with current configuration, graph completeness, staleness horizons, and replay/reinitialization risk. |
| A quality result can hide missing monitoring coverage | Expectations, DMF associations, training/evaluation state, schedules, notification grouping, edition, and privilege visibility form the real denominator. | Upgrade `snowflake-data-quality-sentinel`; training and no-evaluation must never be reported as health. |
| Replication history does not prove failover readiness | Group configuration, object coverage, schedules, progress, dependencies, edition boundaries, RPO, and operator exercise evidence are separate. | Upgrade `snowflake-failover-readiness-drill` without executing failover or failback. |
| Deployment previews can still hide destructive churn | Terraform state/provider migrations, preview resources, behavior-change bundles, dbt Project changes, backups, and post-change invariants interact. | Upgrade `snowflake-deploy-medic` with versioned impact mapping and zero-change receipts. |

Primary product sources include:

- [Snowflake cost attribution](https://docs.snowflake.com/en/user-guide/cost-attributing)
- [Cortex AI cost management](https://docs.snowflake.com/en/user-guide/snowflake-cortex/governance-and-availability/ai-cost-management-and-governance)
- [Access control overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)
- [Authentication policies](https://docs.snowflake.com/en/user-guide/authentication-policies)
- [Query Insights](https://docs.snowflake.com/en/user-guide/query-insights)
- [Dynamic-table troubleshooting](https://docs.snowflake.com/en/user-guide/dynamic-tables-troubleshooting)
- [Data-quality expectations](https://docs.snowflake.com/en/user-guide/data-quality-expectations)
- [Replication monitoring](https://docs.snowflake.com/en/user-guide/account-replication-monitor)
- [Terraform provider roadmap](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/ROADMAP.md)

## New public skill decisions

The legacy gate in `claude-zhc5.9` is resolved as follows: a generic Snowflake
observability-assurance skill is rejected because its trigger and evidence overlap
query, pipeline, cost, data-quality, and failover workflows. The proposed
privacy-policy engineer is approved only in the narrower, denominator-driven form
below; it must not become a broad policy tutorial.

### Approve: `snowflake-governance-coverage-auditor`

This job is distinct from access review and data-quality monitoring. It answers:
which governed sensitive assets lack effective classification, tags, masking,
row-access, projection, join, or aggregation coverage? Its artifact is a
denominator-based protection report with precedence conflicts, stale/pending/failed
classification states, edition/privilege boundaries, policy simulations, and a
dry-run remediation packet.

Sources:

- [Tag-based policies](https://docs.snowflake.com/en/user-guide/tag-based-policies)
- [Monitoring tags and policies](https://docs.snowflake.com/en/user-guide/object-tagging/monitor)
- [Classification troubleshooting](https://docs.snowflake.com/en/user-guide/classify-troubleshooting)

### Approve: `snowflake-native-app-release-sheriff`

This is a provider release-preflight job, not generic deployment guidance. It
validates manifest and setup-script idempotence, privilege and App Spec deltas,
security-scan state, version compatibility, upgrade cohorts, and rollback
observables. It never publishes, upgrades, or promotes an app.

Sources:

- [Native App setup scripts](https://docs.snowflake.com/en/developer-guide/native-apps/creating-setup-script)
- [Native App security scans](https://docs.snowflake.com/en/developer-guide/native-apps/security-run-scan)
- [Native App upgrades](https://docs.snowflake.com/en/developer-guide/native-apps/update-app-develop)

### Defer: sharing, Snowpark telemetry, SnowConvert, and listing operations

Secure-sharing boundary review is real but partially overlaps governance and access
coverage; implement the approved governance skill before deciding whether a separate
slot remains necessary. Snowpark telemetry triage is evidence-backed but lower
priority. SnowConvert reconciliation and listing/auto-fulfillment operations need
more demand evidence. None may be added merely to round out the portfolio.

## Architecture and delivery order

1. Make `shared/evidence` the canonical collector source and generate the eight
   self-contained bundled copies with a non-mutating drift check.
2. Deepen the eight retained skills against current-state, completeness, freshness,
   privacy, edition, and privilege boundaries.
3. Create only the two approved new skills using the `skill-creator` contract.
4. Add canonical executable entry points and concise runbooks. Harness-specific
   commands or agents may be thin projections only; decision logic stays in the
   model-neutral skill scripts.
5. Require deterministic happy, failure, edge, and adversarial tests; marketplace A;
   Tier-2; package, projection, Freshie, independent-review, and protected-CI proof.

The dependency graph and acceptance evidence are authoritative in swarm epic
`claude-na0m`.
