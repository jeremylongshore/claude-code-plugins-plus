# Current-state and history boundary

Use `scripts/sql/current-state.sql` with the approved read-only profile for a
near-live control-plane snapshot. It intentionally asks only for `SHOW TASKS`,
`SHOW STREAMS`, `SHOW DYNAMIC TABLES`, and `SHOW PIPES`; add no definitions,
stage URLs, query text, or payloads.

The analyzer accepts an optional `current_state` envelope alongside the normal
`nodes`/`edges` snapshot:

```json
{
  "status": "collected",
  "observed_at": "2026-08-30T11:58:00Z",
  "max_age_minutes": 15,
  "complete": true,
  "nodes": [{"id": "orders_task", "kind": "TASK", "status": "STARTED"}],
  "edges": [{"from": "orders_stream", "to": "orders_task"}]
}
```

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
