-- Operational storage context. STORAGE_USAGE uses different measurement semantics
-- from invoice storage and must never be labelled invoice-reconciled by collection.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'storage_usage',
  'start_time', TO_TIMESTAMP_LTZ(USAGE_DATE),
  'end_time', DATEADD('day', 1, TO_TIMESTAMP_LTZ(USAGE_DATE)),
  'storage_bytes', STORAGE_BYTES,
  'stage_bytes', STAGE_BYTES,
  'failsafe_bytes', FAILSAFE_BYTES,
  'hybrid_table_storage_bytes', HYBRID_TABLE_STORAGE_BYTES,
  'invoice_reconciliation', 'not_reconciled'
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE
WHERE USAGE_DATE >= DATEADD('day', -7, CURRENT_DATE())
ORDER BY USAGE_DATE
LIMIT 1000;
