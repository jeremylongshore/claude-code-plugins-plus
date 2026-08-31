-- Near-live failover-group inventory and refresh progress. These statements
-- are read-only; substitute a reviewed group identifier only in the SHOW
-- membership statements and never execute promotion/failback SQL.
SHOW FAILOVER GROUPS;
SELECT *
FROM TABLE(INFORMATION_SCHEMA.REPLICATION_GROUP_REFRESH_PROGRESS_ALL())
ORDER BY START_TIME DESC
LIMIT 1000;
