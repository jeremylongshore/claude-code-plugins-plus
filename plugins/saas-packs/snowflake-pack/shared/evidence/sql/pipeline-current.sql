-- Near-live control-plane metadata only. Pipe projections exclude definitions,
-- notification endpoints, query text, and raw SHOW output from the receipt.
SHOW TASKS IN ACCOUNT
->> SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'task_current',
  'database_name', "database_name", 'schema_name', "schema_name", 'name', "name",
  'id', "id", 'state', "state", 'predecessors', "predecessors",
  'schedule', "schedule", 'last_committed_on', "last_committed_on"
) AS EVIDENCE
FROM $1
ORDER BY "database_name", "schema_name", "name";
SHOW STREAMS IN ACCOUNT
->> SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'stream_current',
  'database_name', "database_name", 'schema_name', "schema_name", 'name', "name",
  'table_name', "table_name", 'stale', "stale", 'stale_after', "stale_after",
  'invalid', "invalid"
) AS EVIDENCE
FROM $1
ORDER BY "database_name", "schema_name", "name";
SHOW DYNAMIC TABLES IN ACCOUNT
->> SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'dynamic_table_current',
  'database_name', "database_name", 'schema_name', "schema_name", 'name', "name",
  'scheduling_state', "scheduling_state", 'target_lag', "target_lag",
  'refresh_mode', "refresh_mode", 'warehouse', "warehouse"
) AS EVIDENCE
FROM $1
ORDER BY "database_name", "schema_name", "name";
SHOW PIPES IN ACCOUNT
->> SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'pipe_current',
  'database_name', "database_name", 'schema_name', "schema_name", 'name', "name",
  'type', "type", 'invalid_reason', "invalid_reason",
  'last_ingested_timestamp', "last_ingested_timestamp"
) AS EVIDENCE
FROM $1
ORDER BY "database_name", "schema_name", "name";
