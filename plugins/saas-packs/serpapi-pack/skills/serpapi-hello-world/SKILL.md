---
name: serpapi-hello-world
description: |
  Create a minimal working SerpApi example.
  Use when starting a new SerpApi integration, testing your setup,
  or learning basic SerpApi API patterns.
  Trigger with phrases like "serpapi hello world", "serpapi example",
  "serpapi quick start", "simple serpapi code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, serpapi]
---

# SerpApi Hello World

## Overview

List your projects and trigger your first action via the SerpApi API.


## Prerequisites
- Completed `serpapi-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { SerpApiClient } from '@serpapi/sdk';

const client = new SerpApiClient({

  apiKey: process.env.SERPAPI_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const projects = await client.projects.list();
console.log(`Found ${projects.length} projects:`);
projects.forEach(p => console.log(`  - ${p.name} (${p.status})`));

}

main().catch(console.error);
```

## Output
- Working code file with SerpApi client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your SerpApi connection is working.
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
import { SerpApiClient } from '@serpapi/sdk';

const client = new SerpApiClient({

  apiKey: process.env.SERPAPI_API_KEY,

});

async function main() {
  const projects = await client.projects.list();
console.log(`Found ${projects.length} projects:`);
projects.forEach(p => console.log(`  - ${p.name} (${p.status})`));

}

main().catch(console.error);
```

### Python Example
```python
from serpapi import SerpApiClient

client = SerpApiClient()

projects = client.projects.list()
print(f"Found {len(projects)} projects:")
for p in projects:
    print(f"  - {p.name} ({p.status})")

```

## Resources
- [SerpApi Getting Started](https://docs.serpapi.com/getting-started)
- [SerpApi API Reference](https://docs.serpapi.com/api)
- [SerpApi Examples](https://docs.serpapi.com/examples)

## Next Steps
Proceed to `serpapi-local-dev-loop` for development workflow setup.