---
name: clickhouse-data-handling
description: |
  Handle data lifecycle in ClickHouse — TTL expiration, data deletion (GDPR),
  column-level encryption, and audit logging with real ClickHouse SQL.
  Use when implementing data retention, GDPR deletion requests,
  or managing sensitive data in ClickHouse.
  Trigger: "clickhouse data retention", "clickhouse TTL", "clickhouse GDPR",
  "delete data clickhouse", "clickhouse data lifecycle", "clickhouse PII".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Data Handling

## Overview

Manage the full data lifecycle in ClickHouse: TTL-based expiration, GDPR/CCPA
deletion, data masking, partition management, and audit trails.

## Prerequisites

- ClickHouse tables with data (see `clickhouse-core-workflow-a`)
- Understanding of your data retention requirements

## Instructions

### Step 1: TTL-Based Data Expiration

```sql
-- Add TTL to expire data automatically
CREATE TABLE analytics.events (
    event_id    UUID DEFAULT generateUUIDv4(),
    event_type  LowCardinality(String),
    user_id     UInt64,
    properties  String CODEC(ZSTD(3)),
    created_at  DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (event_type, created_at)
PARTITION BY toYYYYMM(created_at)
TTL created_at + INTERVAL 90 DAY;    -- Auto-delete after 90 days

-- Add TTL to existing table
ALTER TABLE analytics.events
    MODIFY TTL created_at + INTERVAL 90 DAY;

-- Tiered storage TTL (hot → cold → delete)
ALTER TABLE analytics.events
    MODIFY TTL
        created_at + INTERVAL 7 DAY TO VOLUME 'hot',
        created_at + INTERVAL 30 DAY TO VOLUME 'cold',
        created_at + INTERVAL 365 DAY DELETE;

-- Column-level TTL (null out PII after 30 days, keep the row)
ALTER TABLE analytics.events
    MODIFY COLUMN email String DEFAULT ''
    TTL created_at + INTERVAL 30 DAY;

-- Force TTL cleanup now (normally runs during merges)
OPTIMIZE TABLE analytics.events FINAL;
```

### Step 2: Data Deletion for GDPR/CCPA

```sql
-- Option A: Lightweight DELETE (ClickHouse 23.3+)
-- Marks rows as deleted without rewriting parts immediately
DELETE FROM analytics.events WHERE user_id = 42;

-- Option B: ALTER TABLE DELETE (mutation — rewrites parts in background)
ALTER TABLE analytics.events DELETE WHERE user_id = 42;

-- Check mutation progress
SELECT
    database, table, mutation_id, command,
    is_done, parts_to_do, create_time
FROM system.mutations
WHERE NOT is_done
ORDER BY create_time DESC;

-- Option C: Drop entire partitions (fastest for bulk deletion)
-- First, check what partitions exist
SELECT partition, count() AS parts, sum(rows) AS rows,
       min(min_time) AS from_time, max(max_time) AS to_time
FROM system.parts
WHERE database = 'analytics' AND table = 'events' AND active
GROUP BY partition ORDER BY partition;

ALTER TABLE analytics.events DROP PARTITION '202401';
```

**Important notes on ClickHouse deletions:**
- `DELETE FROM` is lightweight but still creates mutations internally
- Mutations rewrite data parts in the background — not instant
- For GDPR compliance, use `ALTER TABLE DELETE` and verify via `system.mutations`
- Partitioned data is fastest to bulk-delete via `DROP PARTITION`

### Step 3: Data Masking and Anonymization

```sql
-- Create a view that masks PII for analyst access
CREATE VIEW analytics.events_masked AS
SELECT
    event_id,
    event_type,
    sipHash64(user_id) AS user_id_hash,    -- One-way hash
    JSONExtractString(properties, 'url') AS url,  -- Extract safe fields only
    -- Mask email: show domain only
    concat('***@', substringAfter(email, '@')) AS masked_email,
    created_at
FROM analytics.events;

-- Row-level masking with dictionaries
CREATE DICTIONARY analytics.pii_allowlist (
    user_id UInt64,
    can_see_pii UInt8
)
PRIMARY KEY user_id
SOURCE(CLICKHOUSE(TABLE 'pii_allowlist'))
LIFETIME(MIN 300 MAX 600)
LAYOUT(FLAT());
```

