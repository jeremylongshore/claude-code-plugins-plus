# Current failover-group and drill state

Use `scripts/sql/current-state.sql` with a least-privilege read-only role for
the group inventory and refresh-progress surface. `SHOW FAILOVER GROUPS` and
the Information Schema refresh-progress table function are current control-
plane evidence; `REPLICATION_GROUP_REFRESH_HISTORY` remains historical and
must carry its collection time, source, row count, and SQL/receipt hashes.

The analyzer accepts an optional current-state envelope:

```json
"current_state": {
  "status": "collected",
  "observed_at": "2026-08-31T17:55:00Z",
  "max_age_minutes": 30,
  "groups": [{
    "name": "DR",
    "refresh_status": "SUCCEEDED",
    "progress_status": "COMPLETED",
    "scheduled_interval_minutes": 30
  }]
}
```

Reconcile each in-scope group’s current refresh phase, progress, schedule,
suspension, and membership with the historical receipt. Missing or stale state,
group progress, cross-group dependencies, task/stream boundaries, dynamic-table
reinitialization, or target invariants remain `INCONCLUSIVE`/`NOT_READY`.

For operator-executed modes, every FAILOVER and FAILBACK event must include a
`receipt_sha256` over its canonical unsigned event object, plus explicit approval
and post-event validations. A successful login or refresh does not prove a
drill. Never execute refresh, promotion, failover, failback, redirect, resume,
or cancellation from this skill.
