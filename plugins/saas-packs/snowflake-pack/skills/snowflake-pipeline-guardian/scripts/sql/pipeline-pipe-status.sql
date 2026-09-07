-- Current status for one validated fully qualified pipe identifier. The raw JSON,
-- file paths, channel names, errors, and faults never leave this statement.
WITH raw_status AS (
  SELECT PARSE_JSON(SYSTEM$PIPE_STATUS('__PIPE_IDENTIFIER__')) AS status
), execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context',
    'observed_at', CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()),
    'organization_name_sha256', SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256),
    'account_identifier_sha256', SHA2(
      TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())),
      256
    ),
    'collector_user_sha256', SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER()
      )),
      256
    ),
    'primary_role_sha256', SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_ROLE()
      )),
      256
    ),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_SECONDARY_ROLES()
      )),
      256
    ),
    'timezone', 'UTC'
  ) AS evidence
), projected_status AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'pipe_status',
    'object_key_sha256', SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
        UPPER(SPLIT_PART('__PIPE_IDENTIFIER__', '.', 1)),
        UPPER(SPLIT_PART('__PIPE_IDENTIFIER__', '.', 2)),
        UPPER(SPLIT_PART('__PIPE_IDENTIFIER__', '.', 3))
      )),
      256
    ),
    'execution_state', status:executionState::STRING,
    'oldest_file_timestamp', TRY_TO_TIMESTAMP_TZ(
      TO_VARCHAR(status:oldestFileTimestamp)
    ),
    'pending_file_count', TRY_TO_NUMBER(TO_VARCHAR(status:pendingFileCount)),
    'last_pipe_error_timestamp', TRY_TO_TIMESTAMP_TZ(
      TO_VARCHAR(status:lastPipeErrorTimestamp)
    ),
    'last_pipe_fault_timestamp', TRY_TO_TIMESTAMP_TZ(
      TO_VARCHAR(status:lastPipeFaultTimestamp)
    ),
    'last_ingested_timestamp', TRY_TO_TIMESTAMP_TZ(
      TO_VARCHAR(status:lastIngestedTimestamp)
    ),
    'outstanding_message_count', TRY_TO_NUMBER(
      TO_VARCHAR(status:numOutstandingMessagesOnChannel)
    ),
    'last_received_message_timestamp', TRY_TO_TIMESTAMP_TZ(
      TO_VARCHAR(status:lastReceivedMessageTimestamp)
    ),
    'last_forwarded_message_timestamp', TRY_TO_TIMESTAMP_TZ(
      TO_VARCHAR(status:lastForwardedMessageTimestamp)
    ),
    'last_pulled_from_channel_timestamp', TRY_TO_TIMESTAMP_TZ(
      TO_VARCHAR(status:lastPulledFromChannelTimestamp)
    ),
    'load_history_remaining_entries_to_sync', TRY_TO_NUMBER(
      TO_VARCHAR(status:loadHistoryRemainingEntriesToSync)
    ),
    'oldest_pending_history_refresh_job_creation_time', TRY_TO_TIMESTAMP_TZ(
      TO_VARCHAR(status:oldestPendingHistoryRefreshJobCreationTime)
    ),
    'pending_history_refresh_jobs_count', TRY_TO_NUMBER(
      TO_VARCHAR(status:pendingHistoryRefreshJobsCount)
    )
  ) AS evidence
  FROM raw_status
)
SELECT evidence AS EVIDENCE
FROM (
  SELECT 0 AS sort_group, evidence FROM execution_context
  UNION ALL
  SELECT 1, evidence FROM projected_status
)
ORDER BY sort_group;
