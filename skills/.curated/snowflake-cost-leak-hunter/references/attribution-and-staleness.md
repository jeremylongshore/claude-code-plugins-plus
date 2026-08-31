# Attribution and staleness boundaries

Use this reference before interpreting Snowflake cost evidence. It records the
platform boundaries that change whether a number can be called observed usage,
estimated currency, or invoice truth.

## Source authority

Primary sources:

- [Attributing cost](https://docs.snowflake.com/en/user-guide/cost-attributing)
- [QUERY_ATTRIBUTION_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_attribution_history)
- [WAREHOUSE_METERING_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_metering_history)
- [Organization Usage](https://docs.snowflake.com/en/sql-reference/organization-usage)

Verify these pages when the behavior matters to a current production decision.
The operational rules below are a concise map, not a substitute for current docs.

## What each surface proves

### `SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY`

This view supplies hourly warehouse credit observations:

- `CREDITS_USED_COMPUTE` is warehouse compute credit usage.
- `CREDITS_USED_CLOUD_SERVICES` is cloud-services credit usage for the warehouse.
- `CREDITS_USED` is their sum before the daily cloud-services adjustment and can be
  greater than billed credits.
- `CREDITS_ATTRIBUTED_COMPUTE_QUERIES` is compute attributed to query execution and
  excludes warehouse idle time.

The documented idle-evidence calculation is:

```text
credits_used_compute - credits_attributed_compute_queries
```

Apply it only to aligned aggregation windows and non-NULL values. A positive result is
observed unattributed/idle compute for review; it is not automatically recoverable.
Adaptive Warehouses can return NULL for the attributed-query column, so do not coerce
NULL to zero.

Account Usage latency is documented as up to three hours for the view and up to six
hours for `CREDITS_USED_CLOUD_SERVICES`. Reader Account Usage can lag longer. Record the
maximum `END_TIME` actually returned.

### `SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY`

This view supplies per-query warehouse compute attribution:

- `CREDITS_ATTRIBUTED_COMPUTE` covers query execution, including weighted attribution
  under resizing/autoscaling and concurrent execution.
- `CREDITS_USED_QUERY_ACCELERATION` is separate; add it only when reporting total
  query-level acceleration usage.
- Attribution excludes warehouse idle time, storage, data transfer, cloud services,
  serverless features, and AI-token charges.
- Very short queries can be absent.
- Adaptive Warehouse jobs are excluded from this view and require their documented
  alternative surface.

The view can lag by up to eight hours. Do not use an incomplete recent window to
declare that usage stopped or a change saved money.

The view is available to roles with the documented `USAGE_VIEWER` or
`GOVERNANCE_VIEWER` Snowflake database role visibility. Do not broaden access simply
to complete an audit; report the missing surface and the role owner.

### Account vs organization surfaces

Do not join account and organization rows by display name alone. Preserve:

- organization name when present;
- account locator and account name;
- warehouse ID, not only warehouse name;
- UTC half-open window boundaries.

Organization Usage has separate availability, edition, organization-account, latency,
and premium-view constraints. Treat a missing organization row as unknown until the
correct organization account and feature availability are verified.

## Evidence labels

### Confirmed

Use `confirmed` for a value directly observed in a supplied Snowflake usage surface or
a deterministic sum/difference explicitly supported by that surface's documented
semantics. Always name the source and window.

Examples:

- warehouse compute credits returned by `WAREHOUSE_METERING_HISTORY`;
- query-attributed compute credits returned by `QUERY_ATTRIBUTION_HISTORY`;
- aligned warehouse compute minus attributed query compute.

Confirmed usage is still not necessarily a billed invoice amount.

### Estimated

Use `estimated` for currency conversion, extrapolation, modeling, or comparisons that
depend on a supplied assumption. Record:

- rate-card provenance;
- currency;
- effective period if known;
- which credit category the rate applies to;
- whether the result has been reconciled to an invoice.

Never substitute a public list price for the customer's contract without the user's
explicit request and a clear estimate label.

### At-risk

Use `at-risk` for an observed condition that may represent avoidable consumption or an
attribution/control gap, but still needs owner review.

Examples:

- warehouse compute not attributed to query execution;
- untagged query-attributed credits;
- serverless usage outside resource-monitor coverage;
- repeated high-credit query hashes without workload context.

Do not sum at-risk credits with confirmed total usage under a “savings” label.

## Freshness receipt

For every source, capture:

```text
source name
collection query ID
window start and end in UTC
maximum source timestamp returned
collection timestamp
observed age = collection timestamp - maximum source timestamp
documented latency boundary checked on current official docs
```

Report observed age numerically. The analyzer intentionally does not hard-code a
“stale” threshold because the relevant documented latency depends on the view and can
change.

## Invoice boundary

Usage views support investigation, chargeback, and optimization. Invoice reconciliation
requires the applicable usage statement, rate sheet/contract, adjustments, account and
organization scope, currency, and billing period. If those are absent, state:

> This report explains supplied usage evidence. It does not reconcile the Snowflake
> invoice.
