# Client Module & Query Functions

A singleton ClickHouse client keeps connection pooling and compression settings in one
place; named query functions live under `src/clickhouse/queries/` and always read from
the aggregate tables (never the raw table). Parameterized queries (`{tid:UInt32}`) are
mandatory — they prevent injection and let ClickHouse cache the query shape.

```typescript
// src/clickhouse/client.ts
import { createClient, ClickHouseClient } from '@clickhouse/client';

let instance: ClickHouseClient | null = null;

export function getClient(): ClickHouseClient {
  if (!instance) {
    instance = createClient({
      url: process.env.CLICKHOUSE_HOST!,
      username: process.env.CLICKHOUSE_USER!,
      password: process.env.CLICKHOUSE_PASSWORD!,
      database: process.env.CLICKHOUSE_DATABASE ?? 'analytics',
      max_open_connections: Number(process.env.CH_MAX_CONNECTIONS ?? 10),
      request_timeout: 30_000,
      compression: { request: true, response: true },
    });
  }
  return instance;
}

// src/clickhouse/queries/dashboards.ts
export async function getTenantDashboard(tenantId: number, days = 30) {
  const client = getClient();
  const rs = await client.query({
    query: `
      SELECT date, sum(total) AS events, uniqMerge(users) AS unique_users
      FROM analytics.events_daily
      WHERE tenant_id = {tid:UInt32} AND date >= today() - {days:UInt32}
      GROUP BY date ORDER BY date
    `,
    query_params: { tid: tenantId, days },
    format: 'JSONEachRow',
  });
  return rs.json<{ date: string; events: string; unique_users: string }>();
}
```

## Notes

- **Singleton** — one client per process reuses the connection pool; recreating a client
  per request exhausts `max_open_connections` under load.
- **`uniqMerge`** finalizes the partial `AggregateFunction(uniq, …)` state stored in
  `events_daily`, producing the true distinct-user count across rolled-up rows.
- **`JSONEachRow`** streams one JSON object per row — easy to debug and well supported by
  the official client. Numeric aggregates arrive as strings to preserve 64-bit precision.
