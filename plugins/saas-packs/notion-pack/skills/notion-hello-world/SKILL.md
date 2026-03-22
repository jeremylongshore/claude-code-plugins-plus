---
name: notion-hello-world
description: |
  Create a minimal working Notion example.
  Use when starting a new Notion integration, testing your setup,
  or learning basic Notion API patterns.
  Trigger with phrases like "notion hello world", "notion example",
  "notion quick start", "simple notion code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, notion]
---

# Notion Hello World

## Overview

List your workspace pages and read content from Notion.


## Prerequisites
- Completed `notion-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { NotionClient } from '@notion/sdk';

const client = new NotionClient({

  apiKey: process.env.NOTION_API_KEY,

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
- Working code file with Notion client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Notion connection is working.
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
import { NotionClient } from '@notion/sdk';

const client = new NotionClient({

  apiKey: process.env.NOTION_API_KEY,

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
from notion import NotionClient

client = NotionClient()

pages = client.pages.list(limit=5)
print(f"Found {pages.total} pages. Recent:")
for p in pages.results:
    print(f"  - {p.title} (edited: {p.last_edited})")

```

## Resources
- [Notion Getting Started](https://docs.notion.com/getting-started)
- [Notion API Reference](https://docs.notion.com/api)
- [Notion Examples](https://docs.notion.com/examples)

## Next Steps
Proceed to `notion-local-dev-loop` for development workflow setup.