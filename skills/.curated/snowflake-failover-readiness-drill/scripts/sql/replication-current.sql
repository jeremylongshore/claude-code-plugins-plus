-- Near-live group inventory and refresh progress. Pipe projection prevents raw
-- account/owner columns from leaving the session; no promotion or failback runs.
SHOW REPLICATION GROUPS
->> SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'failover_groups',
  'name', "name",
  'type', "type",
  'object_types', "object_types",
  'replication_schedule', "replication_schedule",
  'secondary_state', "secondary_state",
  'next_scheduled_refresh', "next_scheduled_refresh"
) AS EVIDENCE
FROM $1
ORDER BY "name"
LIMIT 1000;
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'replication_progress',
  'group_name', GROUP_NAME,
  'group_type', GROUP_TYPE,
  'phase_name', PHASE_NAME,
  'start_time', START_TIME,
  'end_time', END_TIME,
  'progress', PROGRESS
) AS EVIDENCE
FROM TABLE(INFORMATION_SCHEMA.REPLICATION_GROUP_REFRESH_PROGRESS_ALL())
ORDER BY START_TIME DESC
LIMIT 1000;
