-- Detailed Cortex AI Functions attribution. Credits overlap the AI_SERVICES total in
-- METERING_HISTORY and must be represented as a non-additive ledger child.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'ai_usage',
  'start_time', START_TIME,
  'end_time', END_TIME,
  'function_name', FUNCTION_NAME,
  'model_name', MODEL_NAME,
  'query_id', QUERY_ID,
  'warehouse_id', WAREHOUSE_ID,
  'query_tag_sha256', IFF(QUERY_TAG IS NULL OR QUERY_TAG = '', NULL, SHA2(TO_VARCHAR(QUERY_TAG), 256)),
  'user_id_sha256', IFF(USER_ID IS NULL, NULL, SHA2(TO_VARCHAR(USER_ID), 256)),
  'credits_used', CREDITS,
  'is_completed', IS_COMPLETED
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY
WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY START_TIME, QUERY_ID, FUNCTION_NAME, MODEL_NAME
LIMIT 5000;
