---
name: appfolio-hello-world
description: |
  Create a minimal working AppFolio example.
  Use when starting a new AppFolio integration, testing your setup,
  or learning basic AppFolio API patterns.
  Trigger with phrases like "appfolio hello world", "appfolio example",
  "appfolio quick start", "simple appfolio code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, appfolio]
---

# AppFolio Hello World

## Overview

Minimal working example demonstrating core AppFolio functionality.


## Prerequisites
- Completed `appfolio-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AppFolioClient } from '@appfolio/sdk';

const client = new AppFolioClient({

  apiKey: process.env.APPFOLIO_API_KEY,

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
- Working code file with AppFolio client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your AppFolio connection is working.
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
import { AppFolioClient } from '@appfolio/sdk';

const client = new AppFolioClient({

  apiKey: process.env.APPFOLIO_API_KEY,

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
from appfolio import AppFolioClient

client = AppFolioClient()

resources = client.resources.list(limit=5)
print(f"Found {resources.total} resources:")
for r in resources.data:
    print(f"  - {r.name} ({r.type}) — {r.status}")

```

## Resources
- [AppFolio Getting Started](https://docs.appfolio.com/getting-started)
- [AppFolio API Reference](https://docs.appfolio.com/api)
- [AppFolio Examples](https://docs.appfolio.com/examples)

## Next Steps
Proceed to `appfolio-local-dev-loop` for development workflow setup.