---
name: snowflake-hello-world
description: |
  Create a minimal working Snowflake example with real SQL queries.
  Use when testing your Snowflake setup, running first queries,
  or learning basic snowflake-sdk and snowflake-connector-python patterns.
  Trigger with phrases like "snowflake hello world", "snowflake example",
  "snowflake quick start", "first snowflake query".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Hello World

## Overview

Minimal working examples demonstrating core Snowflake operations: connect, query, create objects, load data.

## Prerequisites

- Completed `snowflake-install-auth` setup
- Valid credentials configured in environment
- A warehouse available (e.g., `COMPUTE_WH`)

## Instructions

### Step 1: Connect and Query (Node.js)

```typescript
// hello-snowflake.ts
import snowflake from 'snowflake-sdk';

const connection = snowflake.createConnection({
  account: process.env.SNOWFLAKE_ACCOUNT!,
  username: process.env.SNOWFLAKE_USER!,
  password: process.env.SNOWFLAKE_PASSWORD!,
  warehouse: 'COMPUTE_WH',
  database: 'DEMO_DB',
  schema: 'PUBLIC',
});

connection.connect((err) => {
  if (err) {
    console.error('Connection failed:', err.message);
    process.exit(1);
  }
  console.log('Connected to Snowflake!');

  // Run a simple query
  connection.execute({
    sqlText: `SELECT CURRENT_TIMESTAMP() AS now,
              CURRENT_WAREHOUSE() AS warehouse,
              CURRENT_DATABASE() AS database,
              CURRENT_ROLE() AS role`,
    complete: (err, stmt, rows) => {
      if (err) {
        console.error('Query failed:', err.message);
        return;
      }
      console.log('Query result:', rows);
      connection.destroy((err) => {
        if (err) console.error('Disconnect error:', err.message);
      });
    },
  });
});
```

### Step 2: Connect and Query (Python)

```python
# hello_snowflake.py
import snowflake.connector
import os

conn = snowflake.connector.connect(
    account=os.environ['SNOWFLAKE_ACCOUNT'],
    user=os.environ['SNOWFLAKE_USER'],
    password=os.environ['SNOWFLAKE_PASSWORD'],
    warehouse='COMPUTE_WH',
    database='DEMO_DB',
    schema='PUBLIC',
)

try:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT CURRENT_TIMESTAMP() AS now,
               CURRENT_WAREHOUSE() AS warehouse,
               CURRENT_DATABASE() AS database,
               CURRENT_ROLE() AS role
    """)
    for row in cursor:
        print(f"Time: {row[0]}, Warehouse: {row[1]}, DB: {row[2]}, Role: {row[3]}")
finally:
    conn.close()
```

### Step 3: Create Database Objects

```sql
-- Run via connection.execute() or snowflake worksheet
CREATE DATABASE IF NOT EXISTS DEMO_DB;
CREATE SCHEMA IF NOT EXISTS DEMO_DB.MY_SCHEMA;

CREATE OR REPLACE TABLE DEMO_DB.MY_SCHEMA.USERS (
    id INTEGER AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO DEMO_DB.MY_SCHEMA.USERS (name, email)
VALUES ('Alice', 'alice@example.com'),
       ('Bob', 'bob@example.com');

SELECT * FROM DEMO_DB.MY_SCHEMA.USERS;
```

### Step 4: Parameterized Queries (Node.js)

```typescript
// Insert with bind parameters — prevents SQL injection
connection.execute({
  sqlText: 'INSERT INTO DEMO_DB.MY_SCHEMA.USERS (name, email) VALUES (?, ?)',
  binds: ['Charlie', 'charlie@example.com'],
  complete: (err, stmt, rows) => {
    if (err) {
      console.error('Insert failed:', err.message);
      return;
    }
    console.log('Inserted rows:', stmt.getNumUpdatedRows());
  },
});

// Fetch results with streaming for large datasets
connection.execute({
  sqlText: 'SELECT * FROM DEMO_DB.MY_SCHEMA.USERS ORDER BY created_at DESC',
  streamResult: true,
  complete: (err, stmt) => {
    if (err) { console.error(err.message); return; }
    const stream = stmt.streamRows();
    stream.on('data', (row) => console.log('Row:', row));
    stream.on('end', () => console.log('All rows fetched'));
    stream.on('error', (err) => console.error('Stream error:', err));
  },
});
```

### Step 5: Parameterized Queries (Python)

```python
# Insert with bind parameters
cursor.execute(
    "INSERT INTO DEMO_DB.MY_SCHEMA.USERS (name, email) VALUES (%s, %s)",
    ('Charlie', 'charlie@example.com')
)
print(f"Inserted {cursor.rowcount} row(s)")

# Fetch all results
cursor.execute("SELECT * FROM DEMO_DB.MY_SCHEMA.USERS ORDER BY created_at DESC")
results = cursor.fetchall()
for row in results:
    print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}")

# Fetch as pandas DataFrame
import pandas as pd
cursor.execute("SELECT * FROM DEMO_DB.MY_SCHEMA.USERS")
df = cursor.fetch_pandas_all()
print(df)
```

## Output

```
Connected to Snowflake!
Query result: [{ NOW: '2026-03-22T...', WAREHOUSE: 'COMPUTE_WH', DATABASE: 'DEMO_DB', ROLE: 'SYSADMIN' }]
Inserted 1 row(s)
Row: { ID: 1, NAME: 'Alice', EMAIL: 'alice@example.com', CREATED_AT: '...' }
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `002003 (42S02): Object does not exist` | Table/DB not created yet | Run CREATE statements first |
| `000606: No active warehouse` | No warehouse set or suspended | `USE WAREHOUSE COMPUTE_WH;` or set in connection |
| `001003: SQL compilation error: syntax error` | Bad SQL syntax | Check SQL against Snowflake SQL reference |
| `100035: No space left on device` | Large result set, local disk full | Use `streamResult: true` or limit results |

## Resources

- [Executing Statements (Node.js)](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver-execute)
- [Using the Python Connector](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-example)
- [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference)

## Next Steps

Proceed to `snowflake-local-dev-loop` for development workflow setup.
