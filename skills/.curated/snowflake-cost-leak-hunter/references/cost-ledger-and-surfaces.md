# Typed cost ledger and supplemental surfaces

Use this reference when the audit includes Adaptive Warehouses, storage, transfer,
Cortex AI, budgets, or resource monitors. The baseline collector receipt remains the
authority for its four original datasets; each supplemental surface needs its own
availability and freshness receipt.

## Ledger rules

| Role | Additive | Meaning |
|---|---|---|
| `total` | yes | A bounded usage total within its overlap key and unit. |
| `attribution` | no | A child breakdown already represented by a parent total. |
| `context` | no | Operational evidence whose unit or semantics are not a cost total. |
| `estimate` | no | A supplied-rate conversion of a parent entry. |
| `invoice-only` | yes, only with invoice evidence | Billing truth not derivable from operational views. |

Entries with the same `overlap_key` must not contain multiple additive totals. In
particular:

- `QUERY_ATTRIBUTION_HISTORY` is attribution beneath warehouse compute, not additional
  compute.
- Adaptive `CREDITS_USED_COMPUTE` is attribution beneath the all-warehouse compute
  aggregate, not an additional warehouse total. Do not parent Adaptive
  `CREDITS_USED`, which also contains cloud-services credits, under a compute-only
  total.
