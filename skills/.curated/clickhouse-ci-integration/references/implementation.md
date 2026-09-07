# ClickHouse CI Integration — Full Walkthrough

Deep reference for the `clickhouse-ci-integration` skill. SKILL.md carries the
high-level workflow and the workflow skeleton; this file carries the complete
test-harness setup, schema-validation checks, package scripts, and the
multi-version CI matrix.

## Step 1: GitHub Actions Workflow with ClickHouse Service

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

The `default` user with an empty `CLICKHOUSE_PASSWORD` is correct for the
ephemeral CI service container (it lives only for the job and is never exposed
publicly). For any non-CI target, source credentials from GitHub Actions
secrets (`${{ secrets.CLICKHOUSE_PASSWORD }}`) rather than inlining them.

## Step 2: Integration Test Setup

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

## Step 3: Package Scripts

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

Run the suite against several server versions to catch behavioral drift before
an upgrade lands in production:

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

For the concrete integration + schema-validation test files these scripts and
this workflow run, see [examples.md](examples.md).
