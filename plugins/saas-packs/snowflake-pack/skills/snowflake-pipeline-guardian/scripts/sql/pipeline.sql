-- Bounded, settled Account Usage evidence. All identifiers are account-scoped
-- pseudonyms. SQL text, error messages, paths, and raw object names are omitted.
WITH collection_context AS (
  SELECT
    CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()) AS observed_at,
    TO_TIMESTAMP_TZ('__WINDOW_START_UTC__') AS window_start_utc,
    TO_TIMESTAMP_TZ('__WINDOW_END_UTC__') AS window_end_utc,
    SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256) AS organization_name_sha256,
    SHA2(
      TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())),
      256
    ) AS account_identifier_sha256
), task_history AS (
  SELECT
    SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
        DATABASE_NAME, SCHEMA_NAME, NAME
      )),
      256
    ) || '|' || TO_VARCHAR(COMPLETED_TIME) || '|' || COALESCE(TO_VARCHAR(RUN_ID), '') AS sort_key,
    OBJECT_CONSTRUCT_KEEP_NULL(
      '_dataset', 'task_history',
      'object_key_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
          DATABASE_NAME, SCHEMA_NAME, NAME
        )),
        256
      ),
      'state', STATE,
      'scheduled_time', SCHEDULED_TIME,
      'completed_time', COMPLETED_TIME,
      'query_start_time', QUERY_START_TIME,
      'root_task_id_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), ROOT_TASK_ID
        )),
        256
      ),
      'run_id_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), RUN_ID
        )),
        256
      ),
      'graph_run_group_id_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), GRAPH_RUN_GROUP_ID
        )),
        256
      ),
      'attempt_number', ATTEMPT_NUMBER,
      'graph_version', GRAPH_VERSION,
      'query_id_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), QUERY_ID
        )),
        256
      )
    ) AS evidence
  FROM SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY
  CROSS JOIN collection_context
  WHERE COMPLETED_TIME >= window_start_utc
    AND COMPLETED_TIME < LEAST(
      window_end_utc,
      DATEADD('minute', -45, observed_at)
    )
  ORDER BY COMPLETED_TIME, sort_key
  LIMIT 5000
), dynamic_table_refresh_history AS (
  SELECT
    SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
        DATABASE_NAME, SCHEMA_NAME, NAME
      )),
      256
    ) || '|' || TO_VARCHAR(REFRESH_END_TIME) || '|' ||
      COALESCE(TO_VARCHAR(QUERY_ID), '') AS sort_key,
    OBJECT_CONSTRUCT_KEEP_NULL(
      '_dataset', 'dynamic_table_refresh_history',
      'object_key_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
          DATABASE_NAME, SCHEMA_NAME, NAME
        )),
        256
      ),
      'state', STATE,
      'refresh_start_time', REFRESH_START_TIME,
      'refresh_end_time', REFRESH_END_TIME,
      'data_timestamp', DATA_TIMESTAMP,
      'completion_target', COMPLETION_TARGET,
      'refresh_action', REFRESH_ACTION,
      'refresh_trigger', REFRESH_TRIGGER,
      'target_lag_sec', TARGET_LAG_SEC,
      'query_id_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), QUERY_ID
        )),
        256
      )
    ) AS evidence
  FROM SNOWFLAKE.ACCOUNT_USAGE.DYNAMIC_TABLE_REFRESH_HISTORY
  CROSS JOIN collection_context
  WHERE REFRESH_END_TIME IS NOT NULL
    AND STATE <> 'EXECUTING'
    AND REFRESH_END_TIME >= window_start_utc
    AND REFRESH_END_TIME < LEAST(
      window_end_utc,
      DATEADD('hour', -3, observed_at)
    )
  ORDER BY REFRESH_END_TIME, sort_key
  LIMIT 5000
), copy_history AS (
  SELECT
    TO_VARCHAR(LAST_LOAD_TIME) || '|' || SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
        STAGE_LOCATION, FILE_NAME
      )),
      256
    ) AS sort_key,
    OBJECT_CONSTRUCT_KEEP_NULL(
      '_dataset', 'copy_history',
      'file_identifier_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
          STAGE_LOCATION, FILE_NAME
        )),
        256
      ),
      'stage_identifier_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), STAGE_LOCATION
        )),
        256
      ),
      'object_key_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
          TABLE_CATALOG_NAME, TABLE_SCHEMA_NAME, TABLE_NAME
        )),
        256
      ),
      'pipe_identifier_sha256', IFF(
        PIPE_NAME IS NULL,
        NULL,
        SHA2(
          TO_JSON(ARRAY_CONSTRUCT(
            CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
            PIPE_CATALOG_NAME, PIPE_SCHEMA_NAME, PIPE_NAME
          )),
          256
        )
      ),
      'last_load_time', LAST_LOAD_TIME,
      'pipe_received_time', PIPE_RECEIVED_TIME,
      'first_commit_time', FIRST_COMMIT_TIME,
      'status', STATUS,
      'row_count', ROW_COUNT,
      'row_parsed', ROW_PARSED,
      'file_size', FILE_SIZE,
      'error_count', ERROR_COUNT
    ) AS evidence
  FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
  CROSS JOIN collection_context
  WHERE LAST_LOAD_TIME >= window_start_utc
    AND LAST_LOAD_TIME < LEAST(
      window_end_utc,
      DATEADD('hour', -48, observed_at)
    )
  ORDER BY LAST_LOAD_TIME, sort_key
  LIMIT 5000
), execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context',
    'observed_at', observed_at,
    'organization_name_sha256', organization_name_sha256,
    'account_identifier_sha256', account_identifier_sha256,
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
    'timezone', 'UTC',
    'window_start_utc', window_start_utc,
    'window_end_utc', window_end_utc,
    'window_semantics', 'HALF_OPEN_UTC',
    'task_history_settled_through_utc', LEAST(
      window_end_utc,
      DATEADD('minute', -45, observed_at)
    ),
    'dynamic_table_refresh_history_settled_through_utc', LEAST(
      window_end_utc,
      DATEADD('hour', -3, observed_at)
    ),
    'copy_history_settled_through_utc', LEAST(
      window_end_utc,
      DATEADD('hour', -48, observed_at)
    ),
    'per_dataset_row_limit', 5000
  ) AS evidence
  FROM collection_context
)
SELECT evidence AS EVIDENCE
FROM (
  SELECT 'execution_context' AS dataset, '' AS sort_key, evidence
  FROM execution_context
  UNION ALL
  SELECT 'task_history', sort_key, evidence FROM task_history
  UNION ALL
  SELECT 'dynamic_table_refresh_history', sort_key, evidence
  FROM dynamic_table_refresh_history
  UNION ALL
  SELECT 'copy_history', sort_key, evidence FROM copy_history
)
ORDER BY dataset, sort_key;
