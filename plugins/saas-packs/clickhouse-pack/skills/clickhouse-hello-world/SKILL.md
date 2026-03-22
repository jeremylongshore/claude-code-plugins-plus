---
name: clickhouse-hello-world
description: |
  Create a minimal working ClickHouse example.
  Use when starting a new ClickHouse integration, testing your setup,
  or learning basic ClickHouse API patterns.
  Trigger with phrases like "clickhouse hello world", "clickhouse example",
  "clickhouse quick start", "simple clickhouse code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickhouse]
---

# ClickHouse Hello World

## Overview

Run your first query against ClickHouse and read actual data back.


## Prerequisites
- Completed `clickhouse-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ClickHouseClient } from '@clickhouse/sdk';

const client = new ClickHouseClient({

  connectionString: process.env.CLICKHOUSE_DATABASE_URL,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const result = await client.query('SELECT 1 AS health_check');
console.log('Connected:', result.rows[0].health_check === 1 ? 'OK' : 'FAIL');

}

main().catch(console.error);
```

## Output
- Working code file with ClickHouse client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your ClickHouse connection is working.
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list` or `pip show` |
| Auth Error | Invalid credentials | Check environment variable is set |
| Timeout | Network issues | Increase timeout or check connectivity |
| Rate Limit | Too many requests | Wait and retry with exponential backoff |

## Examples

### TypeScript Example
```typescript
import { ClickHouseClient } from '@clickhouse/sdk';

const client = new ClickHouseClient({

  connectionString: process.env.CLICKHOUSE_DATABASE_URL,

});

async function main() {
  const result = await client.query('SELECT 1 AS health_check');
console.log('Connected:', result.rows[0].health_check === 1 ? 'OK' : 'FAIL');

}

main().catch(console.error);
```

### Python Example
```python
from clickhouse import ClickHouseClient

client = ClickHouseClient()

result = client.query("SELECT 1 AS health_check")
print("Connected:", "OK" if result[0]["health_check"] == 1 else "FAIL")

```

## Resources
- [ClickHouse Getting Started](https://docs.clickhouse.com/getting-started)
- [ClickHouse API Reference](https://docs.clickhouse.com/api)
- [ClickHouse Examples](https://docs.clickhouse.com/examples)

## Next Steps
Proceed to `clickhouse-local-dev-loop` for development workflow setup.