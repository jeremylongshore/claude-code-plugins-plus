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
- Adaptive query metering is attribution beneath the all-warehouse aggregate, not an
  additional warehouse total.
- Cortex AI function detail is attribution beneath the `AI_SERVICES` metering total.
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
`privilege_error`, and `not_collected`. `documented_latency_hours` is evidence supplied
by the collection run after checking current Snowflake documentation; the analyzer
does not silently update or invent that boundary.

## Supplemental sources

| Dataset | Source | Operational boundary |
|---|---|---|
| `adaptive_usage` | `QUERY_METERING_HISTORY` | Region-limited; low-credit queries may be absent; NULL standard attribution is unknown. |
| `storage_usage` | `STORAGE_USAGE` | Daily bytes; different measurement semantics from billing storage. |
| `data_transfer_usage` | `DATA_TRANSFER_HISTORY` | Transfer bytes; currency requires contract and billing evidence. |
| `internal_transfer_usage` | `INTERNAL_DATA_TRANSFER_HISTORY` | Snowpark Container Services internal-transfer bytes. |
| `ai_usage` | `CORTEX_AI_FUNCTIONS_USAGE_HISTORY` | Detailed credits overlap the generic `AI_SERVICES` service total. |
| `resource_monitors` | `SHOW RESOURCE MONITORS` | Current-role visibility only; serverless and AI are outside resource-monitor control. |
| `budgets` | `SHOW SNOWFLAKE.CORE.BUDGET` | Inventory only; detailed configuration requires class methods outside this collector. |

Canonical read-only templates are named `cost-adaptive.sql`, `cost-storage.sql`,
`cost-transfer.sql`, `cost-internal-transfer.sql`, `cost-ai-functions.sql`,
`cost-resource-monitors.sql`, and `cost-budgets.sql` under the pack's shared evidence
directory. Keep each optional surface separate so an unavailable feature does not
erase evidence from the others.

Primary sources:

- [QUERY_METERING_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_metering_history)
- [STORAGE_USAGE](https://docs.snowflake.com/en/sql-reference/account-usage/storage_usage)
- [DATA_TRANSFER_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/data_transfer_history)
- [INTERNAL_DATA_TRANSFER_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/internal_data_transfer_history)
- [CORTEX_AI_FUNCTIONS_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_ai_functions_usage_history)
- [SHOW RESOURCE MONITORS](https://docs.snowflake.com/en/sql-reference/sql/show-resource-monitors)
- [SHOW BUDGET](https://docs.snowflake.com/en/sql-reference/classes/budget/commands/show-budget)

## Stable findings

- `COST_SURFACE_MISSING`, `COST_SURFACE_STALE`, `COST_SURFACE_TRUNCATED`
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
