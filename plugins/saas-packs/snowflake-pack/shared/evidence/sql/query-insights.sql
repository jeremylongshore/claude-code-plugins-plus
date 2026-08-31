-- Query ID is substituted only by the collector after strict validation.
-- Message and suggestions are intentionally omitted because they may reveal
-- object names or query details; the analyzer accepts the typed insight only.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'query_insights',
  'query_id', QUERY_ID,
  'query_hash', QUERY_HASH,
  'query_parameterized_hash', QUERY_PARAMETERIZED_HASH,
  'insight_type_id', INSIGHT_TYPE_ID,
  'is_opportunity', IS_OPPORTUNITY,
  'insight_topic', INSIGHT_TOPIC
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_INSIGHTS
WHERE QUERY_ID = '__QUERY_ID__'
LIMIT 1000;
