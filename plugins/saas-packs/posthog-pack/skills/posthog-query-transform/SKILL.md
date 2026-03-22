---
name: posthog-query-transform
description: |
  Execute PostHog primary workflow: Query & Transform Data.
  Use when writing analytical queries over production data,
  building materialized views for dashboards, or transforming raw events into business metrics.
  Trigger with phrases like "posthog query data",
  "run analytical query with posthog".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, posthog]
---

# PostHog Query & Transform Data

## Overview
Write, optimize, and execute analytical queries against your data platform.
This is the primary workflow — read data, aggregate it, shape it for consumption.


## Prerequisites
- Completed `posthog-install-auth` setup

- Familiarity with SQL and your database schema

- Valid API credentials configured

## Instructions

### Step 1: Connect and Discover Schema
```typescript
const schema = await client.query(`
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_name = 'events'
  ORDER BY ordinal_position
`);
console.log('Schema:', schema.rows);

```

### Step 2: Write and Execute Query
```typescript
const metrics = await client.query(`
  SELECT
    date_trunc('day', created_at) AS day,
    COUNT(*) AS event_count,
    COUNT(DISTINCT user_id) AS unique_users
  FROM events
  WHERE created_at >= NOW() - INTERVAL '30 days'
  GROUP BY 1
  ORDER BY 1 DESC
`);

```

### Step 3: Process and Export Results
```typescript
// Write results to downstream table or export
await client.query(`
  CREATE TABLE IF NOT EXISTS daily_metrics AS
  SELECT * FROM (${metricsQuery}) sub
`);
console.log(`Wrote ${metrics.rows.length} rows to daily_metrics`);

```

## Output
- Completed Query & Transform Data execution

- Query results with row count and execution time
- Data written to target table or exported to file

- Success confirmation or error details

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Query Timeout | Query exceeded execution time limit (complex joins/scans) | Add indexes, reduce scan range with WHERE clauses, or increase timeout. |
| Permission Denied | Role lacks SELECT/INSERT privilege on target table | GRANT required privileges or use a service role with broader access. |

## Examples

### Complete Workflow
```typescript
// Full query pipeline: schema discovery → query → export
const client = new DataClient({ connectionString: process.env.DATABASE_URL });

const result = await client.query(`
  SELECT user_id, COUNT(*) as actions, MAX(created_at) as last_seen
  FROM events
  WHERE event_type = 'purchase'
  GROUP BY user_id
  HAVING COUNT(*) > 5
  ORDER BY actions DESC
  LIMIT 100
`);
console.log(`Top 100 buyers: ${result.rows.length} rows`);

```

### Common Variations
- **Parameterized**: Use `$1, $2` placeholders to prevent SQL injection
- **Streaming**: Use cursor-based iteration for large result sets
- **Materialized views**: Pre-compute expensive aggregations on a schedule


## Resources
- [PostHog Documentation](https://docs.posthog.com)
- [PostHog API Reference](https://docs.posthog.com/api)

## Next Steps
For secondary workflow, see `posthog-schema-migration`.