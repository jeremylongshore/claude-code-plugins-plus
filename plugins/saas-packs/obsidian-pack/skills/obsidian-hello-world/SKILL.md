---
name: obsidian-hello-world
description: |
  Create a minimal working Obsidian example.
  Use when starting a new Obsidian integration, testing your setup,
  or learning basic Obsidian API patterns.
  Trigger with phrases like "obsidian hello world", "obsidian example",
  "obsidian quick start", "simple obsidian code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, obsidian]
---

# Obsidian Hello World

## Overview

List your workspace pages and read content from Obsidian.


## Prerequisites
- Completed `obsidian-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ObsidianClient } from '@obsidian/sdk';

const client = new ObsidianClient({

  apiKey: process.env.OBSIDIAN_API_KEY,

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
- Working code file with Obsidian client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Obsidian connection is working.
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
import { ObsidianClient } from '@obsidian/sdk';

const client = new ObsidianClient({

  apiKey: process.env.OBSIDIAN_API_KEY,

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
from obsidian import ObsidianClient

client = ObsidianClient()

pages = client.pages.list(limit=5)
print(f"Found {pages.total} pages. Recent:")
for p in pages.results:
    print(f"  - {p.title} (edited: {p.last_edited})")

```

## Resources
- [Obsidian Getting Started](https://docs.obsidian.com/getting-started)
- [Obsidian API Reference](https://docs.obsidian.com/api)
- [Obsidian Examples](https://docs.obsidian.com/examples)

## Next Steps
Proceed to `obsidian-local-dev-loop` for development workflow setup.