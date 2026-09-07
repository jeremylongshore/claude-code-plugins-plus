# Pipeline recovery matrix

This is a decision aid, not an execution script. Every recommendation remains
read-only until an operator separately approves and runs a reviewed SQL change.
The evidence snapshot and the analyzer report are the incident receipt.

| Finding | Confirm before changing anything | Ordered recovery | Data-safety boundary |
| --- | --- | --- | --- |
| `STREAM_STALE` | `DESCRIBE STREAM`, source retention, last consumer offset, source object identity | Stop new consumers; preserve source definition; create a replacement plan; backfill from a known source boundary into an idempotent target; validate counts/keys; cut over | Recreating a stale stream loses unconsumed change records. Never promise zero loss without a retained source or replayable raw files |
| `CHANGE_TRACKING_MISSING` | Dynamic table refresh history error, base-table DDL, change-tracking and retention window | Capture `GET_DDL`; restore/repair the original source identity if possible; otherwise schedule a full reinitialization and downstream validation | Incremental history may be unavailable. A full refresh can reprocess all source data and consume substantial compute |
| `SCHEMA_DRIFT` | Producer/consumer columns, types, policies, query id, whether replacement dropped object identity | Choose additive evolution or explicit migration; stage a compatibility view; validate downstream contracts; change definition in place where supported | `CREATE OR REPLACE` can change object identity and invalidate stream/change-tracking consumers. Do not use it as a generic schema edit |
| `LAG_BREACH` | Actual lag, target lag, refresh duration, queueing, warehouse load, upstream graph state | Fix the first upstream failure; if healthy, compare work duration to target, then right-size/serialize/partition and retest | Target lag is best effort. Raising the target hides an SLO change; it does not make data fresher |
| `TASK_SUSPENDED` / `TASK_FAILED` | Root/child state, predecessor result, error/query id, partial commits | Suspend scheduling only with approval; fix the first failed predecessor; use a bounded retry or replay plan; verify downstream invariants | A retry can duplicate side effects. `EXECUTE TASK ... RETRY LAST` is not a substitute for idempotence evidence |
| `PIPE_NOTIFICATION_GAP` | Pipe status timestamps, cloud queue delivery, stage URL/prefix, integration permissions | Repair routing/prefix; verify a test event reaches the pipe; reconcile missing files from source inventory | Replaying blindly can duplicate loads; preserve file names, checksums, and load history |
| `PIPE_LOAD_FAILURE` | Error notification, COPY history, file format/schema, target privileges | Quarantine bad files; correct the producer or file format; replay only after dedupe/key behavior is proven | Do not discard a failed file or mark it loaded without a durable reconciliation record |
| `DUPLICATE_DELIVERY` | Natural key, batch/file identity, retry history, target merge semantics | Stop replay; identify the first duplicate boundary; deduplicate using the business key and event identity; then reprocess bounded input | “Exactly once” is not inferred from Snowpipe/task success. Prove it at the target table |

## Dependency traversal

Start at the user-visible symptom and walk the dependency graph upstream. The
first failed predecessor is a recovery candidate. A downstream failed
dynamic table or task often only reports the consequence of a stale stream,
missing change history, or a notification gap. If graph evidence is incomplete,
report the uncertainty and ask for the missing object history; do not invent a
root cause. Dependency order alone is not causal proof.

The analyzer emits every supplied dependency chain with the earliest upstream
node first and labels the ordering as not-proven causality. It preserves dangling
edges instead of silently dropping them. It
does not claim that a healthy-looking upstream node is proven healthy: lack of a
finding means only that the input had no matching signal.

## Post-fix invariants

Before declaring recovery complete, collect new evidence for all of these:

1. The source-to-target graph is complete and no stream is stale.
2. Every incremental consumer can see the required source history window.
3. Task predecessors complete in order and no graph is silently suspended.
4. Dynamic-table actual lag is within the acknowledged freshness objective.
5. Pipe status, file inventory, COPY history, and target business keys reconcile.
6. The replay window, skipped records, duplicate count, and operator approvals are recorded.

Read [Snowflake task troubleshooting](https://docs.snowflake.com/en/user-guide/tasks-ts),
[dynamic-table troubleshooting](https://docs.snowflake.com/en/user-guide/dynamic-tables/troubleshooting),
and [Snowpipe troubleshooting](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-ts)
when a finding maps to those surfaces.
