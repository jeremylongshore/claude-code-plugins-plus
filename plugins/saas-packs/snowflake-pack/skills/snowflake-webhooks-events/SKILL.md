---
name: snowflake-webhooks-events
description: |
  Implement Snowflake event-driven patterns with alerts, notifications, and external functions.
  Use when setting up Snowflake alerts, email notifications, external API calls,
  or event-driven pipelines triggered by Snowflake data changes.
  Trigger with phrases like "snowflake alerts", "snowflake notifications",
  "snowflake events", "snowflake external function", "snowflake email".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Webhooks & Events

## Overview

Snowflake uses alerts, email notifications, external functions, and notification integrations for event-driven patterns (not traditional webhooks).

## Prerequisites

- ACCOUNTADMIN or role with `CREATE ALERT` privilege
- Email notification integration configured
- For external functions: API Gateway (AWS/GCP/Azure) configured
- For S3/GCS event notifications: Snowpipe configured

## Instructions

### Step 1: Snowflake Alerts (Built-in Event System)

```sql
-- Alert when daily revenue drops below threshold
CREATE OR REPLACE ALERT revenue_drop_alert
  WAREHOUSE = ANALYTICS_WH
  SCHEDULE = '60 MINUTE'
  IF (EXISTS (
    SELECT 1
    FROM daily_order_metrics
    WHERE metric_date = CURRENT_DATE()
      AND total_revenue < (
        SELECT AVG(total_revenue) * 0.5
        FROM daily_order_metrics
        WHERE metric_date BETWEEN DATEADD(days, -30, CURRENT_DATE())
          AND DATEADD(days, -1, CURRENT_DATE())
      )
  ))
  THEN
    CALL SYSTEM$SEND_EMAIL(
      'revenue_notifications',
      'oncall@company.com',
      'Revenue Alert: Below 50% of 30-day average',
      'Daily revenue has dropped significantly. Check dashboard.'
    );

ALTER ALERT revenue_drop_alert RESUME;

-- Alert when warehouse credits exceed daily budget
CREATE OR REPLACE ALERT credit_usage_alert
  WAREHOUSE = ANALYTICS_WH
  SCHEDULE = '30 MINUTE'
  IF (EXISTS (
    SELECT 1
    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
    WHERE start_time >= CURRENT_DATE()
    GROUP BY ALL
    HAVING SUM(credits_used) > 100  -- Daily budget: 100 credits
  ))
  THEN
    CALL SYSTEM$SEND_EMAIL(
      'ops_notifications',
      'ops@company.com',
      'Snowflake Credit Alert',
      'Daily credit usage has exceeded 100 credits.'
    );

-- Monitor alert history
SELECT *
FROM TABLE(INFORMATION_SCHEMA.ALERT_HISTORY(
  SCHEDULED_TIME_RANGE_START => DATEADD(hours, -24, CURRENT_TIMESTAMP())
))
ORDER BY scheduled_time DESC;
```

### Step 2: Email Notification Integration

```sql
-- Set up email notification integration
CREATE OR REPLACE NOTIFICATION INTEGRATION email_notifications
  TYPE = EMAIL
  ENABLED = TRUE
  ALLOWED_RECIPIENTS = (
    'oncall@company.com',
    'ops@company.com',
    'data-team@company.com'
  );

-- Send email from stored procedure
CREATE OR REPLACE PROCEDURE send_data_quality_report()
  RETURNS VARCHAR
  LANGUAGE SQL
AS
$$
BEGIN
  LET row_count INTEGER;
  SELECT COUNT(*) INTO :row_count
  FROM orders WHERE order_date = CURRENT_DATE() AND amount IS NULL;

  IF (row_count > 0) THEN
    CALL SYSTEM$SEND_EMAIL(
      'email_notifications',
      'data-team@company.com',
      'Data Quality Issue: NULL amounts detected',
      row_count || ' orders have NULL amounts today.'
    );
    RETURN 'Alert sent for ' || row_count || ' records';
  END IF;
  RETURN 'No issues found';
END;
$$;
```

### Step 3: External Functions (Call External APIs)

