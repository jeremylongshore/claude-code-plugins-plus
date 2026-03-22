---
name: apple-notes-hello-world
description: |
  Create a minimal working Apple Notes example.
  Use when starting a new Apple Notes integration, testing your setup,
  or learning basic Apple Notes API patterns.
  Trigger with phrases like "apple-notes hello world", "apple-notes example",
  "apple-notes quick start", "simple apple-notes code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apple-notes]
---

# Apple Notes Hello World

## Overview

List your workspace pages and read content from Apple Notes.


## Prerequisites
- Completed `apple-notes-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AppleNotesClient } from '@apple-notes/sdk';

const client = new AppleNotesClient({

  apiKey: process.env.APPLE-NOTES_API_KEY,

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
- Working code file with Apple Notes client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Apple Notes connection is working.
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
import { AppleNotesClient } from '@apple-notes/sdk';

const client = new AppleNotesClient({

  apiKey: process.env.APPLE-NOTES_API_KEY,

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
from apple-notes import AppleNotesClient

client = AppleNotesClient()

pages = client.pages.list(limit=5)
print(f"Found {pages.total} pages. Recent:")
for p in pages.results:
    print(f"  - {p.title} (edited: {p.last_edited})")

```

## Resources
- [Apple Notes Getting Started](https://docs.apple-notes.com/getting-started)
- [Apple Notes API Reference](https://docs.apple-notes.com/api)
- [Apple Notes Examples](https://docs.apple-notes.com/examples)

## Next Steps
Proceed to `apple-notes-local-dev-loop` for development workflow setup.