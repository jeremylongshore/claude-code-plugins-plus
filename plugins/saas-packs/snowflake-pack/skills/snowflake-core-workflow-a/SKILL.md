---
name: snowflake-core-workflow-a
description: |
  Execute Snowflake primary workflow: data loading via stages and COPY INTO.
  Use when loading data from S3/GCS/Azure into Snowflake tables,
  setting up Snowpipe for continuous ingestion, or bulk loading files.
  Trigger with phrases like "snowflake load data", "snowflake COPY INTO",
  "snowflake stage", "snowflake ingest", "snowflake S3 load", "snowpipe".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Core Workflow A — Data Loading

## Overview

Primary data loading workflow: stages, file formats, COPY INTO, and Snowpipe for continuous ingestion.

## Prerequisites

- Completed `snowflake-install-auth` setup
- Target table created in Snowflake
- Source data in S3, GCS, Azure Blob, or local files
- Role with `CREATE STAGE` and `USAGE` on warehouse

## Instructions

### Step 1: Create a File Format

```sql
-- CSV format
CREATE OR REPLACE FILE FORMAT my_csv_format
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  NULL_IF = ('NULL', 'null', '')
  EMPTY_FIELD_AS_NULL = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

-- JSON format (for semi-structured data)
CREATE OR REPLACE FILE FORMAT my_json_format
  TYPE = 'JSON'
  STRIP_OUTER_ARRAY = TRUE
  IGNORE_UTF8_ERRORS = TRUE;

-- Parquet format
CREATE OR REPLACE FILE FORMAT my_parquet_format
  TYPE = 'PARQUET'
  SNAPPY_COMPRESSION = TRUE;
```

### Step 2: Create a Stage

```sql
-- External stage (S3)
CREATE OR REPLACE STAGE my_s3_stage
  STORAGE_INTEGRATION = my_s3_integration
  URL = 's3://my-bucket/data/'
  FILE_FORMAT = my_csv_format;

-- External stage (GCS)
CREATE OR REPLACE STAGE my_gcs_stage
  STORAGE_INTEGRATION = my_gcs_integration
  URL = 'gcs://my-bucket/data/'
  FILE_FORMAT = my_csv_format;

-- Internal stage (Snowflake-managed storage)
CREATE OR REPLACE STAGE my_internal_stage
  FILE_FORMAT = my_csv_format;

-- List files in stage
LIST @my_s3_stage;
```

### Step 3: Upload Files to Internal Stage

```bash
# Using SnowSQL PUT command
snowsql -c prod -q "PUT file:///tmp/data/*.csv @my_internal_stage AUTO_COMPRESS=TRUE"
```

```python
# Using Python connector
cursor.execute("PUT file:///tmp/data/users.csv @my_internal_stage AUTO_COMPRESS=TRUE")
```

### Step 4: Load Data with COPY INTO

```sql
-- Basic COPY INTO from stage
COPY INTO my_db.my_schema.users
  FROM @my_s3_stage/users/
  FILE_FORMAT = my_csv_format
  ON_ERROR = 'CONTINUE'          -- Skip bad rows
  PURGE = TRUE;                  -- Delete files after load

-- COPY with column mapping
COPY INTO my_db.my_schema.orders (order_id, customer_id, amount, order_date)
  FROM (
    SELECT $1, $2, $3::FLOAT, $4::TIMESTAMP_NTZ
    FROM @my_s3_stage/orders/
  )
  FILE_FORMAT = my_csv_format;

-- Load JSON into VARIANT column
COPY INTO my_db.my_schema.raw_events
  FROM @my_s3_stage/events/
  FILE_FORMAT = my_json_format
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Check COPY history
SELECT * FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  TABLE_NAME => 'USERS',
  START_TIME => DATEADD(hours, -24, CURRENT_TIMESTAMP())
));
```

### Step 5: Programmatic Load (Node.js)

```typescript
import { pool } from './snowflake/pool';
import { query } from './snowflake/query';

async function loadDataFromStage(
  tableName: string,
  stagePath: string,
  fileFormat: string = 'my_csv_format'
) {
  return pool.withConnection(async (conn) => {
    const result = await query(conn, `
      COPY INTO ${tableName}
        FROM @${stagePath}
        FILE_FORMAT = ${fileFormat}
        ON_ERROR = 'CONTINUE'
        FORCE = FALSE
    `);

    // COPY INTO returns load status per file
    for (const row of result.rows) {
      console.log(`File: ${row.file}, Status: ${row.status}, Rows: ${row.rows_loaded}`);
      if (row.errors_seen > 0) {
        console.warn(`  Errors: ${row.errors_seen}, First error: ${row.first_error}`);
      }
    }
    return result.rows;
  });
}
```

### Step 6: Set Up Snowpipe for Continuous Loading

```sql
-- Create pipe for auto-ingest from S3
CREATE OR REPLACE PIPE my_db.my_schema.user_pipe
  AUTO_INGEST = TRUE
  AS
  COPY INTO my_db.my_schema.users
    FROM @my_s3_stage/users/
    FILE_FORMAT = my_csv_format;

-- Get the SQS queue ARN for S3 event notifications
SHOW PIPES LIKE 'user_pipe';
-- Use the notification_channel value to configure S3 bucket events

-- Monitor pipe status
SELECT SYSTEM$PIPE_STATUS('my_db.my_schema.user_pipe');

-- Check Snowpipe load history
SELECT *
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  TABLE_NAME => 'USERS',
  START_TIME => DATEADD(hours, -1, CURRENT_TIMESTAMP())
))
WHERE pipe_catalog_name IS NOT NULL;
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Insufficient privileges on stage` | Role lacks USAGE | `GRANT USAGE ON STAGE x TO ROLE y` |
| `File not found` | Wrong stage path | Run `LIST @stage` to verify files |
| `Number of columns in file does not match` | Schema mismatch | Use `ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE` or fix file |
| `Files already loaded` | COPY deduplication | Use `FORCE = TRUE` to reload (careful) |
| `Pipe not receiving files` | Missing S3 event notification | Configure SQS notification from `SHOW PIPES` output |

## Resources

- [Overview of Data Loading](https://docs.snowflake.com/en/user-guide/data-load-overview)
- [CREATE PIPE (Snowpipe)](https://docs.snowflake.com/en/sql-reference/sql/create-pipe)
- [COPY INTO](https://docs.snowflake.com/en/sql-reference/sql/copy-into-table)

## Next Steps

For data transformation workflows, see `snowflake-core-workflow-b`.
