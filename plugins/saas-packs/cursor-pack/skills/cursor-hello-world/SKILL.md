---
name: cursor-hello-world
description: |
  Create a minimal working Cursor example.
  Use when starting a new Cursor integration, testing your setup,
  or learning basic Cursor API patterns.
  Trigger with phrases like "cursor hello world", "cursor example",
  "cursor quick start", "simple cursor code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cursor]
---

# Cursor Hello World

## Overview

List your projects and trigger your first action via the Cursor API.


## Prerequisites
- Completed `cursor-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { CursorClient } from '@cursor/sdk';

const client = new CursorClient({

  apiKey: process.env.CURSOR_API_KEY,

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
- Working code file with Cursor client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Cursor connection is working.
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
import { CursorClient } from '@cursor/sdk';

const client = new CursorClient({

  apiKey: process.env.CURSOR_API_KEY,

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
from cursor import CursorClient

client = CursorClient()

projects = client.projects.list()
print(f"Found {len(projects)} projects:")
for p in projects:
    print(f"  - {p.name} ({p.status})")

```

## Resources
- [Cursor Getting Started](https://docs.cursor.com/getting-started)
- [Cursor API Reference](https://docs.cursor.com/api)
- [Cursor Examples](https://docs.cursor.com/examples)

## Next Steps
Proceed to `cursor-local-dev-loop` for development workflow setup.