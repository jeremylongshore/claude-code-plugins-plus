-- Association metadata only. FILTER, WITHIN_GROUP, and group values are
-- intentionally excluded; Account Usage may lag up to three hours.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'data_quality_current',
  'metric_database_name', METRIC_DATABASE_NAME,
  'metric_schema_name', METRIC_SCHEMA_NAME,
  'metric_name', METRIC_NAME,
  'ref_database_name', REF_DATABASE_NAME,
  'ref_schema_name', REF_SCHEMA_NAME,
  'ref_entity_name', REF_ENTITY_NAME,
  'ref_entity_domain', REF_ENTITY_DOMAIN,
  'reference_id', REF_ID,
  'schedule', SCHEDULE,
  'schedule_status', SCHEDULE_STATUS,
  'notification_status', DATA_QUALITY_NOTIFICATION_STATUS,
  'anomaly_detection_status', ANOMALY_DETECTION_STATUS,
  'execution_role', USE_ROLE
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_METRIC_FUNCTION_REFERENCES
ORDER BY REF_DATABASE_NAME, REF_SCHEMA_NAME, REF_ENTITY_NAME, REF_ID
LIMIT 5000;
