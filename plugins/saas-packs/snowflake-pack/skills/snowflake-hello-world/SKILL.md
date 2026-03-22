---
name: snowflake-hello-world
description: |
  Create a minimal working Snowflake example.
  Use when starting a new Snowflake integration, testing your setup,
  or learning basic Snowflake API patterns.
  Trigger with phrases like "snowflake hello world", "snowflake example",
  "snowflake quick start", "simple snowflake code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, snowflake]
---

# Snowflake Hello World

## Overview

Run your first query against Snowflake and read actual data back.


## Prerequisites
- Completed `snowflake-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { SnowflakeClient } from '@snowflake/sdk';

const client = new SnowflakeClient({

  connectionString: process.env.SNOWFLAKE_DATABASE_URL,

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
- Working code file with Snowflake client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Snowflake connection is working.
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
import { SnowflakeClient } from '@snowflake/sdk';

const client = new SnowflakeClient({

  connectionString: process.env.SNOWFLAKE_DATABASE_URL,

});

async function main() {
  const result = await client.query('SELECT 1 AS health_check');
console.log('Connected:', result.rows[0].health_check === 1 ? 'OK' : 'FAIL');

}

main().catch(console.error);
```

### Python Example
```python
from snowflake import SnowflakeClient

client = SnowflakeClient()

result = client.query("SELECT 1 AS health_check")
print("Connected:", "OK" if result[0]["health_check"] == 1 else "FAIL")

```

## Resources
- [Snowflake Getting Started](https://docs.snowflake.com/getting-started)
- [Snowflake API Reference](https://docs.snowflake.com/api)
- [Snowflake Examples](https://docs.snowflake.com/examples)

## Next Steps
Proceed to `snowflake-local-dev-loop` for development workflow setup.