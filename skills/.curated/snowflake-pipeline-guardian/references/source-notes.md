# Research notes and official sources

Reviewed against the live Snowflake documentation on 2026-09-03. Product syntax,
latency, limits, and privilege behavior can change; re-check these primary pages
before changing a reviewed SQL template or operational boundary.

The skill addresses cross-surface pipeline incidents: stale streams, suspended
or skipped task graphs, dynamic-table scheduling and refresh failures, Snowpipe
queue/notification/load gaps, and duplicate-risk decisions. Snowflake primary
documentation is authoritative for platform behavior. Incident-specific claims
require the schema-2 receipts and separate trusted bundle digest; community
material is discovery-only.

## Current control plane

- [SHOW TASKS](https://docs.snowflake.com/en/sql-reference/sql/show-tasks) — task
  state and reviewed scheduling mode. The bundled projection omits raw schedule
  and target-completion text, names, owners, definitions, conditions,
  integrations, and execute-as users.
- [SHOW STREAMS](https://docs.snowflake.com/en/sql-reference/sql/show-streams) —
  staleness and source metadata. Snowflake defines `stale: true` as “may be
  stale” and documents cases where `stale_after` is inaccurate. The projection
  uses these observations and scoped hashes rather than raw names.
- [Managing streams](https://docs.snowflake.com/en/user-guide/streams-manage) —
  retention and staleness behavior, including the warning that
  `SYSTEM$STREAM_HAS_DATA` can prevent an empty stream from becoming stale.
- [SHOW DYNAMIC TABLES](https://docs.snowflake.com/en/sql-reference/sql/show-dynamic-tables)
  — scheduling state, refresh mode, and data timestamp. Raw target-lag text,
  free-text reasons/codes, warehouse, owner, and execute-as identity are
  excluded; settled history retains numeric `target_lag_sec`.
- [SHOW PIPES](https://docs.snowflake.com/en/sql-reference/sql/show-pipes) —
  role-visible pipe inventory and its fixed 10,000-row ceiling. Definition,
  pattern, notification channel, integration, owner, comments, and free-text
  invalid reason are excluded.
- [SYSTEM$PIPE_STATUS](https://docs.snowflake.com/en/sql-reference/functions/system_pipe_status)
  — selected-pipe status. The reviewed template extracts only bounded state,
  count, and timestamp fields; raw JSON, paths, channels, errors, and faults do
  not leave the statement. The analyzer accepts only the documented finite
  execution-state domain.
- [CURRENT_ROLE_TYPE](https://docs.snowflake.com/en/sql-reference/functions/current_role_type)
  — the primary role type is `ROLE` or, inside a Native App,
  `APPLICATION_INSTANCE`; arbitrary role-type text is rejected.

## Settled history

- [TASK_HISTORY Account Usage](https://docs.snowflake.com/en/sql-reference/account-usage/task_history)
  — completed task-run history with documented latency up to 45 minutes. The
  reviewed window is based on `COMPLETED_TIME`, not schedule time. The reviewed
  terminal state domain is `SUCCEEDED`, `FAILED`,
  `FAILED_AND_AUTO_SUSPENDED`, `CANCELLED`, and `SKIPPED`; the auto-suspension
  state is also documented in Snowflake's
  [TASK_HISTORY behavior-change notice](https://docs.snowflake.com/en/release-notes/bcr-bundles/2023_01/bcr-899).
- [DYNAMIC_TABLE_REFRESH_HISTORY Account Usage](https://docs.snowflake.com/en/sql-reference/account-usage/dynamic_table_refresh_history)
  — refresh history with documented latency up to 3 hours. `EXECUTING` rows are
  mutable, so reviewed settled history requires a non-null `REFRESH_END_TIME`.
  After that settled filter, the reviewed state domain is `SUCCEEDED`, `FAILED`,
  `CANCELLED`, and `UPSTREAM_FAILED`; `SCHEDULED` and `SKIPPED` belong to a
  different Information Schema table-function surface and are not admitted.
- [COPY_HISTORY Account Usage](https://docs.snowflake.com/en/sql-reference/account-usage/copy_history)
  — load history. Snowflake documents typical latency up to 2 hours and a
  possible 2-day delay for low-activity tables; the reviewed contract therefore
  settles at 48 hours.
- [Account Usage overview](https://docs.snowflake.com/en/sql-reference/account-usage)
  — view availability, latency, retention, and database-role references.

The history template uses explicit `[window_start, window_end)` UTC selectors,
a maximum seven-day requested interval, conservative per-view settlement
cutoffs, explicit columns, scoped identity hashes, and a 5,000-row cap for each
dataset. It never selects query text, raw query IDs, state/error messages, file or
stage names, or customer data.

## Diagnostic semantics

- [Task graph troubleshooting](https://docs.snowflake.com/en/user-guide/tasks-ts)
- [Task graphs](https://docs.snowflake.com/en/user-guide/tasks-graphs)
- [Dynamic-table monitoring](https://docs.snowflake.com/en/user-guide/dynamic-tables-tasks-monitor)
- [Dynamic-table troubleshooting](https://docs.snowflake.com/en/user-guide/dynamic-tables/troubleshooting)
- [Dynamic-table target lag](https://docs.snowflake.com/en/user-guide/dynamic-tables-target-lag)
- [Snowpipe troubleshooting](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-ts)

These pages support diagnosis but do not authorize mutation. Dependency order,
status disagreement, or a green retry is not proof of causality or recovery.
