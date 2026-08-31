# Current association and notification state

Use `scripts/sql/current-state.sql` to inspect the current association metadata
needed to interpret historical expectation results. The query uses
`SNOWFLAKE.ACCOUNT_USAGE.DATA_METRIC_FUNCTION_REFERENCES` and deliberately
excludes `FILTER`, `WITHIN_GROUP`, and group values. That Account Usage view can
lag up to three hours and requires the documented governance/usage viewer
visibility; it is not a real-time health signal.

The normalized analyzer input may include:

```json
"current_state": {
  "status": "collected",
  "observed_at": "2026-08-31T11:55:00Z",
  "max_age_seconds": 1800,
  "associations": [{
    "requirement_id": "orders-null-count",
    "reference_id": "ref-orders-null",
    "status": "ACTIVE",
    "schedule_status": "STARTED",
    "notification_status": "ENABLED",
    "execution_role": "DQ_MONITOR"
  }],
  "notifications": [{
    "requirement_id": "orders-null-count",
    "status": "ENABLED",
    "last_delivery_at": "2026-08-31T11:30:00Z"
  }]
}
```

The requirement list remains the denominator. Missing, stale, unavailable,
duplicate, or non-active current associations block monitoring claims even when
a historical measurement passed. Notification status is separate from
expectation status: a valid expectation result does not prove delivery. Do not
collect `GROUP_BY_VALUES`, failed rows, predicates, SQL text, endpoints, or
customer identifiers.
