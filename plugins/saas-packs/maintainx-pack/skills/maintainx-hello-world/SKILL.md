---
name: maintainx-hello-world
description: |
  Create a minimal working MaintainX example.
  Use when starting a new MaintainX integration, testing your setup,
  or learning basic MaintainX API patterns.
  Trigger with phrases like "maintainx hello world", "maintainx example",
  "maintainx quick start", "simple maintainx code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, maintainx]
---

# MaintainX Hello World

## Overview

Minimal working example demonstrating core MaintainX functionality.


## Prerequisites
- Completed `maintainx-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { MaintainXClient } from '@maintainx/sdk';

const client = new MaintainXClient({

  apiKey: process.env.MAINTAINX_API_KEY,

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
- Working code file with MaintainX client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your MaintainX connection is working.
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
import { MaintainXClient } from '@maintainx/sdk';

const client = new MaintainXClient({

  apiKey: process.env.MAINTAINX_API_KEY,

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
from maintainx import MaintainXClient

client = MaintainXClient()

resources = client.resources.list(limit=5)
print(f"Found {resources.total} resources:")
for r in resources.data:
    print(f"  - {r.name} ({r.type}) — {r.status}")

```

## Resources
- [MaintainX Getting Started](https://docs.maintainx.com/getting-started)
- [MaintainX API Reference](https://docs.maintainx.com/api)
- [MaintainX Examples](https://docs.maintainx.com/examples)

## Next Steps
Proceed to `maintainx-local-dev-loop` for development workflow setup.