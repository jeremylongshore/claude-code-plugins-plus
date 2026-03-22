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
Minimal working example demonstrating core Databricks functionality.

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
  apiKey: process.env.DATABRICKS_API_KEY,
});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  // Your first API call here
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
  apiKey: process.env.DATABRICKS_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from databricks import DatabricksClient

client = DatabricksClient()

# Your first API call here
```

## Resources
- [Databricks Getting Started](https://docs.databricks.com/getting-started)
- [Databricks API Reference](https://docs.databricks.com/api)
- [Databricks Examples](https://docs.databricks.com/examples)

## Next Steps
Proceed to `databricks-local-dev-loop` for development workflow setup.