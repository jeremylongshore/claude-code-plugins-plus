# Research notes and official sources

This skill targets recurring operational pain rather than generic Snowflake
tutorials: stale streams after retention or object replacement, task graphs that
skip or suspend work, dynamic-table lag and incremental-refresh history failures,
Snowpipe notification/path gaps, schema drift, and duplicate delivery during
replay. The symptoms are intentionally cross-surface because teams experience a
pipeline outage, not an isolated object type.

The source hierarchy is:

1. Snowflake documentation and SQL reference for behavior and privilege claims.
2. Redacted account evidence for the incident-specific state.
3. Community discussions only as discovery signals; never as authority for a
   recovery instruction.

The main primary sources are:

- [Task troubleshooting](https://docs.snowflake.com/en/user-guide/tasks-ts)
- [Task graphs](https://docs.snowflake.com/en/user-guide/tasks-graphs)
- [Stream introduction and staleness](https://docs.snowflake.com/en/user-guide/streams-intro)
- [Dynamic-table monitoring](https://docs.snowflake.com/en/user-guide/dynamic-tables-tasks-monitor)
- [Dynamic-table refresh troubleshooting](https://docs.snowflake.com/en/user-guide/dynamic-tables/troubleshooting)
- [Dynamic-table target lag](https://docs.snowflake.com/en/user-guide/dynamic-tables-target-lag)
- [Snowpipe troubleshooting](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-ts)
- [`SYSTEM$PIPE_STATUS`](https://docs.snowflake.com/en/sql-reference/functions/system_pipe_status)
- [`COPY_HISTORY`](https://docs.snowflake.com/en/sql-reference/functions/copy_history)

Read the live pages for current syntax and retention behavior at the time of an
incident. Product behavior and privilege surfaces evolve; this reference is a
route to primary evidence, not a promise that a copied snippet remains current.
