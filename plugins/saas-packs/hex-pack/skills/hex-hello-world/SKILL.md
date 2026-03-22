---
name: hex-hello-world
description: |
  Create a minimal working Hex example.
  Use when starting a new Hex integration, testing your setup,
  or learning basic Hex API patterns.
  Trigger with phrases like "hex hello world", "hex example",
  "hex quick start", "simple hex code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hex]
---

# Hex Hello World

## Overview

Run your first query against Hex and read actual data back.


## Prerequisites
- Completed `hex-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { HexClient } from '@hex/sdk';

const client = new HexClient({

  connectionString: process.env.HEX_DATABASE_URL,

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
- Working code file with Hex client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Hex connection is working.
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
import { HexClient } from '@hex/sdk';

const client = new HexClient({

  connectionString: process.env.HEX_DATABASE_URL,

});

async function main() {
  const result = await client.query('SELECT 1 AS health_check');
console.log('Connected:', result.rows[0].health_check === 1 ? 'OK' : 'FAIL');

}

main().catch(console.error);
```

### Python Example
```python
from hex import HexClient

client = HexClient()

result = client.query("SELECT 1 AS health_check")
print("Connected:", "OK" if result[0]["health_check"] == 1 else "FAIL")

```

## Resources
- [Hex Getting Started](https://docs.hex.com/getting-started)
- [Hex API Reference](https://docs.hex.com/api)
- [Hex Examples](https://docs.hex.com/examples)

## Next Steps
Proceed to `hex-local-dev-loop` for development workflow setup.