---
name: snowflake-sdk-patterns
description: |
  Apply production-ready Snowflake SDK patterns for snowflake-sdk and snowflake-connector-python.
  Use when implementing connection pooling, async execute wrappers, streaming results,
  or establishing team coding standards for Snowflake.
  Trigger with phrases like "snowflake SDK patterns", "snowflake best practices",
  "snowflake code patterns", "idiomatic snowflake", "snowflake connection pool".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake SDK Patterns

## Overview

Production-ready patterns for `snowflake-sdk` (Node.js) and `snowflake-connector-python` using real driver APIs.

## Prerequisites

- Completed `snowflake-install-auth` setup
- Understanding of callback-to-promise conversion patterns
- Familiarity with Snowflake's callback-based Node.js API

## Instructions

### Step 1: Connection Pool (Node.js)

```typescript
// src/snowflake/pool.ts
import snowflake from 'snowflake-sdk';

interface PoolConfig {
  max: number;
  idleTimeoutMs: number;
}

class SnowflakePool {
  private pool: snowflake.Connection[] = [];
  private available: snowflake.Connection[] = [];
  private waiting: ((conn: snowflake.Connection) => void)[] = [];
  private config: PoolConfig;

  constructor(
    private connConfig: snowflake.ConnectionOptions,
    config: Partial<PoolConfig> = {}
  ) {
    this.config = { max: 10, idleTimeoutMs: 60000, ...config };
  }

  async acquire(): Promise<snowflake.Connection> {
    // Return available connection
    if (this.available.length > 0) {
      return this.available.pop()!;
    }
    // Create new if under limit
    if (this.pool.length < this.config.max) {
      const conn = snowflake.createConnection(this.connConfig);
      await new Promise<void>((resolve, reject) => {
        conn.connect((err) => (err ? reject(err) : resolve()));
      });
      this.pool.push(conn);
      return conn;
    }
    // Wait for one to become available
    return new Promise((resolve) => {
      this.waiting.push(resolve);
    });
  }

  release(conn: snowflake.Connection): void {
    if (this.waiting.length > 0) {
      const next = this.waiting.shift()!;
      next(conn);
    } else {
      this.available.push(conn);
    }
  }

  async withConnection<T>(fn: (conn: snowflake.Connection) => Promise<T>): Promise<T> {
    const conn = await this.acquire();
    try {
      return await fn(conn);
    } finally {
      this.release(conn);
    }
  }
}

// Singleton pool
export const pool = new SnowflakePool({
  account: process.env.SNOWFLAKE_ACCOUNT!,
  username: process.env.SNOWFLAKE_USER!,
  password: process.env.SNOWFLAKE_PASSWORD!,
  warehouse: process.env.SNOWFLAKE_WAREHOUSE || 'COMPUTE_WH',
  database: process.env.SNOWFLAKE_DATABASE!,
  schema: process.env.SNOWFLAKE_SCHEMA || 'PUBLIC',
});
```

### Step 2: Promise-Based Query Helper

```typescript
// src/snowflake/query.ts
import snowflake from 'snowflake-sdk';

interface QueryResult<T = Record<string, any>> {
  rows: T[];
  statement: snowflake.Statement;
  sqlText: string;
}

export function query<T = Record<string, any>>(
  conn: snowflake.Connection,
  sqlText: string,
  binds?: snowflake.Binds
): Promise<QueryResult<T>> {
  return new Promise((resolve, reject) => {
    conn.execute({
      sqlText,
      binds,
      complete: (err, stmt, rows) => {
        if (err) {
          reject(Object.assign(err, { sqlText }));
        } else {
          resolve({ rows: (rows || []) as T[], statement: stmt, sqlText });
        }
      },
    });
  });
}

// Multi-statement execution
export async function multiQuery(
  conn: snowflake.Connection,
  statements: string[]
): Promise<QueryResult[]> {
  const results: QueryResult[] = [];
  for (const sql of statements) {
    results.push(await query(conn, sql));
  }
  return results;
}
```

