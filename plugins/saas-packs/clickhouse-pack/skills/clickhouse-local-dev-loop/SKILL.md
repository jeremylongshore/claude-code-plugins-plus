---
name: clickhouse-local-dev-loop
description: |
  Run ClickHouse locally with Docker, configure test fixtures, and iterate fast.
  Use when setting up a local ClickHouse dev environment, writing integration tests,
  or running ClickHouse in Docker Compose.
  Trigger: "clickhouse local dev", "clickhouse docker", "clickhouse dev environment",
  "run clickhouse locally", "clickhouse docker compose".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(docker:*), Bash(docker-compose:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Local Dev Loop

## Overview

Run ClickHouse in Docker for local development with fast schema iteration,
seed data, and integration testing using vitest.

## Prerequisites

- Docker or Docker Compose installed
- Node.js 18+ with `@clickhouse/client`

## Instructions

### Step 1: Docker Compose Setup

```yaml
# docker-compose.yml
services:
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    ports:
      - "8123:8123"   # HTTP interface
      - "9000:9000"   # Native TCP (clickhouse-client CLI)
    volumes:
      - clickhouse-data:/var/lib/clickhouse
      - ./init-db:/docker-entrypoint-initdb.d  # Auto-run SQL on first start
    environment:
      CLICKHOUSE_USER: default
      CLICKHOUSE_PASSWORD: dev_password
      CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1  # Enable SQL-based user management
    ulimits:
      nofile:
        soft: 262144
        hard: 262144

volumes:
  clickhouse-data:
```

```bash
docker compose up -d
# Verify: curl http://localhost:8123/ping   → "Ok.\n"
```

### Step 2: Init Script (Auto-Run on First Start)

```sql
-- init-db/001-schema.sql
CREATE DATABASE IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.events (
    event_id    UUID DEFAULT generateUUIDv4(),
    event_type  LowCardinality(String),
    user_id     UInt64,
    properties  String,     -- JSON string
    created_at  DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (event_type, created_at)
PARTITION BY toYYYYMM(created_at);
```

### Step 3: Seed Data Script

```typescript
// scripts/seed.ts
import { createClient } from '@clickhouse/client';

const client = createClient({
  url: 'http://localhost:8123',
  username: 'default',
  password: 'dev_password',
  database: 'app',
});

const events = Array.from({ length: 1000 }, (_, i) => ({
  event_type: ['page_view', 'click', 'signup', 'purchase'][i % 4],
  user_id: Math.floor(Math.random() * 100) + 1,
  properties: JSON.stringify({ index: i }),
  created_at: new Date(Date.now() - Math.random() * 86400000 * 30)
    .toISOString()
    .replace('T', ' ')
    .slice(0, 19),
}));

await client.insert({ table: 'events', values: events, format: 'JSONEachRow' });
console.log(`Seeded ${events.length} events`);
await client.close();
```

### Step 4: Project Structure

```
my-clickhouse-app/
├── docker-compose.yml
├── init-db/
│   └── 001-schema.sql
├── scripts/
│   └── seed.ts
├── src/
│   ├── db.ts              # Client singleton
│   └── queries.ts          # Named query functions
├── tests/
│   ├── setup.ts            # Test lifecycle (truncate tables)
│   └── events.test.ts
├── .env.local              # Local creds (git-ignored)
├── .env.example
└── package.json
```

### Step 5: Client Singleton

```typescript
// src/db.ts
import { createClient, ClickHouseClient } from '@clickhouse/client';

let client: ClickHouseClient | null = null;

export function getClient(): ClickHouseClient {
  if (!client) {
    client = createClient({
      url: process.env.CLICKHOUSE_HOST ?? 'http://localhost:8123',
      username: process.env.CLICKHOUSE_USER ?? 'default',
      password: process.env.CLICKHOUSE_PASSWORD ?? 'dev_password',
      database: process.env.CLICKHOUSE_DATABASE ?? 'app',
    });
  }
  return client;
}
```

### Step 6: Integration Testing with Vitest

```typescript
// tests/setup.ts
import { getClient } from '../src/db';
import { beforeEach, afterAll } from 'vitest';

beforeEach(async () => {
  const client = getClient();
  // TRUNCATE is lightweight — drops parts without logging
  await client.command({ query: 'TRUNCATE TABLE IF EXISTS app.events' });
});

afterAll(async () => {
  await getClient().close();
});
```

```typescript
// tests/events.test.ts
import { describe, it, expect } from 'vitest';
import { getClient } from '../src/db';

describe('ClickHouse events', () => {
  it('inserts and queries events', async () => {
    const client = getClient();

    await client.insert({
      table: 'events',
      values: [
        { event_type: 'test', user_id: 1, properties: '{}' },
        { event_type: 'test', user_id: 2, properties: '{}' },
      ],
      format: 'JSONEachRow',
    });

    const rs = await client.query({
      query: 'SELECT count() AS cnt FROM events',
      format: 'JSONEachRow',
    });
    const [row] = await rs.json<{ cnt: string }>();
    expect(Number(row.cnt)).toBe(2);
  });
});
```

### Step 7: Package Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "db:up": "docker compose up -d",
    "db:down": "docker compose down",
    "db:reset": "docker compose down -v && docker compose up -d",
    "db:seed": "tsx scripts/seed.ts",
    "db:shell": "docker exec -it $(docker compose ps -q clickhouse) clickhouse-client --password dev_password",
    "test": "vitest",
    "test:watch": "vitest --watch"
  }
}
```

## Useful CLI Commands

```bash
# Interactive SQL shell
docker exec -it <container> clickhouse-client --password dev_password

# Run a query from host via HTTP
curl 'http://localhost:8123/?query=SELECT+count()+FROM+app.events'

# Check running queries
curl 'http://localhost:8123/?query=SELECT+*+FROM+system.processes+FORMAT+PrettyCompact'

# Watch merges
curl 'http://localhost:8123/?query=SELECT+*+FROM+system.merges+FORMAT+PrettyCompact'
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused :8123` | Container not running | `docker compose up -d` |
| `READONLY` | User lacks write perms | Set `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` |
| `Too many parts` | Tiny frequent inserts | Batch inserts or increase `parts_to_throw_insert` |
| `Memory limit exceeded` | Large query on small container | Add `--memory 4g` to Docker |

## Resources

- [ClickHouse Docker Image](https://hub.docker.com/r/clickhouse/clickhouse-server)
- [clickhouse-client CLI](https://clickhouse.com/docs/interfaces/cli)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps

See `clickhouse-sdk-patterns` for production-ready client patterns.
