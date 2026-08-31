-- Near-live control-plane metadata only. Run each pair with an approved
-- read-only role. RESULT_SCAN projects safe columns so task/pipe definitions,
-- notification endpoints, and query text never leave the Snowflake session.
SHOW TASKS IN ACCOUNT;
SELECT "database_name", "schema_name", "name", "id", "state", "predecessors",
       "schedule", "last_committed_on"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY "database_name", "schema_name", "name";
SHOW STREAMS IN ACCOUNT;
SELECT "database_name", "schema_name", "name", "table_name", "stale",
       "stale_after", "invalid"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY "database_name", "schema_name", "name";
SHOW DYNAMIC TABLES IN ACCOUNT;
SELECT "database_name", "schema_name", "name", "scheduling_state",
       "target_lag", "refresh_mode", "warehouse"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY "database_name", "schema_name", "name";
SHOW PIPES IN ACCOUNT;
SELECT "database_name", "schema_name", "name", "owner", "type",
       "invalid_reason", "last_ingested_timestamp"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY "database_name", "schema_name", "name";
