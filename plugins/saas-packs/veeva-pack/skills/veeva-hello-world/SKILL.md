---
name: veeva-hello-world
description: |
  Create a minimal working Veeva example.
  Use when starting a new Veeva integration, testing your setup,
  or learning basic Veeva API patterns.
  Trigger with phrases like "veeva hello world", "veeva example",
  "veeva quick start", "simple veeva code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, veeva]
---

# Veeva Hello World

## Overview

Minimal working example demonstrating core Veeva functionality.


## Prerequisites
- Completed `veeva-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { VeevaClient } from '@veeva/sdk';

const client = new VeevaClient({

  apiKey: process.env.VEEVA_API_KEY,

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
- Working code file with Veeva client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Veeva connection is working.
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
import { VeevaClient } from '@veeva/sdk';

const client = new VeevaClient({

  apiKey: process.env.VEEVA_API_KEY,

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
from veeva import VeevaClient

client = VeevaClient()

resources = client.resources.list(limit=5)
print(f"Found {resources.total} resources:")
for r in resources.data:
    print(f"  - {r.name} ({r.type}) — {r.status}")

```

## Resources
- [Veeva Getting Started](https://docs.veeva.com/getting-started)
- [Veeva API Reference](https://docs.veeva.com/api)
- [Veeva Examples](https://docs.veeva.com/examples)

## Next Steps
Proceed to `veeva-local-dev-loop` for development workflow setup.