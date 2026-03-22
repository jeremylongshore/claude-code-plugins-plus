---
name: navan-hello-world
description: |
  Create a minimal working Navan example.
  Use when starting a new Navan integration, testing your setup,
  or learning basic Navan API patterns.
  Trigger with phrases like "navan hello world", "navan example",
  "navan quick start", "simple navan code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, navan]
---

# Navan Hello World

## Overview

Minimal working example demonstrating core Navan functionality.


## Prerequisites
- Completed `navan-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { NavanClient } from '@navan/sdk';

const client = new NavanClient({

  apiKey: process.env.NAVAN_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const resources = await client.resources.list({ limit: 5 });
console.log(`Found ${resources.total} resources:`);
resources.data.forEach(r => console.log(`  - ${r.name} (${r.type}) — ${r.status}`));

}

main().catch(console.error);
```

## Output
- Working code file with Navan client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Navan connection is working.
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
import { NavanClient } from '@navan/sdk';

const client = new NavanClient({

  apiKey: process.env.NAVAN_API_KEY,

});

async function main() {
  const resources = await client.resources.list({ limit: 5 });
console.log(`Found ${resources.total} resources:`);
resources.data.forEach(r => console.log(`  - ${r.name} (${r.type}) — ${r.status}`));

}

main().catch(console.error);
```

### Python Example
```python
from navan import NavanClient

client = NavanClient()

resources = client.resources.list(limit=5)
print(f"Found {resources.total} resources:")
for r in resources.data:
    print(f"  - {r.name} ({r.type}) — {r.status}")

```

## Resources
- [Navan Getting Started](https://docs.navan.com/getting-started)
- [Navan API Reference](https://docs.navan.com/api)
- [Navan Examples](https://docs.navan.com/examples)

## Next Steps
Proceed to `navan-local-dev-loop` for development workflow setup.