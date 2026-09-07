# Official Snowflake source notes

Re-check these primary sources at execution time because provider behavior and
columns can change.

- [SHOW FAILOVER GROUPS](https://docs.snowflake.com/en/sql-reference/sql/show-failover-groups): Business Critical requirement; role-filtered visibility;
  `is_primary`, configuration, schedule, `secondary_state`, and next refresh.
  Snowflake's example shows `secondary_state` null on the primary and `STARTED`
  on the scheduled secondary, so readiness tests the secondary state rather than
  demanding `STARTED` from a primary row.
- [Replication group refresh history](https://docs.snowflake.com/en/sql-reference/functions/replication_group_refresh_history): Information Schema history,
  14-day range limit, target-account secondary scope, phase rows, and
  `PRIMARY_SNAPSHOT_TIMESTAMP`. That timestamp—not refresh end time—is the RPO
  currency anchor.
- [Replication group refresh progress](https://docs.snowflake.com/en/sql-reference/functions/replication_group_refresh_progress): current/recent progress phases. `END_TIME` can be null even for a terminal phase, so status is derived from `PHASE_NAME`.
- [Replication group dangling references](https://docs.snowflake.com/en/sql-reference/functions/replication_group_dangling_references): selector-scoped dependencies and
  `IS_BLOCKING_REFRESH`. Evaluate all secondaries from the source group and the
  selected target from the target account; zero rows is scoped absence only.
- [Monitor replication](https://docs.snowflake.com/en/user-guide/account-replication-monitor): documented monitoring routes and history/progress interpretation.
- [Replication considerations](https://docs.snowflake.com/en/user-guide/account-replication-considerations): object dependencies and provider limitations.
- [Failover and failback](https://docs.snowflake.com/en/user-guide/account-replication-failover-failback): operator-controlled promotion and return lifecycle. Failback is a later reverse promotion after refresh, not an analyzer rollback.

The collector intentionally uses Information Schema for bounded history and
progress. Snowflake documents the query range/retention but no numeric visibility
latency SLA for these functions, so the contract does not invent one. The 15-minute
receipt-age rule is this skill's evidence currency bound, not a Snowflake SLA.

Preview-only columns are excluded from readiness completeness. Historical success
does not prove current health; a permission-limited empty result does not prove
absence; current group state does not prove application behavior; and a successful
login does not prove data currency or business invariants.