```sql
-- Create API integration for external function
CREATE OR REPLACE API INTEGRATION my_api_integration
  API_PROVIDER = aws_api_gateway
  API_AWS_ROLE_ARN = 'arn:aws:iam::123456789:role/snowflake-api-role'
  ENABLED = TRUE
  API_ALLOWED_PREFIXES = ('https://api.execute-api.us-east-1.amazonaws.com/');

-- Create external function that calls your API
CREATE OR REPLACE EXTERNAL FUNCTION notify_slack(message VARCHAR)
  RETURNS VARIANT
  API_INTEGRATION = my_api_integration
  AS 'https://api.execute-api.us-east-1.amazonaws.com/prod/slack-notify';

-- Use in a task to notify on data changes
CREATE OR REPLACE TASK notify_new_high_value_orders
  WAREHOUSE = ANALYTICS_WH
  SCHEDULE = '15 MINUTE'
  WHEN SYSTEM$STREAM_HAS_DATA('orders_stream')
AS
  SELECT notify_slack(
    'New high-value order: $' || amount || ' from customer ' || customer_id
  )
  FROM orders_stream
  WHERE METADATA$ACTION = 'INSERT' AND amount >= 10000;
```

### Step 4: Cloud Event Notifications (S3/GCS/Azure)

```sql
-- S3 event notification for auto-ingest (Snowpipe)
-- This triggers when new files land in S3
CREATE OR REPLACE PIPE auto_ingest_pipe
  AUTO_INGEST = TRUE
  AS
  COPY INTO raw_events
    FROM @my_s3_stage/events/
    FILE_FORMAT = my_json_format;

-- Get the SQS queue ARN to configure S3 event notifications
SHOW PIPES LIKE 'auto_ingest_pipe';
-- Copy notification_channel value → S3 bucket event configuration

-- GCS pub/sub notification
CREATE OR REPLACE NOTIFICATION INTEGRATION gcs_notification
  TYPE = QUEUE
  NOTIFICATION_PROVIDER = GCP_PUBSUB
  ENABLED = TRUE
  GCP_PUBSUB_SUBSCRIPTION_NAME = 'projects/my-project/subscriptions/snowflake-sub';
```

### Step 5: Application-Side Event Processing

```typescript
// src/snowflake/event-processor.ts
// Poll for changes using streams (app-side consumption)

interface OrderEvent {
  ORDER_ID: number;
  CUSTOMER_ID: number;
  AMOUNT: number;
  METADATA$ACTION: 'INSERT' | 'DELETE';
}

async function processOrderEvents(conn: snowflake.Connection) {
  // Check if stream has data
  const hasData = await query<{ HAS_DATA: boolean }>(conn,
    "SELECT SYSTEM$STREAM_HAS_DATA('orders_stream') AS HAS_DATA"
  );
  if (!hasData.rows[0]?.HAS_DATA) return;

  // Consume stream within a transaction
  await query(conn, 'BEGIN');
  try {
    const events = await query<OrderEvent>(conn,
      'SELECT * FROM orders_stream'
    );

    for (const event of events.rows) {
      if (event.METADATA$ACTION === 'INSERT' && event.AMOUNT >= 10000) {
        await notifySlack(`High-value order: $${event.AMOUNT}`);
      }
    }

    // Advance the stream offset by writing to target
    await query(conn, `
      INSERT INTO processed_orders
      SELECT order_id, customer_id, amount, CURRENT_TIMESTAMP()
      FROM orders_stream WHERE METADATA$ACTION = 'INSERT'
    `);

    await query(conn, 'COMMIT');
  } catch (err) {
    await query(conn, 'ROLLBACK');
    throw err;
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Alert not firing | Alert suspended | `ALTER ALERT x RESUME` |
| Email not delivered | Recipient not in allowlist | Add to `ALLOWED_RECIPIENTS` |
| External function timeout | API too slow | Increase timeout, check API health |
| Snowpipe not triggering | S3 event config missing | Configure SQS notification from `SHOW PIPES` |
| Stream data loss | Stream stale | Recreate stream, increase retention |

## Resources

- [Snowflake Alerts](https://docs.snowflake.com/en/user-guide/alerts)
- [External Functions](https://docs.snowflake.com/en/sql-reference/external-functions)
- [Snowpipe Auto-Ingest](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro)

## Next Steps

For performance optimization, see `snowflake-performance-tuning`.
