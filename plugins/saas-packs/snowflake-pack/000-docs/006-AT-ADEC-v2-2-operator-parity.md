# Snowflake v3 Pain-to-Capability Decision

**Status:** accepted portfolio authority; implementation state is explicit below

**Date:** 2026-09-02

**Owner:** marketplace CTO

**Beads:** `claude-zhc5.9`, `claude-na0m`, `claude-na0m.1`

**Repository baseline:** `e486a1c1db4410cef073c66520d666ca3a9a6d37`

## Decision

Preserve the eight operator skills shipped in Snowflake pack `3.0.0`. They are the
current no-filler baseline. Do not restore the retired 30-skill tutorial taxonomy or
`snowflake-hello-world`, and do not add generic setup, SDK, checklist, architecture,
static-limit, or error-catalog skills to reach a round count.

The query-identity and provenance work delivered by
[PR #1411](https://github.com/jeremylongshore/tons-of-skills-marketplace/pull/1411)
at `c4eafaf138bc77499b8282e98df74b7623de7dcb` is part of the current v3
baseline. The retained-skill states below and the two approved additions do not have
the same delivery state. Every retained skill already ships a
deterministic core in v3; the table below names only the current-state collection or
reconciliation delta that remains. The two additions are portfolio decisions, not
claims that their implementation has landed. Each pending delta must move through
its own bounded Bead and protected pull request.

## Evidence and provenance boundary

This decision reconciles four evidence classes without treating them as
interchangeable:

- Current Snowflake documentation and Snowflake-maintained repositories define
  product behavior, limitations, privileges, and supported workflows.
- Original research informs diagnostic method but never overrides current Snowflake
  product documentation.
- Practitioner reports from issue trackers, forums, and community channels are
  discovery signals for recurrence and vocabulary, not product-behavior authority.
- The repository at the immutable baseline above, its focused tests, and merged PR
  history define what the marketplace actually ships.

The Semantic Scholar MCP connector was not available during the research session.
Web discovery and original publisher pages were used where available; this record
does not claim an MCP result. The supporting research and its authority boundaries
are recorded in
[`005-RL-RSRC-operator-depth-refresh.md`](005-RL-RSRC-operator-depth-refresh.md).

The superseded broad expansion in PR #1405 is source material only. Its generated
catalog, curated mirror, package, and Freshie outputs are not evidence of current
state and must not be replayed.

## Reproducible current-state receipt

Run these commands from repository baseline
`e486a1c1db4410cef073c66520d666ca3a9a6d37`:

```bash
node -e "const p=require('./plugins/saas-packs/snowflake-pack/package.json'); const fs=require('fs'); const d=fs.readdirSync('./plugins/saas-packs/snowflake-pack/skills',{withFileTypes:true}).filter(x=>x.isDirectory()).map(x=>x.name).sort(); console.log(p.version, d.length, d.join(','))"
test ! -e plugins/saas-packs/skill-databases/snowflake
python3 -m unittest tests.test_snowflake_pack_integrity
find plugins/saas-packs/snowflake-pack -type f -name 'test*.py' -print0 | sort -z | xargs -0 -n1 python3
```

Observed on 2026-09-02: version `3.0.0`; eight skill directories; the retired
Snowflake skill database absent; 5 pack-integrity tests passing; and 157 current
collector/analyzer tests passing across the nine test modules beneath the pack. This
replaces, rather than repeats, the superseded branch's 127-test assertion. No
portfolio-wide grade claim is made.

## Ranked pain-to-capability decisions

| Rank | Operator pain and product boundary | Skill | Shipped deterministic v3 core | Missing delta only | State at baseline |
| ---: | --- | --- | --- | --- | --- |
| 1 | Query history can be stale or mismatched to unrelated rows; operator statistics exist only for a completed query within their documented window and privileges. | `snowflake-query-forensics` | Schema-2 anchor query/source/role binding, terminal-state and operator-evidence gates, recursive redaction, and an independently recorded canonical-digest trust boundary, delivered by PR #1411. | Add bounded acquisition and source receipts for `GET_QUERY_OPERATOR_STATS` and Query Insights; do not weaken the separate trusted-digest boundary. | **Delivered v3 core; current-source collector delta pending.** |
| 2 | Query attribution does not cover idle time or every spend domain, and Cortex AI uses separate usage views and credit semantics. | `snowflake-cost-leak-hunter` | Receipt-validated collection for warehouse metering/load, query attribution, and metering history plus deterministic observed/estimated/non-claim classification. | Add source-stamped storage, transfer, Cortex AI, budget, and resource-monitor coverage, then reconcile those surfaces without presenting attribution as invoice truth. | **Partially delivered in v3; current-state collector/reconciliation delta pending.** |
| 3 | Historical grants do not prove effective access now because role inheritance, direct user grants, ownership, managed access, and future-grant precedence interact. | `snowflake-access-guardian` | Deterministic role-path analysis for direct-user/`PUBLIC`, ownership, managed access, future-grant precedence, and positive/negative verification receipts, plus Account Usage grant collection. | Collect current `SHOW` grant, policy, share, and session-context evidence and reconcile it to the historical receipt before least-privilege conclusions. | **Partially delivered in v3; current-state collector/reconciliation delta pending.** |
| 4 | Strong-auth rollout can lock out people or workloads when supported methods, policy precedence, workload binding, and recovery evidence differ. | `snowflake-strong-auth-migration-pilot` | Deterministic user/workload mapping, target-method decisions, owner and deadline checks, canary evidence, positive/negative receipts, and break-glass gates, plus Account Usage user collection. | Collect effective authentication/network/session policy state, current WIF/PAT capability, and login/canary evidence tied to each declared workload. | **Partially delivered in v3; current-state collector/reconciliation delta pending.** |
| 5 | Historical task, refresh, and copy rows can disagree with current task, stream, dynamic-table, pipe, and dbt Project state. | `snowflake-pipeline-guardian` | Deterministic dependency, staleness, overlap, idempotency, duplicate, notification, and replay-risk findings plus bounded task, dynamic-table refresh, and copy-history collection. | Collect and reconcile current task/stream/dynamic-table configuration and graph state, `SYSTEM$PIPE_STATUS`, and dbt Project object/run state. | **Partially delivered in v3; current-state collector/reconciliation delta pending.** |
| 6 | A data-quality pass can hide missing coverage, anomaly training, failed evaluation, schedule or notification gaps, edition limits, or privilege blind spots. | `snowflake-data-quality-sentinel` | Deterministic requirement-denominator analysis with separate quality and monitoring verdicts, explicit training/unevaluated/stale states, provenance hashes, and expectation-status/usage-history collection. | Collect current association, schedule, group, notification, execution-role, edition, and visibility inventories and reconcile them to result history. | **Partially delivered in v3; current-state collector/reconciliation delta pending.** |
| 7 | Replication history alone does not prove failover readiness or attainable RPO/RTO. | `snowflake-failover-readiness-drill` | Deterministic objective, group-denominator, dependency, target-validation, drill-event, RPO/RTO, and abort-gate classification plus replication refresh-history collection. | Collect current failover-group configuration, membership, object/dependency coverage, privileges, and target state, then reconcile them to history and operator drill receipts. | **Partially delivered in v3; current-state collector/reconciliation delta pending.** |
| 8 | A deployment preview can hide destructive churn across Terraform state/imports, schemachange history, behavior-change bundles, dbt Projects, backups, and post-change invariants. | `snowflake-deploy-medic` | Deterministic plan/state/import, migration checksum, BCR, affected-object, backup, rollback, and zero-change receipt classification. | Normalize current behavior-change bundle status and dbt Project object/run evidence, then bind the affected-object map and post-change checks to the saved plan and account identity. | **Partially delivered in v3; current-state collector/reconciliation delta pending.** |

### Direct primary-source map

These pages were rechecked on 2026-09-02. Each row supports the adjacent product
boundary; repository files and tests, not these pages, support the shipped-core
claims.

| Capability boundary | Current primary sources |
| --- | --- |
| Cost attribution versus idle and cross-domain spend | [Attributing cost](https://docs.snowflake.com/en/user-guide/cost-attributing); [understanding overall cost](https://docs.snowflake.com/en/user-guide/cost-understanding-overall); [storage cost](https://docs.snowflake.com/en/user-guide/cost-understanding-data-storage); [data-transfer cost](https://docs.snowflake.com/en/user-guide/cost-understanding-data-transfer); [resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors); [monitor budgets](https://docs.snowflake.com/en/user-guide/budgets/monitor); [AI cost management and governance](https://docs.snowflake.com/en/user-guide/snowflake-cortex/governance-and-availability/ai-cost-management-and-governance); [Cortex AI Functions cost management](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-func-cost-management) |
| Query Insights and operator-statistics completion/window/privilege limits | [Query Insights](https://docs.snowflake.com/en/user-guide/query-insights); [`GET_QUERY_OPERATOR_STATS`](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats) |
| Role inheritance, managed access, direct grants, and future-grant precedence | [Access control overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview); [`GRANT ... TO ROLE` future-grant considerations](https://docs.snowflake.com/en/sql-reference/sql/grant-privilege) |
| Authentication methods, policy precedence, WIF, PAT, and rollout boundaries | [Authentication policies](https://docs.snowflake.com/en/user-guide/authentication-policies); [single-factor password deprecation](https://docs.snowflake.com/en/user-guide/security-mfa-rollout); [workload identity federation](https://docs.snowflake.com/en/user-guide/workload-identity-federation); [programmatic access tokens](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens) |
| Current task, stream, dynamic-table graph/state, pipe state, and dbt Project state | [`TASK_HISTORY`](https://docs.snowflake.com/en/sql-reference/account-usage/task_history); [stream staleness](https://docs.snowflake.com/en/user-guide/streams-intro#label-stream-staleness); [dynamic table reference](https://docs.snowflake.com/en/user-guide/dynamic-tables/reference); [`SYSTEM$PIPE_STATUS`](https://docs.snowflake.com/en/sql-reference/functions/system_pipe_status); [dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake); [manage dbt project objects](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake-manage) |
| Data-quality expectation status, anomaly training, notifications, and visibility privileges | [`DATA_QUALITY_MONITORING_EXPECTATION_STATUS`](https://docs.snowflake.com/en/sql-reference/functions/data_quality_monitoring_expectation_status); [anomaly detection and training](https://docs.snowflake.com/en/user-guide/data-quality-anomaly); [data-quality notifications](https://docs.snowflake.com/en/user-guide/data-quality-notifications); [data-quality access control](https://docs.snowflake.com/en/user-guide/data-quality-access-control) |
| Replication history versus current failover-group dependencies | [Monitoring replication and failover](https://docs.snowflake.com/en/user-guide/account-replication-monitor); [replication groups in BCDR](https://docs.snowflake.com/en/user-guide/account-replication-replication-groups) |
| Terraform, schemachange, behavior-change bundles, and dbt Project release state | [Snowflake Terraform provider roadmap](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/ROADMAP.md); [Snowflake-Labs schemachange canonical upstream (community-developed, not an official offering)](https://github.com/Snowflake-Labs/schemachange); [behavior-change management](https://docs.snowflake.com/en/release-notes/bcr-bundles/managing-behavior-change-releases); [dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake) |

## Approved additions: two jobs, no filler

Neither approved addition is present in the eight-skill v3 baseline. Approval grants
a bounded implementation slot only after its dependency-ready Bead is claimed and
its evidence contract is validated.

### `snowflake-governance-coverage-auditor`

**Trigger:** an operator must determine which governed sensitive assets lack
effective classification, tags, masking, row-access, projection, join, or aggregation
coverage. This is distinct from tracing who currently has access and from evaluating
data-quality expectations.

**Required output:** a denominator-based protection report containing uncovered
assets, policy-precedence conflicts, stale/pending/failed classification states,
edition and privilege blind spots, policy-simulation results, source timestamps, and
a dry-run remediation packet. It remains read-only.

Primary sources:

- [Tag-based policies](https://docs.snowflake.com/en/user-guide/tag-based-policies)
- [Monitor tags and masking policies](https://docs.snowflake.com/en/user-guide/object-tagging/monitor)
- [Classification troubleshooting](https://docs.snowflake.com/en/user-guide/classify-troubleshooting)

### `snowflake-native-app-release-sheriff`

**Trigger:** a Native App provider needs a release preflight before publishing or
promoting a version. This is distinct from generic infrastructure deployment review.

**Required output:** a non-mutating release packet covering manifest and setup-script
idempotence, privilege and App Spec deltas, security-scan state, version compatibility,
upgrade cohorts, rollback observables, and blocked-evidence findings. It never
publishes, upgrades, or promotes an app.

Primary sources:

- [Create the setup script](https://docs.snowflake.com/en/developer-guide/native-apps/creating-setup-script)
- [Run the automated security scan](https://docs.snowflake.com/en/developer-guide/native-apps/security-run-scan)
- [Develop a new app version](https://docs.snowflake.com/en/developer-guide/native-apps/update-app-develop)

## Rejected and deferred candidates

- Reject a generic observability-assurance skill: its trigger and evidence overlap
  query, pipeline, cost, data-quality, and failover workflows.
- Defer secure-sharing review until governance coverage establishes whether a
  distinct operator job remains.
- Defer Snowpark telemetry triage, SnowConvert reconciliation, and listing or
  auto-fulfillment operations until recurrence evidence justifies separate slots.
- Reject any tutorial, hello-world, generic checklist, static limits table, or
  vendor-SDK wrapper whose only benefit is catalog breadth.

This resolves the research gate in `claude-zhc5.9`: observability remains merged into
existing workflows, while privacy-policy engineering is narrowed to the approved
governance-coverage job. Its historical closure receipt points to the earlier decision
commit `67ac62641`; this record restates that outcome against the current v3 baseline
without claiming the approved addition is shipped.

## Delivery rule

The live Beads graph under `claude-na0m` owns sequencing and acceptance evidence.
Every future retained-skill upgrade or approved addition must remain model-neutral,
read-only by default, deterministic under fixtures, explicit about source freshness,
privileges, editions, truncation, and missing evidence, and independently reviewed
through the protected repository gates. Generated catalog, curated mirror, package,
and Freshie projections belong to the implementation PR that changes source; they do
not belong in this decision-only slice.