### Step 3: Streaming for Large Result Sets

```typescript
// src/snowflake/stream.ts
export async function* streamQuery<T = Record<string, any>>(
  conn: snowflake.Connection,
  sqlText: string,
  binds?: snowflake.Binds
): AsyncGenerator<T> {
  const stmt = await new Promise<snowflake.Statement>((resolve, reject) => {
    conn.execute({
      sqlText,
      binds,
      streamResult: true,
      complete: (err, stmt) => {
        if (err) reject(err);
        else resolve(stmt);
      },
    });
  });

  const stream = stmt.streamRows();
  for await (const row of stream) {
    yield row as T;
  }
}

// Usage: process millions of rows without memory pressure
// for await (const row of streamQuery(conn, 'SELECT * FROM big_table')) {
//   await processRow(row);
// }
```

### Step 4: Python Context Manager Pattern

```python
# src/snowflake_pool.py
import snowflake.connector
from contextlib import contextmanager
from typing import Generator, Any

class SnowflakePool:
    def __init__(self, **conn_params):
        self._params = conn_params

    @contextmanager
    def connection(self) -> Generator[snowflake.connector.SnowflakeConnection, None, None]:
        conn = snowflake.connector.connect(**self._params)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def cursor(self) -> Generator[snowflake.connector.cursor.SnowflakeCursor, None, None]:
        with self.connection() as conn:
            cur = conn.cursor()
            try:
                yield cur
            finally:
                cur.close()

    def execute(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def execute_many(self, sql: str, params_list: list[tuple]) -> int:
        """Batch insert — much faster than individual inserts."""
        with self.cursor() as cur:
            cur.executemany(sql, params_list)
            return cur.rowcount

# Usage
pool = SnowflakePool(
    account=os.environ['SNOWFLAKE_ACCOUNT'],
    user=os.environ['SNOWFLAKE_USER'],
    password=os.environ['SNOWFLAKE_PASSWORD'],
    warehouse='COMPUTE_WH',
    database='MY_DB',
    schema='PUBLIC',
)

users = pool.execute("SELECT * FROM users WHERE status = %s", ('active',))
```

### Step 5: Error Handling Wrapper

```typescript
// src/snowflake/errors.ts
export class SnowflakeQueryError extends Error {
  constructor(
    message: string,
    public readonly sqlState: string,
    public readonly code: number,
    public readonly sqlText: string,
    public readonly retryable: boolean
  ) {
    super(message);
    this.name = 'SnowflakeQueryError';
  }
}

const RETRYABLE_CODES = new Set([
  390114, // Connection token expired — reconnect
  390503, // Service unavailable
]);

export async function safeQuery<T>(
  conn: snowflake.Connection,
  sqlText: string,
  binds?: snowflake.Binds,
  maxRetries = 3
): Promise<T[]> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const { rows } = await query<T>(conn, sqlText, binds);
      return rows;
    } catch (err: any) {
      const retryable = RETRYABLE_CODES.has(err.code);
      if (!retryable || attempt === maxRetries) {
        throw new SnowflakeQueryError(
          err.message, err.sqlState, err.code, sqlText, retryable
        );
      }
      const delay = 1000 * Math.pow(2, attempt - 1);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Connection pool | High concurrency apps | Reuses connections, prevents exhaustion |
| Promise wrapper | All Node.js code | Clean async/await instead of callbacks |
| Streaming | Large result sets (>100K rows) | Constant memory usage |
| Context manager | All Python code | Guarantees connection cleanup |
| Retry with backoff | Transient failures | Handles token expiry, service blips |

## Resources

- [Node.js Driver Execute](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver-execute)
- [Node.js Consuming Results](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver-consume)
- [Python Connector API](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api)

## Next Steps

Apply patterns in `snowflake-core-workflow-a` for real-world data pipeline usage.
