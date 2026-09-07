# Replay, idempotency, overlap, and skipped-run evidence

Read this when a task retry, Snowpipe replay, stream replacement, or dynamic-table
recovery is being considered.

## Required evidence

Retain task `RUN_ID` or `GRAPH_RUN_GROUP_ID`, `ATTEMPT_NUMBER`, `SCHEDULED_FROM`,
scheduled/completed/query times, and predecessor return/state. A `SKIPPED` run is
not a successful no-op: bound its missed interval and explain its `WHEN` or
predecessor condition. A scheduled interval that starts before the previous run
completes is an overlap candidate, not proof of duplicate writes.

For files/events, retain a stable file/event identity, business key, target
uniqueness or MERGE semantics, notification IDs, and the first retry/replay
boundary. Duplicate counts without a key are insufficient to prove correction.

## Decision boundary

`IDEMPOTENCY_UNPROVEN`, `DEDUPLICATION_UNVERIFIED`, and `REPLAY_RISK` are hard
holds: stop before replay and request the smallest read-only key-level and
partial-commit checks. Exactly-once delivery is never inferred from a green task,
pipe, or COPY status. After an approved replay, re-collect source/file history,
target keys, skipped intervals, and duplicate counts before declaring recovery.

Primary sources:

- [TASK_HISTORY](https://docs.snowflake.com/en/sql-reference/functions/task_history)
- [Task graphs](https://docs.snowflake.com/en/user-guide/tasks-graphs)
- [Snowpipe troubleshooting](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-ts)
