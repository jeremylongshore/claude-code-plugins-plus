---
name: onenote-hello-world
description: |
  Create a minimal working OneNote example.
  Use when starting a new OneNote integration, testing your setup,
  or learning basic OneNote API patterns.
  Trigger with phrases like "onenote hello world", "onenote example",
  "onenote quick start", "simple onenote code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, onenote]
---

# OneNote Hello World

## Overview
Minimal working example demonstrating core OneNote functionality.

## Prerequisites
- Completed `onenote-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { OneNoteClient } from '@onenote/sdk';

const client = new OneNoteClient({
  apiKey: process.env.ONENOTE_API_KEY,
});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  // Your first API call here
}

main().catch(console.error);
```

## Output
- Working code file with OneNote client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your OneNote connection is working.
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
import { OneNoteClient } from '@onenote/sdk';

const client = new OneNoteClient({
  apiKey: process.env.ONENOTE_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from onenote import OneNoteClient

client = OneNoteClient()

# Your first API call here
```

## Resources
- [OneNote Getting Started](https://docs.onenote.com/getting-started)
- [OneNote API Reference](https://docs.onenote.com/api)
- [OneNote Examples](https://docs.onenote.com/examples)

## Next Steps
Proceed to `onenote-local-dev-loop` for development workflow setup.