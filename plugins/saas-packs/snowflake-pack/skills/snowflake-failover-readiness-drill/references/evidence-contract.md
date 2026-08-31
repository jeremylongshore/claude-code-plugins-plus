# Evidence contract

The analyzer accepts one JSON object. Timestamps must be timezone-aware ISO 8601.
Use `as_of` as the deterministic evaluation clock.

```json
{
  "schema_version": "1",
  "as_of": "2026-08-31T18:00:00Z",
  "mode": "READ_ONLY_PREFLIGHT",
  "edition": "BUSINESS_CRITICAL",
  "objectives": {"rpo_minutes": 60, "rto_minutes": 30},
  "groups": [{
    "name": "DR_CORE", "kind": "FAILOVER", "role": "SECONDARY",
    "secondary_present": true, "suspended": false,
    "refresh_status": "SUCCEEDED",
    "last_successful_refresh_at": "2026-08-31T17:30:00Z",
    "scheduled_interval_minutes": 30
  }],
  "dependencies": [],
  "object_checks": [],
  "target_validations": [{"name": "orders-count", "status": "PASS"}],
  "client_redirect": {"tested": true},
  "privileges": {"observable": true, "missing": []},
  "history": {
    "account_usage_collected_at": "2026-08-31T17:45:00Z",
    "detailed_window_days": 14
  },
  "drill_events": []
}
```

Allowed modes are `PLAN_ONLY`, `READ_ONLY_PREFLIGHT`,
`OPERATOR_EXECUTED_FAILOVER`, and `OPERATOR_EXECUTED_FAILOVER_AND_FAILBACK`.
Execution modes describe events already performed by an authorized operator;
they never cause the analyzer to execute anything.

`dependencies` rows use `from_group`, `to_group`, and `status`; an unknown group
is dangling and a dependency across two known groups is a cross-group risk.
`object_checks` rows use `object`, `task_stream_split`, `task_owner_valid`,
`stream_state` (`CURRENT`, `STALE`, `DUPLICATE_RISK`, `TIME_TRAVEL_RISK`), and
`dynamic_table_reinitialize`. Drill events use `event` (`FAILOVER` or `FAILBACK`),
`status`, `operator_approved`, timezone-aware `observed_at`, and
`duration_minutes`. Event timestamps must be no later than `as_of`.

Status precedence is `NOT_READY`, `INCONCLUSIVE`, `AT_RISK`, then a positive
state. A clean preflight is only `READY_FOR_OPERATOR_DRILL`. A successful
operator failover with passing target checks is `FAILOVER_VERIFIED`; a successful
operator failover and failback is `DRILL_VERIFIED`.
