---
name: granola-hello-world
description: |
  Create a minimal working Granola example.
  Use when starting a new Granola integration, testing your setup,
  or learning basic Granola API patterns.
  Trigger with phrases like "granola hello world", "granola example",
  "granola quick start", "simple granola code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, granola]
---

# Granola Hello World

## Overview

List your workspace pages and read content from Granola.


## Prerequisites
- Completed `granola-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { GranolaClient } from '@granola/sdk';

const client = new GranolaClient({

  apiKey: process.env.GRANOLA_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const pages = await client.pages.list({ limit: 5 });
console.log(`Found ${pages.total} pages. Recent:`);
pages.results.forEach(p => console.log(`  - ${p.title} (edited: ${p.lastEdited})`));

}

main().catch(console.error);
```

## Output
- Working code file with Granola client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Granola connection is working.
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
import { GranolaClient } from '@granola/sdk';

const client = new GranolaClient({

  apiKey: process.env.GRANOLA_API_KEY,

});

async function main() {
  const pages = await client.pages.list({ limit: 5 });
console.log(`Found ${pages.total} pages. Recent:`);
pages.results.forEach(p => console.log(`  - ${p.title} (edited: ${p.lastEdited})`));

}

main().catch(console.error);
```

### Python Example
```python
from granola import GranolaClient

client = GranolaClient()

pages = client.pages.list(limit=5)
print(f"Found {pages.total} pages. Recent:")
for p in pages.results:
    print(f"  - {p.title} (edited: {p.last_edited})")

```

## Resources
- [Granola Getting Started](https://docs.granola.com/getting-started)
- [Granola API Reference](https://docs.granola.com/api)
- [Granola Examples](https://docs.granola.com/examples)

## Next Steps
Proceed to `granola-local-dev-loop` for development workflow setup.