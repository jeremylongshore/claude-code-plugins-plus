# Snowflake pipeline evidence map

Use this reference when collecting the snapshot consumed by
`scripts/analyze_pipeline_state.py`. The commands below are read-only. Replace
identifiers with fully qualified names and keep the time window explicit. A
missing row is an unknown, not a healthy result.

## Tasks and task graphs

Snowflake creates tasks suspended. Query both object state and run history before
concluding that a task is broken. A child can be skipped because a predecessor did
not complete, and a graph can become suspended after consecutive failures.

```sql
SHOW TASKS IN ACCOUNT;

SELECT name, state, scheduled_time, query_id, error_code, error_message,
       completed_time
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
  SCHEDULED_TIME_RANGE_START => DATEADD('hour', -24, CURRENT_TIMESTAMP())
))
ORDER BY scheduled_time DESC;

SELECT *
FROM TABLE(INFORMATION_SCHEMA.TASK_DEPENDENTS(
  TASK_NAME => 'DB.SCHEMA.ROOT_TASK', RECURSIVE => TRUE
));
```

Capture `state`, `error_code`, `error_message`, `query_id`, and predecessor
relationships. Do not infer a retry is safe from a transient-looking message;
first determine whether the task body is idempotent and whether a previous run
committed partial work.

Primary documentation: [Troubleshooting tasks](https://docs.snowflake.com/en/user-guide/tasks-ts)
and [task graphs](https://docs.snowflake.com/en/user-guide/tasks-graphs).

## Streams

Inspect the stream definition and staleness indicators. A stream becomes stale
when its offset falls outside the source's retained change history. A stale stream
cannot be made current by a blind retry; plan a replacement and a bounded,
idempotent backfill after confirming the source retention boundary.

```sql
SHOW STREAMS IN SCHEMA DB.SCHEMA;
DESCRIBE STREAM DB.SCHEMA.ORDERS_STREAM;
```

Record `stale`, `stale_after`, source object, append-only mode, and the last
successful consumer run. If the source was replaced with `CREATE OR REPLACE`,
the source identity and change history may no longer match the stream. Treat that
as a separate object-identity/schema event, not ordinary lag.

Primary documentation: [Streams introduction](https://docs.snowflake.com/en/user-guide/streams-intro)
and [stream staleness](https://docs.snowflake.com/en/user-guide/streams-manage#label-streams-stale).

## Dynamic tables

Use `SHOW DYNAMIC TABLES` for scheduling state, target lag, current lag, refresh
mode, and refresh-mode reason. Use refresh history and graph history for the
dependency chain. Graph order narrows investigation but does not prove causality.
Information Schema functions retain a shorter window than Account
Usage views, so record which source and window were used.

```sql
SHOW DYNAMIC TABLES LIKE 'DT_ORDERS' IN SCHEMA DB.SCHEMA;

SELECT name, state, state_message, refresh_trigger, refresh_action,
       data_timestamp, refresh_start_time, refresh_end_time, query_id
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  NAME => 'DB.SCHEMA.DT_ORDERS', ERROR_ONLY => FALSE
))
ORDER BY refresh_start_time DESC;

SELECT *
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_GRAPH_HISTORY())
WHERE qualified_name = 'DB.SCHEMA.DT_ORDERS';
```

`TARGET_LAG` is a freshness goal, not a guaranteed interval. A table whose
refresh duration exceeds its target cannot meet that goal by configuration alone;
separate a lag breach from an upstream failure. If incremental refresh reports
missing change tracking or time-travel history, preserve the DDL and identify the
required full reinitialization before proposing any change.

Primary documentation: [dynamic table monitoring](https://docs.snowflake.com/en/user-guide/dynamic-tables-tasks-monitor),
[refresh troubleshooting](https://docs.snowflake.com/en/user-guide/dynamic-tables/troubleshooting),
and [target lag](https://docs.snowflake.com/en/user-guide/dynamic-tables-target-lag).

## Snowpipe

`SYSTEM$PIPE_STATUS` is the first evidence source for event-driven loading. Keep
the raw JSON: timestamps such as the last received message and last forwarded
message distinguish a cloud-notification/path gap from a COPY or file-format
failure. Then correlate to `COPY_HISTORY` and the configured stage/prefix.

```sql
SELECT SYSTEM$PIPE_STATUS('DB.SCHEMA.ORDERS_PIPE');

SELECT file_name, last_load_time, status, row_count, first_error_message
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  TABLE_NAME => 'DB.SCHEMA.ORDERS',
  START_TIME => DATEADD('hour', -24, CURRENT_TIMESTAMP())
))
ORDER BY last_load_time DESC;
```

Do not replay a file until its load identity and target key are known. Snowpipe
may report the same file as already loaded, while downstream tasks can still
duplicate rows if the transformation is not idempotent.

Primary documentation: [Troubleshooting Snowpipe](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-ts),
[SYSTEM$PIPE_STATUS](https://docs.snowflake.com/en/sql-reference/functions/system_pipe_status),
and [COPY_HISTORY](https://docs.snowflake.com/en/sql-reference/functions/copy_history).