### Step 4: User Data Export (DSAR)

```typescript
import { createClient } from '@clickhouse/client';

async function exportUserData(userId: number): Promise<Record<string, unknown[]>> {
  const client = createClient({ url: process.env.CLICKHOUSE_HOST! });

  // Export all user data from all tables
  const tables = ['events', 'sessions', 'purchases'];
  const result: Record<string, unknown[]> = {};

  for (const table of tables) {
    const rs = await client.query({
      query: `SELECT * FROM analytics.${table} WHERE user_id = {uid:UInt64}`,
      query_params: { uid: userId },
      format: 'JSONEachRow',
    });
    result[table] = await rs.json();
  }

  return result;
}

// GDPR: Delete all user data
async function deleteUserData(userId: number): Promise<void> {
  const client = createClient({ url: process.env.CLICKHOUSE_HOST! });
  const tables = ['events', 'sessions', 'purchases'];

  for (const table of tables) {
    await client.command({
      query: `ALTER TABLE analytics.${table} DELETE WHERE user_id = {uid:UInt64}`,
      query_params: { uid: userId },
    });
  }

  // Log the deletion for compliance audit trail
  await client.insert({
    table: 'analytics.gdpr_audit_log',
    values: [{
      user_id: userId,
      action: 'DELETE_ALL',
      tables_affected: tables.join(','),
      requested_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
    }],
    format: 'JSONEachRow',
  });
}
```

### Step 5: Audit Trail Table

```sql
-- Immutable audit log (no deletes, no TTL)
CREATE TABLE analytics.audit_log (
    log_id      UUID DEFAULT generateUUIDv4(),
    action      LowCardinality(String),  -- 'query', 'delete', 'export', 'schema_change'
    actor       String,                   -- User or service name
    target      String,                   -- Table or resource
    details     String CODEC(ZSTD(3)),    -- JSON details
    ip_address  IPv4,
    logged_at   DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (action, logged_at)
PARTITION BY toYYYYMM(logged_at);
-- No TTL — audit logs must be retained

-- Query audit trail
SELECT logged_at, actor, action, target, details
FROM analytics.audit_log
WHERE action = 'DELETE_ALL'
ORDER BY logged_at DESC
LIMIT 50;
```

### Step 6: Retention Monitoring

```sql
-- Data retention overview
SELECT
    database, table,
    result_ttl_expression AS ttl,
    formatReadableSize(sum(bytes_on_disk)) AS size,
    min(p.min_time) AS oldest_data,
    max(p.max_time) AS newest_data,
    dateDiff('day', min(p.min_time), max(p.max_time)) AS days_span
FROM system.tables t
LEFT JOIN system.parts p ON t.database = p.database AND t.name = p.table AND p.active
WHERE t.database = 'analytics'
GROUP BY database, table, result_ttl_expression
ORDER BY sum(bytes_on_disk) DESC;

-- Find tables missing TTL
SELECT database, name AS table, engine
FROM system.tables
WHERE database = 'analytics'
  AND engine LIKE '%MergeTree%'
  AND result_ttl_expression = '';
```

## Data Classification

| Category | Examples | Handling in ClickHouse |
|----------|----------|------------------------|
| PII | Email, name, IP | Column-level TTL, masking views, deletion support |
| Sensitive | API keys, tokens | Never store in ClickHouse — use secret managers |
| Business | Event counts, metrics | Standard TTL, aggregate for long-term retention |
| Audit | Access logs | No TTL, immutable, partitioned by month |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Mutation stuck | Large table rewrite | Check `system.mutations`, cancel if needed |
| TTL not expiring | No merges running | `OPTIMIZE TABLE ... FINAL` to force |
| DELETE not working | Old ClickHouse version | Use `ALTER TABLE DELETE` (mutation) |
| Export timeout | Too much user data | Add LIMIT or export in batches |

## Resources

- [TTL for Data Management](https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree#table_engine-mergetree-ttl)
- [DELETE Statement](https://clickhouse.com/docs/sql-reference/statements/delete)
- [Mutations](https://clickhouse.com/docs/guides/developer/mutations)

## Next Steps

For role-based access control, see `clickhouse-enterprise-rbac`.