- Cortex AI Functions detail uses `AI_FUNCTIONS` in Snowflake's general
  [service-type taxonomy](https://docs.snowflake.com/en/sql-reference/service-types),
  but its attribution parent in
  [`METERING_HISTORY`](https://docs.snowflake.com/en/sql-reference/account-usage/metering_history)
  is `AI_SERVICES`. Attach detail only when that parent, account, and window align.
  Do not assert equality: `AI_SERVICES` also covers Cortex Analyst and is broader than
  this detail surface.
- Generic `METERING_HISTORY` totals use the output domain
  `metering:<SERVICE_TYPE>`. The legacy analyzer input key `serverless_usage` is only
  a compatibility name; never repeat it as a product classification because the view
  also contains warehouse, cloud-services, and Openflow categories.
- Storage and transfer bytes remain context unless separate contract and invoice
  evidence provides a defensible billing entry.
- A currency estimate remains `estimate` even when its supplied rate was reconciled;
  it does not turn the operational credit row into an invoice total.
- Customer-supplied billing-statement rows use `invoice-only` and a distinct overlap
  key. Their presence does not prove reconciliation to operational usage unless the
  operator supplies that mapping separately.

## Surface denominator

Declare `metadata.expected_surfaces` and provide one `surface_inventory` row per
surface. Do not remove an unavailable surface from the denominator.

## Analyzer envelope and exact keys

Pass the collector's normalized rows without renaming their top-level keys:

| Evidence class | Exact top-level keys |
|---|---|
| Baseline datasets | `warehouse_metering`, `query_attribution`, `warehouse_load`, `serverless_usage` |
| Supplemental datasets | `adaptive_usage`, `storage_usage`, `data_transfer_usage`, `internal_transfer_usage`, `ai_usage` |
| Coverage and proof | `surface_inventory`, `collector_receipt`, `supplemental_receipts`, `source_max_times` |
| Controls and billing | `controls_inventory`, `invoice_usage`, `credit_rates` |

`serverless_usage` is the compatibility key for generic `METERING_HISTORY`, not a
serverless-only claim. `source_max_times` uses the four baseline dataset keys and is
descriptive activity evidence only; it cannot prove ingestion freshness.

Do not hand-build or trim receipts. Preserve `collected_at`,
`collection_started_at`, `collection_completed_at`, `source_views`, `sql_sha256`,
`template_sha256`, `rendered_sql_sha256`, `selector_fingerprint`, `result_sha256`,
`receipt_sha256`, row-count/cap fields, `truncation_possible`, and the complete
`datasets` object emitted by the reviewed collector. The baseline receipt belongs at
`collector_receipt`; each optional surface receipt belongs at
`supplemental_receipts.<dataset_key>`. `truncation_possible` must be exactly `false`
before that surface can support completeness.

The receipt's single `execution_context` row has an exact reviewed shape. Its
`account_identifier_sha256`, `collector_user_sha256`, `primary_role_sha256`, and
`secondary_roles_sha256` values are lowercase 64-hex digests; `session_timezone` is
`UTC`; and `observed_at` falls inside the collection interval. `primary_role_type`
must be `ROLE`, or `APPLICATION_INSTANCE` only in a native-app context.
`DATABASE_ROLE` is not a valid result of `CURRENT_ROLE_TYPE()`.

For query rows, keep `query_tag_present` boolean exactly aligned with the presence of
`query_tag_sha256`. Preserve optional `query_hash` and `query_parameterized_hash` only
as lowercase 64-hex organization/account-scoped digests. See
[warehouse and idle evidence](warehouse-and-idle-evidence.md) for the normalized row
example and rate-card shape. `controls_inventory` is an object with
`resource_monitors` and `budgets` arrays; `invoice_usage` remains invoice-only, and
`credit_rates` can create estimates but never prove reconciliation.

```json
{
  "surface": "adaptive_usage",
  "source": "SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY",
  "status": "region_unavailable",
  "privilege_status": "verified",
  "documented_latency_hours": "1",
  "latest_timestamp": null,
  "truncated": false
}
```

Accepted availability states are `available`, `unavailable`, `region_unavailable`,
`privilege_error`, and `not_collected`. A surface inventory row is an operator
assertion, not proof of source freshness, privilege completeness, or origin. A
self-checksum detects accidental alteration after collection but does not authenticate
the collector or Snowflake. The analyzer must compare the receipt to the fixed,
reviewed latency policy below; caller-supplied `documented_latency_hours` and
`latest_timestamp` never enlarge a settled window or establish freshness.

## Fixed latency and settled-window policy

All usage windows are half-open UTC intervals `[window_start, window_end)` and a single
collection bundle must not exceed seven days. Bind both
bounds, the collection time, account/organization identity, current role, session UTC
offset, SQL/template hash, result hash, row count, and cap state into each receipt. A
source can support a settled-window claim only when `window_end` is no later than the
same-statement `execution_context.observed_at` minus the applicable official maximum
latency. Do not use the later CLI completion time; the allowed collection interval
cannot make an unsettled window appear settled. For daily surfaces, use closed UTC
days. Do not infer staleness from the maximum activity timestamp: a
quiet but successfully queried surface can legitimately have no recent row.

| Surface or field | Fixed maximum latency / finality rule | Source |
|---|---|---|
| `WAREHOUSE_METERING_HISTORY`, excluding cloud-services field | 3 hours | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_metering_history) |
| `WAREHOUSE_METERING_HISTORY.CREDITS_USED_CLOUD_SERVICES` | 6 hours | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_metering_history) |
| `QUERY_ATTRIBUTION_HISTORY` | 8 hours | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/query_attribution_history) |
| `QUERY_HISTORY` enrichment | 45 minutes | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/query_history) |
| `WAREHOUSE_LOAD_HISTORY` | 3 hours; five-minute load intervals | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_load_history) |
| `METERING_HISTORY` | 3 hours; cloud-services fields 6 hours; `SNOWPIPE_STREAMING` credits 12 hours. Multiple entity rows can share a service/hour, so the reviewed collector sums credits by service and interval before its cap. | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/metering_history) |
| `QUERY_METERING_HISTORY` | 1 hour; in-progress rows remain mutable and are not final | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/query_metering_history) |
| `STORAGE_USAGE` | 2 hours | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/storage_usage) |
| `DATA_TRANSFER_HISTORY` | 2 hours | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/data_transfer_history) |
| `INTERNAL_DATA_TRANSFER_HISTORY` | 3 hours | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/internal_data_transfer_history) |
| `CORTEX_AI_FUNCTIONS_USAGE_HISTORY` | Running calls refresh every 2 minutes best effort with a 5-minute SLA. A query can span hourly rows and use multiple functions or models; it is final only when at least one row for the same query ID has `IS_COMPLETED=TRUE`, at which point every row for that query contributes usage. | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_ai_functions_usage_history) |
| `METERING_DAILY_HISTORY` | 3 hours | [Snowflake](https://docs.snowflake.com/en/sql-reference/account-usage/metering_daily_history) |
| `USAGE_IN_CURRENCY_DAILY` | 72 hours and mutable until month close | [Snowflake](https://docs.snowflake.com/en/sql-reference/organization-usage/usage_in_currency_daily) |
| `RATE_SHEET_DAILY` | 24 hours and mutable until month close | [Snowflake](https://docs.snowflake.com/en/sql-reference/organization-usage/rate_sheet_daily) |

`SHOW` commands do not publish an Account Usage-style latency SLA. Treat them as a
current, role-scoped observation at collection time, not as proof of historical
enforcement or account-wide visibility.

## Supplemental sources

| Dataset | Source | Operational boundary |
|---|---|---|
| `adaptive_usage` | `QUERY_METERING_HISTORY` | GA only in select AWS regions; low/zero-credit queries may be absent; in-progress rows mutate; use compute credits beneath a compute parent. |
| `storage_usage` | `STORAGE_USAGE` | Daily average-byte snapshots converted across non-overlapping intervals to `byte-days`, not summed and mislabeled as bytes; different measurement semantics from billing storage; include applicable standard, stage, Fail-safe, hybrid, archive cool/cold, and retrieval-temporary fields. |
| `data_transfer_usage` | `DATA_TRANSFER_HISTORY` | Transfer bytes in a `VARIANT`; current transfer types include external, cross-region, internal, Postgres, and SPCS activity; currency requires billing evidence. |
| `internal_transfer_usage` | `INTERNAL_DATA_TRANSFER_HISTORY` | Snowpark Container Services internal-transfer bytes. |
| `ai_usage` | `CORTEX_AI_FUNCTIONS_USAGE_HISTORY` | AI Functions only, with data beginning 2026-01-05 and identity/tag/role fields beginning 2026-02-16; not an exhaustive Cortex/AI cost surface. The general taxonomy label is `AI_FUNCTIONS`; its broader `METERING_HISTORY` parent, when present and aligned, is `AI_SERVICES`, which also covers Cortex Analyst. |
| `resource_monitors` | `SHOW RESOURCE MONITORS` | Current-role visibility only and an intrinsic 10,000-row SHOW cap. `LEVEL` proves assignment, not configured actions. Resource monitors cover warehouses, including Adaptive Warehouses, but not serverless or AI services. |
| `budgets` | `SHOW SNOWFLAKE.CORE.BUDGET` | Visible custom-budget instance inventory only; it does not prove account-root activation, spending limit, notifications, linked resources, refresh tier, or actions. |

Canonical read-only templates are named `cost-adaptive.sql`, `cost-storage.sql`,
`cost-transfer.sql`, `cost-internal-transfer.sql`, `cost-ai-functions.sql`,
`cost-resource-monitors.sql`, and `cost-budgets.sql` under the pack's shared evidence
directory. Keep each optional surface separate so an unavailable feature does not
erase evidence from the others.

Run those names through `scripts/collect_snowflake_evidence.py --surface <name>` and
store the returned envelopes in `supplemental_receipts`, keyed by the dataset name in
the table above. `surface_inventory` is an operator assertion; it becomes verified
evidence only when the analyzer binds it to the matching source, template SHA-256,
normalized dataset rows, collection time, row cap, and canonical receipt SHA-256.
Even then, the receipt is locally self-consistent evidence, not cryptographic proof of
Snowflake origin. A caller-added field that was not emitted by the reviewed SQL is
untrusted and must not establish budget coverage, monitor enforcement, freshness, or
invoice reconciliation.

## AI, controls, and privacy boundaries

`CORTEX_AI_FUNCTIONS_USAGE_HISTORY` is not an account-wide AI denominator. Current
Snowflake cost guidance lists separate usage surfaces and service types for Agents,
Search, CoWork, Code, REST inference, guardrails, and other AI capabilities. Either
declare those surfaces separately or state that the report covers AI Functions only.
See [AI cost management and governance](https://docs.snowflake.com/en/user-guide/snowflake-cortex/governance-and-availability/ai-cost-management-and-governance).
Determine finality by query ID. Include every hourly function/model/warehouse row for
that query when any row has `IS_COMPLETED=TRUE`; quarantine the entire query only when
all its rows are in progress. Function, model, and warehouse remain attribution
dimensions, not independent finality boundaries.

`SHOW RESOURCE MONITORS` lists only objects visible to the current role. A non-NULL
`LEVEL` means a monitor is assigned; enforcement additionally requires a configured
action. Resource monitors are not precise hard limits, do not control serverless or AI
services, and cannot suspend cloud-services usage. See
[Working with resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors).

`SHOW SNOWFLAKE.CORE.BUDGET` lists visible class instances but cannot establish
coverage. The special account budget is configured through
`SNOWFLAKE.LOCAL.ACCOUNT_ROOT_BUDGET`; ordinary budget refresh is up to 6.5 hours or
one hour in low-latency mode. Do not infer coverage from operator-supplied domain names.
See [Budgets](https://docs.snowflake.com/en/user-guide/budgets) and
[Account budget](https://docs.snowflake.com/en/user-guide/budgets/account-budget).

Hash customer-controlled warehouse, compute-pool, budget, owner, user, tag, model, and
account display names before export. The evidence metadata must explicitly set
`identity_disclosure_authorized`. Raw display text in `account`, `role`,
`review_owner`, or `approval_boundary` is accepted only when that value is `true` and
the trusted-digest-bound `identity_disclosure_authority` names who authorized it. With
authorization `false`, all four fields must be lowercase 64-hex scoped digests and the
authority must be absent. Prefer an organization-and-account-scoped hash so equal
names in different accounts are not linkable. Query text, notification addresses,
contract numbers, credentials, connection values, and raw tags or user names never
belong in the normal evidence packet.

## Billing and invoice levels

Keep three evidence levels distinct:

1. Hourly operational usage (`WAREHOUSE_METERING_HISTORY`, `METERING_HISTORY`, and
   detailed attribution views) is useful for investigation but precedes the daily
   cloud-services adjustment.
2. `METERING_DAILY_HISTORY.CREDITS_BILLED` incorporates the daily cloud-services
   adjustment and is billed-credit evidence, not customer-currency invoice truth.
3. `ORGANIZATION_USAGE.USAGE_IN_CURRENCY_DAILY`, optionally corroborated with
   `RATE_SHEET_DAILY`, supports usage-statement reconciliation. It is access-sensitive,
   unavailable to some reseller customers, delayed, and mutable until month close; the
   issued invoice or usage statement remains authoritative.

Follow Snowflake's [billing reconciliation guide](https://docs.snowflake.com/en/user-guide/billing-reconcile).
Customer-supplied statement rows and rate cards remain unverified assertions unless
their provenance and exact account, contract, currency, service, adjustment, and
billing-period mapping are separately established.

Primary sources:

- [QUERY_METERING_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_metering_history)
- [STORAGE_USAGE](https://docs.snowflake.com/en/sql-reference/account-usage/storage_usage)
- [DATA_TRANSFER_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/data_transfer_history)
- [INTERNAL_DATA_TRANSFER_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/internal_data_transfer_history)
- [CORTEX_AI_FUNCTIONS_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_ai_functions_usage_history)
- [SHOW RESOURCE MONITORS](https://docs.snowflake.com/en/sql-reference/sql/show-resource-monitors)
- [SHOW BUDGET](https://docs.snowflake.com/en/sql-reference/classes/budget/commands/show-budget)
- [METERING_DAILY_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/metering_daily_history)
- [USAGE_IN_CURRENCY_DAILY](https://docs.snowflake.com/en/sql-reference/organization-usage/usage_in_currency_daily)
- [RATE_SHEET_DAILY](https://docs.snowflake.com/en/sql-reference/organization-usage/rate_sheet_daily)

## Stable findings

- `COST_SURFACE_MISSING`, `COST_SURFACE_STALE`, `COST_SURFACE_TRUNCATED`,
  `COST_SURFACE_RECEIPT_INVALID`
- `COST_DOUBLE_COUNT_RISK`, `COST_INVOICE_ONLY`, `COST_UNATTRIBUTABLE`
- `COST_ESTIMATE_UNPRICED`, `COST_TAG_COVERAGE_GAP`
- `COST_RESOURCE_MONITOR_COVERAGE_GAP`, `COST_BUDGET_COVERAGE_GAP`,
  `COST_SERVERLESS_MONITOR_GAP`
- `COST_ADAPTIVE_REGION_UNAVAILABLE`, `COST_ADAPTIVE_ATTRIBUTION_GAP`
- `COST_AI_ATTRIBUTION_GAP`, `COST_EXPERIMENT_ROLLBACK_UNBOUNDED`

Missing, stale, truncated, unsupported, or privilege-hidden evidence blocks a complete
claim. It never becomes a zero-valued ledger entry.

## Experiment rollback

A right-sizing proposal is bounded only when its input includes the current size,
finite candidate set, maximum size steps, aligned measurement window, success
criterion, rollback size, and operator-supplied numeric rollback thresholds. The
analyzer records those thresholds and always sets automatic execution to false. It
does not invent a percentage, execute a resize, or decide that the measured credits
are recoverable savings.
