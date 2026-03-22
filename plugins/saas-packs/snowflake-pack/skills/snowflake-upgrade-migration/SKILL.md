---
name: snowflake-upgrade-migration
description: |
  Upgrade Snowflake drivers, handle breaking changes, and migrate between editions.
  Use when upgrading snowflake-sdk or snowflake-connector-python versions,
  migrating between Snowflake editions, or handling deprecations.
  Trigger with phrases like "upgrade snowflake", "snowflake migration",
  "snowflake breaking changes", "update snowflake driver", "snowflake version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Upgrade & Migration

## Overview

Guide for upgrading Snowflake driver versions, handling Snowflake behavior change releases, and migrating between editions.

## Prerequisites

- Current driver version identified
- Test suite available
- Staging Snowflake account
- Git for version control

## Instructions

### Step 1: Check Current Versions

```bash
# Node.js driver
npm list snowflake-sdk
npm view snowflake-sdk version   # Latest available

# Python connector
pip show snowflake-connector-python
pip index versions snowflake-connector-python 2>/dev/null | head -5

# Snowflake platform version (run in SQL)
# SELECT CURRENT_VERSION();
```

### Step 2: Review Snowflake Release Notes

```bash
# Check Node.js driver changelog
open https://github.com/snowflakedb/snowflake-connector-nodejs/blob/master/CHANGELOG.md

# Check Python connector changelog
open https://docs.snowflake.com/en/release-notes/clients-drivers/python-connector-2025

# Check Snowflake BCR (Behavior Change Releases)
open https://docs.snowflake.com/en/release-notes/bcr-bundles
```

### Step 3: Upgrade on a Branch

```bash
# Node.js
git checkout -b chore/upgrade-snowflake-sdk
npm install snowflake-sdk@latest
npm test

# Python
git checkout -b chore/upgrade-snowflake-connector
pip install --upgrade snowflake-connector-python
pytest
```

### Step 4: Handle Common Breaking Changes

**Node.js Driver Changes (1.x to 2.x+):**
```typescript
// Old: Synchronous configure
// snowflake.configure({ logLevel: 'DEBUG' });

// New: Same API but check for removed options
import snowflake from 'snowflake-sdk';
snowflake.configure({
  logLevel: process.env.NODE_ENV === 'development' ? 'DEBUG' : 'WARN',
  // insecureConnect removed in newer versions — use proper certs
});

// connectAsync added in later versions
const conn = snowflake.createConnection({ /* ... */ });
await conn.connectAsync();  // Promise-based (if available)
// Fallback for older versions:
await new Promise((resolve, reject) => {
  conn.connect((err, c) => err ? reject(err) : resolve(c));
});
```

**Python Connector Changes:**
```python
# v3.x: fetch_pandas_all() requires pandas extra
# pip install "snowflake-connector-python[pandas]"

# v3.x: write_pandas() moved to snowflake.connector.pandas_tools
from snowflake.connector.pandas_tools import write_pandas

# v2.x to v3.x: DictCursor import changed
# Old: from snowflake.connector import DictCursor
# New:
cursor = conn.cursor(snowflake.connector.DictCursor)

# Arrow result format (default in newer versions)
conn = snowflake.connector.connect(
    # ...
    arrow_number_to_decimal=True,  # New in 3.x
)
```

**Snowflake Platform BCR (Behavior Change Releases):**
```sql
-- Check which BCR bundles are enabled
SELECT SYSTEM$SHOW_ACTIVE_BEHAVIOR_CHANGE_BUNDLES();

-- Test a specific BCR before it's mandatory
ALTER ACCOUNT SET BCR_ENABLED = '2024_08';

-- Common BCRs to watch:
-- Stricter type checking in COPY INTO
-- Changed NULL handling in aggregations
-- Modified INFORMATION_SCHEMA view columns
```

### Step 5: Validate After Upgrade

```typescript
// src/tests/integration/upgrade-validation.test.ts
describe('Post-upgrade validation', () => {
  it('should connect with existing credentials', async () => {
    const conn = createConnection();
    await connectAsync(conn);
    expect(conn.getId()).toBeTruthy();
  });

  it('should execute parameterized queries', async () => {
    const rows = await query(conn,
      'SELECT ? AS test_value', [42]
    );
    expect(rows[0].TEST_VALUE).toBe(42);
  });

  it('should stream large results', async () => {
    let count = 0;
    for await (const row of streamQuery(conn,
      'SELECT SEQ4() AS n FROM TABLE(GENERATOR(ROWCOUNT => 10000))'
    )) {
      count++;
    }
    expect(count).toBe(10000);
  });

  it('should handle errors correctly', async () => {
    await expect(
      query(conn, 'SELECT * FROM nonexistent_table_xyz')
    ).rejects.toThrow(/does not exist/);
  });
});
```

### Step 6: Rollback Procedure

```bash
# Node.js — pin exact version
npm install snowflake-sdk@1.9.0 --save-exact

# Python — pin exact version
pip install snowflake-connector-python==3.6.0

# Git rollback
git checkout main -- package-lock.json package.json
npm ci
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `connectAsync is not a function` | Old SDK version | Use callback-based `connect()` |
| `Arrow deserialization error` | Arrow format mismatch | Set `arrow_number_to_decimal` |
| `BCR behavior change` | New Snowflake release | Test BCR bundle in staging first |
| `ImportError: pandas` | Missing pandas extra | Install with `[pandas]` extra |
| `SSL certificate error` | Driver TLS change | Update CA bundle, don't use `insecureConnect` |

## Resources

- [Node.js Driver Releases](https://github.com/snowflakedb/snowflake-connector-nodejs/releases)
- [Python Connector Release Notes](https://docs.snowflake.com/en/release-notes/clients-drivers/python-connector-2025)
- [Behavior Change Bundles](https://docs.snowflake.com/en/release-notes/bcr-bundles)

## Next Steps

For CI integration during upgrades, see `snowflake-ci-integration`.
