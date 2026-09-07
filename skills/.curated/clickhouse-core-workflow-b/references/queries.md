# Analytical Query Patterns

Ready-to-adapt SQL for the most common ClickHouse analytics workloads. Each
query targets the `analytics.events` table created in `clickhouse-core-workflow-a`.

## Top events by tenant

```sql
-- Top events by tenant in the last 7 days
SELECT
    tenant_id,
    event_type,
    count()                  AS event_count,
    uniqExact(user_id)       AS unique_users,
    min(created_at)          AS first_seen,
    max(created_at)          AS last_seen
FROM analytics.events
WHERE created_at >= now() - INTERVAL 7 DAY
GROUP BY tenant_id, event_type
ORDER BY event_count DESC
LIMIT 100;
```

## Funnel analysis

```sql
-- Funnel analysis: signup → activation → purchase
SELECT
    level,
    count() AS users
FROM (
    SELECT
        user_id,
        groupArray(event_type) AS journey
    FROM analytics.events
    WHERE event_type IN ('signup', 'activation', 'purchase')
      AND created_at >= today() - 30
    GROUP BY user_id
)
ARRAY JOIN arrayEnumerate(journey) AS level
GROUP BY level
ORDER BY level;
```

## Retention

```sql
-- Retention: users active this week who were also active last week
SELECT
    count(DISTINCT curr.user_id) AS retained_users
FROM analytics.events AS curr
INNER JOIN analytics.events AS prev
    ON curr.user_id = prev.user_id
WHERE curr.created_at >= toMonday(today())
  AND prev.created_at >= toMonday(today()) - 7
  AND prev.created_at < toMonday(today());
```

## Parameterized queries in Node.js

```typescript
// Use {param:Type} syntax for safe parameterized queries
const rs = await client.query({
  query: `
    SELECT event_type, count() AS cnt
    FROM analytics.events
    WHERE tenant_id = {tenant_id:UInt32}
      AND created_at >= {from_date:DateTime}
    GROUP BY event_type
    ORDER BY cnt DESC
  `,
  query_params: {
    tenant_id: 1,
    from_date: '2025-01-01 00:00:00',
  },
  format: 'JSONEachRow',
});
const rows = await rs.json();
```
