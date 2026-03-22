---
name: databricks-hello-world
description: |
  Create a minimal working Databricks example.
  Use when starting a new Databricks integration, testing your setup,
  or learning basic Databricks API patterns.
  Trigger with phrases like "databricks hello world", "databricks example",
  "databricks quick start", "simple databricks code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, databricks]
---

# Databricks Hello World

## Overview

Run your first query against Databricks and read actual data back.


## Prerequisites
- Completed `databricks-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { DatabricksClient } from '@databricks/sdk';

const client = new DatabricksClient({

  connectionString: process.env.DATABRICKS_DATABASE_URL,

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
- Working code file with Databricks client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Databricks connection is working.
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
import { DatabricksClient } from '@databricks/sdk';

const client = new DatabricksClient({

  connectionString: process.env.DATABRICKS_DATABASE_URL,

});

async function main() {
  const result = await client.query('SELECT 1 AS health_check');
console.log('Connected:', result.rows[0].health_check === 1 ? 'OK' : 'FAIL');

}

main().catch(console.error);
```

### Python Example
```python
from databricks import DatabricksClient

client = DatabricksClient()

result = client.query("SELECT 1 AS health_check")
print("Connected:", "OK" if result[0]["health_check"] == 1 else "FAIL")

```

## Resources
- [Databricks Getting Started](https://docs.databricks.com/getting-started)
- [Databricks API Reference](https://docs.databricks.com/api)
- [Databricks Examples](https://docs.databricks.com/examples)

## Next Steps
Proceed to `databricks-local-dev-loop` for development workflow setup.