# Snowflake pipeline evidence map

Use only the six reviewed templates bundled with this skill. Each template is a
single read-only statement with a same-statement execution-context row. Do not
replace an explicit projection with a wildcard, paste raw command output into a bundle, or
add names, SQL text, free-text errors, paths, endpoints, integrations, owners, or
roles.

## Surface map

| Surface | Reviewed source | Output scope | Fixed bound |
| --- | --- | --- | --- |
| `pipeline` | Account Usage `TASK_HISTORY`, `DYNAMIC_TABLE_REFRESH_HISTORY`, `COPY_HISTORY` | Explicit half-open UTC history | Window at most 7 days; 5,000 rows per history dataset |
| `pipeline-task-current` | `SHOW TASKS IN ACCOUNT` | Current role-visible tasks | 10,000 tasks |
| `pipeline-stream-current` | `SHOW STREAMS IN ACCOUNT` | Current role-visible streams | 10,000 streams |
| `pipeline-dynamic-table-current` | `SHOW DYNAMIC TABLES IN ACCOUNT` | Current role-visible dynamic tables | 10,000 dynamic tables |
| `pipeline-pipe-current` | `SHOW PIPES IN ACCOUNT` | Current role-visible pipes | 10,000 pipes |
| `pipeline-pipe-status` | `SYSTEM$PIPE_STATUS` for one validated pipe selector | One privacy-projected status row | Exactly one row per selected pipe |

The first five surface types occur exactly once. Repeat `pipeline-pipe-status`
exactly once for every `object_key_sha256` returned by `current_pipes`. If the
current pipe inventory is empty, supply no status receipt. Any missing, duplicate,
or orphan status receipt blocks completeness.

## History window and settlement

Collect `pipeline` with canonical UTC `--window-start` and exclusive
`--window-end` selectors. The collector rejects missing, reversed, non-UTC, or
longer-than-seven-day windows. It records `window_semantics: HALF_OPEN_UTC` and
the selector fingerprint plus the non-sensitive window values needed to
recompute the rendered-query digest. Raw identity selectors are never retained.

Account Usage is delayed. The reviewed query and analyzer use conservative
cutoffs:

- task history: observation time minus 45 minutes;
- dynamic-table refresh history: observation time minus 3 hours;
- copy history: observation time minus 48 hours.

Each dataset reads `[window_start, min(window_end, cutoff))` using task
`COMPLETED_TIME`, non-executing refresh `REFRESH_END_TIME`, or copy
`LAST_LOAD_TIME`. Execution context records the resulting
`*_settled_through_utc`. A requested interval beyond that value remains
unsettled. A schedule/start timestamp cannot pull a recently completed or
executing event into settled evidence. A missing row in the unsettled tail
cannot prove no run, refresh, copy, error, or duplicate occurred.

The 5,000-row history cap applies independently to each history dataset. A
dataset at its cap is incomplete even if the other datasets are small. Narrow or
partition the requested window; never infer absence from a capped result.

## Current inventories

The four `SHOW` surfaces project only account-scoped pseudonymous object/source
keys and reviewed states, timestamps, booleans, counts, and enums. They omit raw
names and sensitive metadata exposed by the underlying commands. Each current
inventory is role-visible, not inherently account-complete. A result of exactly
10,000 objects is capped and unusable for completeness. An empty result means
only that the bound role saw no rows at that observation.

For streams, projected `stale: true` means **may be stale**, not confirmed
staleness; `stale_after` can also be inaccurate in documented cases. Preserve
the boundary and require authorized verification. Do not invoke
`SYSTEM$STREAM_HAS_DATA`: Snowflake documents that calling it can prevent an
empty stream from becoming stale, so it is not observationally neutral.

For dynamic tables, the current projection omits raw `target_lag` text. Use the
numeric `target_lag_sec` from settled refresh history as a freshness goal, not
a guaranteed refresh interval. Compare scheduling/data timestamps with settled
refresh history; neither surface alone establishes health or cause.

## Pipe status

The pipe-status template accepts one validated three-part unquoted identifier as
a local CLI selector. A successful receipt exposes only selector
presence/fingerprint and the same account-scoped `object_key_sha256` used by the
pipe inventory. Its `rendered_sql_sha256` covers a receipt-only rendering where
the raw selector is replaced by that scoped hash; the analyzer recomputes it. If
collection fails before the scoped hash exists, the error receipt records the
reviewed template digest and a null selector fingerprint. Raw
`SYSTEM$PIPE_STATUS` JSON never leaves Snowflake.

The projection includes bounded state, counts, and timestamps needed to
distinguish queueing, notification, load, and failover observations. It excludes
file paths, file names, channel names, integration endpoints, `error`, `fault`,
and other free text. `execution_state` must be in Snowflake's documented finite
domain; unknown values invalidate the receipt and are never echoed. Even a fully
covered pipe inventory does not prove cloud delivery, target idempotence, or
absence of a recent copy while COPY_HISTORY is unsettled.

For copy history, `Partially loaded`, `Load failed`, and `Load skipped` remain
distinct findings. `ERROR_COUNT` is evaluated; a partial load is never normalized
to success. Snowpipe rows correlate through `pipe_identifier_sha256`. Bulk
`COPY INTO` rows have no pipe identity and remain separate copy-load nodes.

## Context and trust

Every receipt must contain exactly one `execution_context` with lowercase
SHA-256 values for organization, account, collector user, primary role, and
secondary roles; a primary-role type of `ROLE` or `APPLICATION_INSTANCE`; UTC
timezone; and an observation inside its collection interval. All receipt contexts must match and their
observations must span no more than 15 minutes.

The analyzer checks the reviewed template binding, recorded rendered-SQL digest,
normalized result, receipt digest,
dataset names/counts, caps, collection mode, freshness, and context. These checks
establish self-consistency only. A separately recorded digest of the complete
canonical bundle is required for trusted-input status, and even that digest is
an operator assertion of byte identity rather than proof of Snowflake origin.

Primary documentation:

- [TASK_HISTORY Account Usage view](https://docs.snowflake.com/en/sql-reference/account-usage/task_history)
- [DYNAMIC_TABLE_REFRESH_HISTORY Account Usage view](https://docs.snowflake.com/en/sql-reference/account-usage/dynamic_table_refresh_history)
- [COPY_HISTORY Account Usage view](https://docs.snowflake.com/en/sql-reference/account-usage/copy_history)
- [SHOW TASKS](https://docs.snowflake.com/en/sql-reference/sql/show-tasks)
- [SHOW STREAMS](https://docs.snowflake.com/en/sql-reference/sql/show-streams)
- [SHOW DYNAMIC TABLES](https://docs.snowflake.com/en/sql-reference/sql/show-dynamic-tables)
- [SHOW PIPES](https://docs.snowflake.com/en/sql-reference/sql/show-pipes)
- [SYSTEM$PIPE_STATUS](https://docs.snowflake.com/en/sql-reference/functions/system_pipe_status)
