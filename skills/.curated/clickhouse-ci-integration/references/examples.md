# ClickHouse CI Integration — Example Test Files

Complete, runnable example test files for the `clickhouse-ci-integration`
skill. Both files import the shared `client` created in
[implementation.md](implementation.md) Step 2 (`tests/setup-integration.ts`).

## Real Integration Tests

Exercises insert → aggregate query → assertion against the live service
container, plus parameterized-query and empty-result behavior.

```typescript
// tests/events.integration.test.ts
import { describe, it, expect } from 'vitest';
import { client } from './setup-integration';

describe('Events table', () => {
  it('creates and queries events', async () => {
    // Insert test data
    await client.insert({
      table: 'events',
      values: [
        { event_type: 'page_view', user_id: 1, properties: '{"url":"/home"}' },
        { event_type: 'click', user_id: 1, properties: '{"btn":"cta"}' },
        { event_type: 'page_view', user_id: 2, properties: '{"url":"/pricing"}' },
      ],
      format: 'JSONEachRow',
    });

    // Query and validate
    const rs = await client.query({
      query: `
        SELECT event_type, count() AS cnt, uniqExact(user_id) AS users
        FROM events GROUP BY event_type ORDER BY cnt DESC
      `,
      format: 'JSONEachRow',
    });
    const rows = await rs.json<{ event_type: string; cnt: string; users: string }>();

    expect(rows).toHaveLength(2);
    expect(rows[0]).toMatchObject({ event_type: 'page_view', cnt: '2', users: '2' });
    expect(rows[1]).toMatchObject({ event_type: 'click', cnt: '1', users: '1' });
  });

  it('validates parameterized queries prevent injection', async () => {
    await client.insert({
      table: 'events',
      values: [{ event_type: 'test', user_id: 42, properties: '{}' }],
      format: 'JSONEachRow',
    });

    const rs = await client.query({
      query: 'SELECT count() AS cnt FROM events WHERE user_id = {uid:UInt64}',
      query_params: { uid: 42 },
      format: 'JSONEachRow',
    });
    const [row] = await rs.json<{ cnt: string }>();
    expect(Number(row.cnt)).toBe(1);
  });

  it('handles empty results gracefully', async () => {
    const rs = await client.query({
      query: 'SELECT * FROM events WHERE user_id = 999999',
      format: 'JSONEachRow',
    });
    const rows = await rs.json();
    expect(rows).toEqual([]);
  });
});
```

## Schema Validation in CI

Asserts the deployed schema (column types, table engine) matches expectations
by querying ClickHouse's `system.columns` / `system.tables` catalog — catches
a drifted migration before application tests even run.

```typescript
// tests/schema.integration.test.ts
import { describe, it, expect } from 'vitest';
import { client } from './setup-integration';

describe('Schema validation', () => {
  it('events table has expected columns', async () => {
    const rs = await client.query({
      query: "SELECT name, type FROM system.columns WHERE database='test_db' AND table='events'",
      format: 'JSONEachRow',
    });
    const columns = await rs.json<{ name: string; type: string }>();
    const colMap = new Map(columns.map((c) => [c.name, c.type]));

    expect(colMap.get('event_type')).toBe("LowCardinality(String)");
    expect(colMap.get('user_id')).toBe('UInt64');
    expect(colMap.get('created_at')).toMatch(/DateTime/);
  });

  it('events table uses MergeTree engine', async () => {
    const rs = await client.query({
      query: "SELECT engine FROM system.tables WHERE database='test_db' AND name='events'",
      format: 'JSONEachRow',
    });
    const [row] = await rs.json<{ engine: string }>();
    expect(row.engine).toBe('MergeTree');
  });
});
```
