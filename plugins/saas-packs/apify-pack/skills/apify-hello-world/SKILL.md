---
name: apify-hello-world
description: |
  Create a minimal working Apify example.
  Use when starting a new Apify integration, testing your setup,
  or learning basic Apify API patterns.
  Trigger with phrases like "apify hello world", "apify example",
  "apify quick start", "simple apify code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apify]
---

# Apify Hello World

## Overview

List your projects and trigger your first action via the Apify API.


## Prerequisites
- Completed `apify-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ApifyClient } from '@apify/sdk';

const client = new ApifyClient({

  apiKey: process.env.APIFY_API_KEY,

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
- Working code file with Apify client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Apify connection is working.
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
import { ApifyClient } from '@apify/sdk';

const client = new ApifyClient({

  apiKey: process.env.APIFY_API_KEY,

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
from apify import ApifyClient

client = ApifyClient()

projects = client.projects.list()
print(f"Found {len(projects)} projects:")
for p in projects:
    print(f"  - {p.name} ({p.status})")

```

## Resources
- [Apify Getting Started](https://docs.apify.com/getting-started)
- [Apify API Reference](https://docs.apify.com/api)
- [Apify Examples](https://docs.apify.com/examples)

## Next Steps
Proceed to `apify-local-dev-loop` for development workflow setup.