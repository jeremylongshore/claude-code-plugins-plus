# Current failover-group and drill state

Use the bundled collector with `--surface replication-current` and a
least-privilege read-only profile. Its reviewed
`scripts/sql/replication-current.sql` projects only the bounded group inventory
and refresh-progress fields; it does not expose account/owner columns or invoke
promotion/failback. `REPLICATION_GROUP_REFRESH_HISTORY` remains historical and
must carry its own collection time, source, row count, and SQL/receipt hashes.

The analyzer requires the complete collector object at root
`current_state_receipt`. The receipt must have exact schema/surface/status,
empty errors, exact source/template metadata, hashes of the bundled SQL for
`sql_sha256`, `template_sha256`, and `rendered_sql_sha256`, and a valid canonical
`receipt_sha256`. Its timestamp must be valid and no later than `as_of`; its row
cap, total count, per-dataset caps, truncation flags, and dataset names must match
the reviewed surface. Dataset rows must match the exact projected fields. Either
dataset reaching its SQL cap blocks readiness. `max_age_minutes` is bounded to
1-30 minutes and cannot be enlarged to make stale state pass.

Bind the current-state envelope directly to the receipt:

```json
"current_state": {
  "status": "collected",
  "observed_at": "2026-08-31T17:55:00Z",
  "max_age_minutes": 30,
  "groups": [{
    "name": "DR", "type": "FAILOVER", "object_types": "DATABASES",
    "replication_schedule": "30 MINUTE", "secondary_state": "STARTED",
    "next_scheduled_refresh": "2026-08-31T18:00:00Z"
  }],
  "progress": [{
    "group_name": "DR", "group_type": "FAILOVER", "phase_name": "COMPLETED",
    "start_time": "2026-08-31T17:50:00Z", "end_time": "2026-08-31T17:55:00Z",
    "progress": 100
  }]
}
```

`groups` must equal the receipt `failover_groups` dataset and `progress` must
equal `replication_progress`; `observed_at` must equal receipt `collected_at`.
Do not hand-normalize, omit, or append rows. Detail payloads and account
endpoints/identifiers are rejected rather than retained in evidence or reports.

Reconcile each in-scope group’s current refresh phase, progress, schedule,
suspension, and membership with the historical receipt. Missing or stale state,
group progress, cross-group dependencies, task/stream boundaries, dynamic-table
reinitialization, or target invariants remain `INCONCLUSIVE`/`NOT_READY`.

For operator-executed modes, every FAILOVER and FAILBACK event must include a
`receipt_sha256` over its canonical unsigned event object, plus explicit approval
and post-event validations. A successful login or refresh does not prove a
drill. Never execute refresh, promotion, failover, failback, redirect, resume,
or cancellation from this skill.
