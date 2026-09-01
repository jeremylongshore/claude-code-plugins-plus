# Current-state and history boundary

Use the bundled collector with `--surface pipeline-current` and the approved
read-only profile for a near-live control-plane snapshot. Its reviewed
`scripts/sql/pipeline-current.sql` template asks only for `SHOW TASKS`, `SHOW
STREAMS`, `SHOW DYNAMIC TABLES`, and `SHOW PIPES`; add no definitions, stage URLs,
notification endpoints, query text, or payloads.

The analyzer accepts a `current_state` envelope alongside the normal
`nodes`/`edges` snapshot. When it is supplied, its unmodified collector receipt
is required at the root as `current_state_receipt`:

```json
{
  "current_state": {
    "status": "collected",
    "observed_at": "2026-08-30T11:58:00Z",
    "max_age_minutes": 15,
    "complete": true,
    "nodes": [{"id": "ANALYTICS.OPS.ORDERS_TASK", "kind": "TASK", "status": "STARTED"}],
    "edges": [{"from": "ANALYTICS.OPS.ORDERS_STREAM", "to": "ANALYTICS.OPS.ORDERS_TASK"}]
  },
  "current_state_receipt": {"surface": "pipeline-current", "...": "unmodified collector receipt"}
}
```

`current_state.observed_at` must equal the receipt's `collected_at`; the fixed
freshness ceiling is 15 minutes and the declared `max_age_minutes` cannot exceed
it. The receipt must contain exactly `task_current`, `stream_current`,
`dynamic_table_current`, and `pipe_current`, stay below the analyzer's 10,000-row
safety cap, and report no truncation or collector errors. Each current node must
match exactly one receipt row by kind plus fully qualified name, unambiguous short
name, or the projected task ID, and its normalized status must agree. Missing IDs,
status drift, omitted rows, extra rows, and ambiguous names are evidence gaps.

The report returns only verification status, sanitized issues, and binding counts.
It does not echo current receipt rows, raw definitions, or notification endpoints.

Use `history` for bounded `TASK_HISTORY`, dynamic-table refresh history, and
`COPY_HISTORY` observations. Supply identified rows with `status`/`state` and
set `complete: true` only when the requested window and source visibility are
proven. The report marks stale, unavailable, incomplete, disconnected, or
current-versus-history disagreement as evidence gaps; none supports a health or
root-cause claim. Every task run needs a stable run/query identity, and every
stream, dynamic table, pipe, and task node must be represented before graph
completeness is claimed.

Account Usage is historical and may lag. Recollect current `SHOW` metadata and
partition a history window when the receipt reaches its limit. Keep source
timestamps, row counts, privilege gaps, and the exact SQL hash in the collector
receipt; never treat an empty result as absence or health.
