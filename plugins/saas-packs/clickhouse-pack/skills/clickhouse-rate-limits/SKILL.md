---
name: clickhouse-rate-limits
description: |
  Configure ClickHouse query concurrency, memory quotas, and connection limits.
  Use when hitting "too many simultaneous queries", managing concurrent users,
  or tuning server-side resource limits so an app never starves the cluster.
  Trigger with "clickhouse rate limit", "clickhouse concurrency", "clickhouse quota",
  "too many simultaneous queries", "clickhouse connection limit".
allowed-tools: Read, Write, Edit
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Rate Limits & Concurrency

## Overview

ClickHouse has no REST API rate limits like a SaaS product. Instead it enforces
server-side concurrency limits, memory quotas, and per-user settings that
control resource usage. This skill configures those server-side limits and pairs
them with client-side controls so an application stays within them under load.

## Prerequisites

- ClickHouse admin access (or Cloud console) to create quotas and settings profiles.
- The `@clickhouse/client` Node package for the client-side patterns.
- A rough target for peak concurrent queries and per-query memory.

## Instructions

Work top-down: cap resources at the server, then make the client respect the cap.

### Step 1: Know the server-side limits

The defaults you tune most often:

| Setting | Default | Controls |
|---------|---------|----------|
| `max_concurrent_queries` | 100 | Queries running simultaneously |
| `max_connections` | 4096 | Max TCP/HTTP connections |
| `max_memory_usage` | ~10GB | Per-query memory |
| `max_execution_time` | 0 (unlimited) | Per-query timeout (seconds) |

ClickHouse Cloud's management API (not the query interface) is separately limited
to 10 requests per 10 seconds. Full table in
[references/implementation.md](references/implementation.md).

### Step 2: Cap resources per user (essential skeleton)

Bind a quota and a settings profile to each application user:

```sql
CREATE SETTINGS PROFILE IF NOT EXISTS app_profile
    SETTINGS
        max_memory_usage = 5000000000,       -- 5GB per query
        max_execution_time = 30,             -- 30s timeout
        max_concurrent_queries_for_user = 10 -- 10 parallel queries
    TO app_user;
```

The full quota (`CREATE QUOTA … FOR INTERVAL 1 HOUR MAX …`) plus verification
queries are in [references/implementation.md](references/implementation.md).

### Step 3: Make the client respect the cap

Four client-side patterns keep the app inside the server limits — connection
pooling, an app-level concurrency queue (`p-queue`), retry-with-backoff on
`TOO_MANY_SIMULTANEOUS_QUERIES`, and insert buffering to avoid `TOO_MANY_PARTS`.
Each is a drop-in TypeScript snippet in
[references/implementation.md](references/implementation.md), with the
concurrency queue as the smallest starting point:

```typescript
import PQueue from 'p-queue';
const queryQueue = new PQueue({ concurrency: 5, timeout: 30_000, throwOnTimeout: true });
const rateLimitedQuery = <T>(sql: string) =>
  queryQueue.add(async () => (await client.query({ query: sql, format: 'JSONEachRow' })).json<T>());
```

### Step 4: Monitor and verify

Watch live concurrency and confirm limits bind with the queries in
[references/examples.md](references/examples.md) (`system.processes`,
`system.metrics`, `system.query_log`, `SHOW QUOTAS`).

## Output

Applying this skill produces:

- A ClickHouse **settings profile** and **quota** bound to the app user, capping
  per-query memory, timeout, and per-user concurrency.
- **Client-side guardrails** — a bounded connection pool, a concurrency queue, a
  retry wrapper, and an insert buffer — so the app cannot exceed the server cap.
- **Monitoring queries** that report current running queries, queue depth, and
  historical peak concurrency, plus a check that the quota is applied.

## Error Handling

| Error | Code | Solution |
|-------|------|----------|
| `TOO_MANY_SIMULTANEOUS_QUERIES` | 202 | Reduce client concurrency or raise `max_concurrent_queries`; retry with backoff |
| `MEMORY_LIMIT_EXCEEDED` | 241 | Lower `max_threads`, add query filters, reduce `max_memory_usage` scope |
| `TIMEOUT_EXCEEDED` | 159 | Increase `max_execution_time` or optimize the query |
| `TOO_MANY_PARTS` | 252 | Batch inserts via the insert buffer, wait for merges |

The retry wrapper in [references/implementation.md](references/implementation.md)
treats codes 202, 159, and network errors as retryable.

## Examples

Three worked end-to-end scenarios live in
[references/examples.md](references/examples.md):

1. **Cap a reporting service at 5 concurrent queries** — wrap every dashboard
   tile's query in the `p-queue` limiter.
2. **Survive a concurrency spike** — `queryWithRetry` absorbs code-202 bursts
   with exponential backoff + jitter instead of returning 500s.
3. **High-throughput ingest without `TOO_MANY_PARTS`** — `InsertBuffer` batches
   a firehose into a few large inserts.

## Resources

- [Server Settings](https://clickhouse.com/docs/operations/server-configuration-parameters/settings)
- [Query Complexity Limits](https://clickhouse.com/docs/operations/settings/query-complexity)
- [Quotas](https://clickhouse.com/docs/operations/quotas)
- [references/implementation.md](references/implementation.md) — full server + client code
- [references/examples.md](references/examples.md) — monitoring queries + worked scenarios

## Next Steps

For security hardening (users, roles, TLS), see the `clickhouse-security-basics`
skill. For query-level performance work, see `clickhouse-performance-tuning`.
