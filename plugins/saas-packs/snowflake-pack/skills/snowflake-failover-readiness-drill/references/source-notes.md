# Primary source notes

Verify these live before an exercise because Snowflake capabilities and columns
can change:

- [Replication group refresh history](https://docs.snowflake.com/en/sql-reference/account-usage/replication_group_refresh_history): Account Usage columns, three-hour latency warning, secondary-account scope, phases, and real-time table-function route.
- [Introduction to replication and failover](https://docs.snowflake.com/en/user-guide/account-replication-intro): capability and edition boundaries.
- [Failover groups](https://docs.snowflake.com/en/user-guide/account-replication-failover-failback): operator-controlled failover/failback lifecycle and object behavior.
- [Replication considerations](https://docs.snowflake.com/en/user-guide/account-replication-considerations): object dependencies and feature limitations.

The analyzer intentionally preserves conservative non-claims: historical
success is not current readiness, client login is not application validation,
and absence from a lagged or permission-limited view is not health.
