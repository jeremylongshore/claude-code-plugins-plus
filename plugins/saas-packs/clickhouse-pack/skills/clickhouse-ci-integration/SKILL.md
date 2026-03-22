---
name: clickhouse-ci-integration
description: |
  Run ClickHouse integration tests in CI with GitHub Actions and Docker containers.
  Use when setting up automated testing against a real ClickHouse instance,
  configuring CI pipelines, or implementing schema validation in CI.
  Trigger: "clickhouse CI", "clickhouse GitHub Actions", "clickhouse integration tests",
  "test clickhouse in CI", "clickhouse automated testing".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse CI Integration

## Overview

Run integration tests against a real ClickHouse server in GitHub Actions using
Docker service containers. No mocks needed for schema and query validation.

## Prerequisites

- GitHub repository with Actions enabled
- `@clickhouse/client` in project dependencies
- Test suite (vitest or jest)

## Instructions

### Step 1: GitHub Actions Workflow with ClickHouse Service

```yaml
# .github/workflows/clickhouse-tests.yml
name: ClickHouse Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      clickhouse:
        image: clickhouse/clickhouse-server:latest
        ports:
          - 8123:8123
          - 9000:9000
        options: >-
          --health-cmd "wget --no-verbose --tries=1 --spider http://localhost:8123/ping || exit 1"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      CLICKHOUSE_HOST: http://localhost:8123
      CLICKHOUSE_USER: default
      CLICKHOUSE_PASSWORD: ""

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - run: npm ci

      # Apply schema before tests
      - name: Apply schema
        run: |
          curl -s 'http://localhost:8123/' -d 'CREATE DATABASE IF NOT EXISTS test_db'
          for f in init-db/*.sql; do
            echo "Applying $f..."
            curl -s 'http://localhost:8123/?database=test_db' --data-binary @"$f"
          done

      - name: Run unit tests
        run: npm test -- --coverage

      - name: Run integration tests
        run: npm run test:integration
```

### Step 2: Integration Test Setup

```typescript
// tests/setup-integration.ts
import { createClient, ClickHouseClient } from '@clickhouse/client';
import { beforeAll, afterAll, beforeEach } from 'vitest';

let client: ClickHouseClient;

beforeAll(async () => {
  client = createClient({
    url: process.env.CLICKHOUSE_HOST ?? 'http://localhost:8123',
    database: 'test_db',
  });

  // Verify connection
  const { success } = await client.ping();
  if (!success) throw new Error('ClickHouse not reachable');
});

beforeEach(async () => {
  // Clean test data between tests
  await client.command({ query: 'TRUNCATE TABLE IF EXISTS test_db.events' });
});

afterAll(async () => {
  await client.close();
});

export { client };
```

### Step 3: Write Real Integration Tests

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

### Step 4: Schema Validation in CI

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

### Step 5: Package Scripts

```json
{
  "scripts": {
    "test": "vitest run",
    "test:integration": "vitest run --config vitest.integration.config.ts",
    "test:ci": "vitest run --coverage --reporter=junit --outputFile=test-results.xml"
  }
}
```

## CI Matrix for Multiple ClickHouse Versions

```yaml
strategy:
  matrix:
    clickhouse-version: ["24.3", "24.8", "latest"]

services:
  clickhouse:
    image: clickhouse/clickhouse-server:${{ matrix.clickhouse-version }}
    ports:
      - 8123:8123
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Service not healthy | Slow container start | Increase `health-retries` |
| Schema not found | Init scripts not run | Run schema step before tests |
| Flaky test order | Shared state | Use `beforeEach` with TRUNCATE |
| Port conflict | Another process | Use random port mapping |

## Resources

- [GitHub Actions Service Containers](https://docs.github.com/en/actions/using-containerized-services)
- [ClickHouse Docker Image](https://hub.docker.com/r/clickhouse/clickhouse-server)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps

For deployment patterns, see `clickhouse-deploy-integration`.
