---
name: evernote-hello-world
description: |
  Create a minimal working Evernote example.
  Use when starting a new Evernote integration, testing your setup,
  or learning basic Evernote API patterns.
  Trigger with phrases like "evernote hello world", "evernote example",
  "evernote quick start", "simple evernote code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, evernote]
---

# Evernote Hello World

## Overview

List your workspace pages and read content from Evernote.


## Prerequisites
- Completed `evernote-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { EvernoteClient } from '@evernote/sdk';

const client = new EvernoteClient({

  apiKey: process.env.EVERNOTE_API_KEY,

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
- Working code file with Evernote client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Evernote connection is working.
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
import { EvernoteClient } from '@evernote/sdk';

const client = new EvernoteClient({

  apiKey: process.env.EVERNOTE_API_KEY,

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
from evernote import EvernoteClient

client = EvernoteClient()

pages = client.pages.list(limit=5)
print(f"Found {pages.total} pages. Recent:")
for p in pages.results:
    print(f"  - {p.title} (edited: {p.last_edited})")

```

## Resources
- [Evernote Getting Started](https://docs.evernote.com/getting-started)
- [Evernote API Reference](https://docs.evernote.com/api)
- [Evernote Examples](https://docs.evernote.com/examples)

## Next Steps
Proceed to `evernote-local-dev-loop` for development workflow setup.