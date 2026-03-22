---
name: snowflake-local-dev-loop
description: |
  Configure Snowflake local development with testing, mocking, and fast iteration.
  Use when setting up dev environment, writing tests against Snowflake,
  or establishing a fast iteration cycle with SnowSQL and dev warehouses.
  Trigger with phrases like "snowflake dev setup", "snowflake local development",
  "snowflake dev environment", "develop with snowflake", "snowflake testing".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for Snowflake with separate dev warehouses, mocked tests, and SnowSQL for rapid iteration.

## Prerequisites

- Completed `snowflake-install-auth` setup
- Node.js 18+ or Python 3.9+
- A dedicated dev warehouse (e.g., `DEV_WH_XS`) with auto-suspend

## Instructions

### Step 1: Create Dev-Specific Snowflake Objects

```sql
-- Run once to set up isolated dev environment
CREATE WAREHOUSE IF NOT EXISTS DEV_WH_XS
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS DEV_DB;
CREATE SCHEMA IF NOT EXISTS DEV_DB.SANDBOX;

-- Grant to dev role
GRANT USAGE ON WAREHOUSE DEV_WH_XS TO ROLE DEV_ROLE;
GRANT ALL ON DATABASE DEV_DB TO ROLE DEV_ROLE;
```

### Step 2: Project Structure

```
my-snowflake-project/
├── src/
│   ├── snowflake/
│   │   ├── connection.ts     # Connection wrapper with connectAsync
│   │   ├── queries.ts        # Typed query functions
│   │   └── types.ts          # Row type definitions
│   └── index.ts
├── tests/
│   ├── unit/
│   │   └── queries.test.ts   # Mocked — no Snowflake needed
│   └── integration/
│       └── snowflake.test.ts # Requires SNOWFLAKE_* env vars
├── sql/
│   ├── migrations/           # Versioned DDL scripts
│   │   ├── V001__create_users.sql
│   │   └── V002__add_orders.sql
│   └── seeds/
│       └── dev-data.sql      # Sample data for dev
├── .env.local                # Local secrets (git-ignored)
├── .env.example              # Template for team
└── package.json
```

### Step 3: Connection Wrapper with Async/Await

```typescript
// src/snowflake/connection.ts
import snowflake from 'snowflake-sdk';

// Enable promise-based API
snowflake.configure({ logLevel: 'WARN' });

export function createSnowflakeConnection() {
  return snowflake.createConnection({
    account: process.env.SNOWFLAKE_ACCOUNT!,
    username: process.env.SNOWFLAKE_USER!,
    password: process.env.SNOWFLAKE_PASSWORD!,
    warehouse: process.env.SNOWFLAKE_WAREHOUSE || 'DEV_WH_XS',
    database: process.env.SNOWFLAKE_DATABASE || 'DEV_DB',
    schema: process.env.SNOWFLAKE_SCHEMA || 'SANDBOX',
    role: process.env.SNOWFLAKE_ROLE || 'DEV_ROLE',
  });
}

// Promise wrapper for connection.execute
export function executeQuery(
  conn: snowflake.Connection,
  sqlText: string,
  binds?: any[]
): Promise<any[]> {
  return new Promise((resolve, reject) => {
    conn.execute({
      sqlText,
      binds,
      complete: (err, stmt, rows) => {
        if (err) reject(err);
        else resolve(rows || []);
      },
    });
  });
}

// Promise wrapper for connect
export function connectAsync(
  conn: snowflake.Connection
): Promise<snowflake.Connection> {
  return new Promise((resolve, reject) => {
    conn.connect((err, conn) => {
      if (err) reject(err);
      else resolve(conn);
    });
  });
}
```

### Step 4: Unit Tests with Mocked Snowflake

```typescript
// tests/unit/queries.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the snowflake-sdk module
vi.mock('snowflake-sdk', () => ({
  default: {
    configure: vi.fn(),
    createConnection: vi.fn(() => ({
      connect: vi.fn((cb) => cb(null, { getId: () => 'mock-id' })),
      execute: vi.fn(({ sqlText, complete }) => {
        // Return mock data based on query
        if (sqlText.includes('CURRENT_WAREHOUSE')) {
          complete(null, {}, [{ WAREHOUSE: 'DEV_WH_XS' }]);
        } else if (sqlText.includes('SELECT')) {
          complete(null, {}, [
            { ID: 1, NAME: 'Alice' },
            { ID: 2, NAME: 'Bob' },
          ]);
        } else {
          complete(null, { getNumUpdatedRows: () => 1 }, []);
        }
      }),
      destroy: vi.fn((cb) => cb(null)),
    })),
  },
}));

import { createSnowflakeConnection, executeQuery, connectAsync } from '../../src/snowflake/connection';

describe('Snowflake Queries', () => {
  it('should connect and execute a query', async () => {
    const conn = createSnowflakeConnection();
    await connectAsync(conn);
    const rows = await executeQuery(conn, 'SELECT * FROM USERS');
    expect(rows).toHaveLength(2);
    expect(rows[0].NAME).toBe('Alice');
  });
});
```

### Step 5: Integration Tests (Against Real Snowflake)

```typescript
// tests/integration/snowflake.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { createSnowflakeConnection, connectAsync, executeQuery } from '../../src/snowflake/connection';

describe.skipIf(!process.env.SNOWFLAKE_ACCOUNT)('Snowflake Integration', () => {
  let conn: any;

  beforeAll(async () => {
    conn = createSnowflakeConnection();
    await connectAsync(conn);
    // Create temp table for test isolation
    await executeQuery(conn, `
      CREATE TEMPORARY TABLE test_users (
        id INTEGER AUTOINCREMENT, name VARCHAR(100)
      )
    `);
  });

  afterAll(async () => {
    conn?.destroy(() => {});
  });

  it('should insert and query data', async () => {
    await executeQuery(conn,
      'INSERT INTO test_users (name) VALUES (?)', ['TestUser']
    );
    const rows = await executeQuery(conn, 'SELECT * FROM test_users');
    expect(rows.length).toBeGreaterThan(0);
    expect(rows[0].NAME).toBe('TestUser');
  });
});
```

### Step 6: SnowSQL for Quick Iteration

```bash
# Install SnowSQL CLI
brew install --cask snowflake-snowsql  # macOS

# Configure named connection
cat >> ~/.snowsql/config << 'EOF'
[connections.dev]
accountname = myorg-myaccount
username = my_user
dbname = DEV_DB
schemaname = SANDBOX
warehousename = DEV_WH_XS
rolename = DEV_ROLE
EOF

# Quick queries
snowsql -c dev -q "SELECT COUNT(*) FROM my_table"

# Run migration scripts
snowsql -c dev -f sql/migrations/V001__create_users.sql
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `000606: No active warehouse` | Dev warehouse suspended | Set `AUTO_RESUME = TRUE` on warehouse |
| `Module not found: snowflake-sdk` | Not installed | Run `npm install snowflake-sdk` |
| `Tests timeout` | Warehouse resuming from suspend | Increase test timeout to 30s, or pre-warm |
| `002003: Object does not exist` | Wrong database/schema context | Check `.env.local` DB and SCHEMA values |

## Resources

- [Node.js Driver Options](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver-options)
- [Vitest Documentation](https://vitest.dev/)
- [SnowSQL Reference](https://docs.snowflake.com/en/user-guide/snowsql)

## Next Steps

See `snowflake-sdk-patterns` for production-ready code patterns.
