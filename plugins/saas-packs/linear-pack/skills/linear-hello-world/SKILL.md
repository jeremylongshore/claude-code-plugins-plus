---
name: linear-hello-world
description: |
  Create a minimal working Linear example.
  Use when starting a new Linear integration, testing your setup,
  or learning basic Linear API patterns.
  Trigger with phrases like "linear hello world", "linear example",
  "linear quick start", "simple linear code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linear]
---

# Linear Hello World

## Overview

List your workspace pages and read content from Linear.


## Prerequisites
- Completed `linear-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { LinearClient } from '@linear/sdk';

const client = new LinearClient({

  apiKey: process.env.LINEAR_API_KEY,

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
- Working code file with Linear client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Linear connection is working.
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
import { LinearClient } from '@linear/sdk';

const client = new LinearClient({

  apiKey: process.env.LINEAR_API_KEY,

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
from linear import LinearClient

client = LinearClient()

pages = client.pages.list(limit=5)
print(f"Found {pages.total} pages. Recent:")
for p in pages.results:
    print(f"  - {p.title} (edited: {p.last_edited})")

```

## Resources
- [Linear Getting Started](https://docs.linear.com/getting-started)
- [Linear API Reference](https://docs.linear.com/api)
- [Linear Examples](https://docs.linear.com/examples)

## Next Steps
Proceed to `linear-local-dev-loop` for development workflow setup.