---
name: flexport-hello-world
description: |
  Create a minimal working Flexport example.
  Use when starting a new Flexport integration, testing your setup,
  or learning basic Flexport API patterns.
  Trigger with phrases like "flexport hello world", "flexport example",
  "flexport quick start", "simple flexport code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flexport]
---

# Flexport Hello World

## Overview

Minimal working example demonstrating core Flexport functionality.


## Prerequisites
- Completed `flexport-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { FlexportClient } from '@flexport/sdk';

const client = new FlexportClient({

  apiKey: process.env.FLEXPORT_API_KEY,

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
- Working code file with Flexport client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Flexport connection is working.
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
import { FlexportClient } from '@flexport/sdk';

const client = new FlexportClient({

  apiKey: process.env.FLEXPORT_API_KEY,

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
from flexport import FlexportClient

client = FlexportClient()

resources = client.resources.list(limit=5)
print(f"Found {resources.total} resources:")
for r in resources.data:
    print(f"  - {r.name} ({r.type}) — {r.status}")

```

## Resources
- [Flexport Getting Started](https://docs.flexport.com/getting-started)
- [Flexport API Reference](https://docs.flexport.com/api)
- [Flexport Examples](https://docs.flexport.com/examples)

## Next Steps
Proceed to `flexport-local-dev-loop` for development workflow setup.