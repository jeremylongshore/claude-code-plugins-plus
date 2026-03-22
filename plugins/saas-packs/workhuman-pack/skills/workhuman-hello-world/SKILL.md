---
name: workhuman-hello-world
description: |
  Create a minimal working Workhuman example.
  Use when starting a new Workhuman integration, testing your setup,
  or learning basic Workhuman API patterns.
  Trigger with phrases like "workhuman hello world", "workhuman example",
  "workhuman quick start", "simple workhuman code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, workhuman]
---

# Workhuman Hello World

## Overview

Minimal working example demonstrating core Workhuman functionality.


## Prerequisites
- Completed `workhuman-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { WorkhumanClient } from '@workhuman/sdk';

const client = new WorkhumanClient({

  apiKey: process.env.WORKHUMAN_API_KEY,

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
- Working code file with Workhuman client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Workhuman connection is working.
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
import { WorkhumanClient } from '@workhuman/sdk';

const client = new WorkhumanClient({

  apiKey: process.env.WORKHUMAN_API_KEY,

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
from workhuman import WorkhumanClient

client = WorkhumanClient()

resources = client.resources.list(limit=5)
print(f"Found {resources.total} resources:")
for r in resources.data:
    print(f"  - {r.name} ({r.type}) — {r.status}")

```

## Resources
- [Workhuman Getting Started](https://docs.workhuman.com/getting-started)
- [Workhuman API Reference](https://docs.workhuman.com/api)
- [Workhuman Examples](https://docs.workhuman.com/examples)

## Next Steps
Proceed to `workhuman-local-dev-loop` for development workflow setup.