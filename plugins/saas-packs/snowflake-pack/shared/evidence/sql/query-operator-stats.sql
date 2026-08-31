-- Query ID is substituted only by the collector after strict validation.
-- GET_QUERY_OPERATOR_STATS is available for completed queries from the past
-- 14 days and requires warehouse OPERATE or MONITOR privilege.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'operator_stats',
  'query_id', '__QUERY_ID__',
  'operator_id', OPERATOR_ID,
  'operator_type', OPERATOR_TYPE,
  'operator_statistics', OPERATOR_STATISTICS,
  'execution_time_breakdown', EXECUTION_TIME_BREAKDOWN
) AS EVIDENCE
FROM TABLE(GET_QUERY_OPERATOR_STATS('__QUERY_ID__'))
LIMIT 1000;
