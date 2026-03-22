---
name: algolia-hello-world
description: |
  Create a minimal working Algolia example.
  Use when starting a new Algolia integration, testing your setup,
  or learning basic Algolia API patterns.
  Trigger with phrases like "algolia hello world", "algolia example",
  "algolia quick start", "simple algolia code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, algolia]
---

# Algolia Hello World

## Overview

Run your first query against Algolia and read actual data back.


## Prerequisites
- Completed `algolia-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AlgoliaClient } from '@algolia/sdk';

const client = new AlgoliaClient({

  connectionString: process.env.ALGOLIA_DATABASE_URL,

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
- Working code file with Algolia client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Algolia connection is working.
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
import { AlgoliaClient } from '@algolia/sdk';

const client = new AlgoliaClient({

  connectionString: process.env.ALGOLIA_DATABASE_URL,

});

async function main() {
  const result = await client.query('SELECT 1 AS health_check');
console.log('Connected:', result.rows[0].health_check === 1 ? 'OK' : 'FAIL');

}

main().catch(console.error);
```

### Python Example
```python
from algolia import AlgoliaClient

client = AlgoliaClient()

result = client.query("SELECT 1 AS health_check")
print("Connected:", "OK" if result[0]["health_check"] == 1 else "FAIL")

```

## Resources
- [Algolia Getting Started](https://docs.algolia.com/getting-started)
- [Algolia API Reference](https://docs.algolia.com/api)
- [Algolia Examples](https://docs.algolia.com/examples)

## Next Steps
Proceed to `algolia-local-dev-loop` for development workflow setup.