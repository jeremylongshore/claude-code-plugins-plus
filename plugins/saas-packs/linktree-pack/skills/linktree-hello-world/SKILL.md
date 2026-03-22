---
name: linktree-hello-world
description: |
  Create a minimal working Linktree example.
  Use when starting a new Linktree integration, testing your setup,
  or learning basic Linktree API patterns.
  Trigger with phrases like "linktree hello world", "linktree example",
  "linktree quick start", "simple linktree code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linktree]
---

# Linktree Hello World

## Overview
Minimal working example demonstrating core Linktree functionality.

## Prerequisites
- Completed `linktree-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { LinktreeClient } from '@linktree/sdk';

const client = new LinktreeClient({
  apiKey: process.env.LINKTREE_API_KEY,
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
- Working code file with Linktree client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Linktree connection is working.
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
import { LinktreeClient } from '@linktree/sdk';

const client = new LinktreeClient({
  apiKey: process.env.LINKTREE_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from linktree import LinktreeClient

client = LinktreeClient()

# Your first API call here
```

## Resources
- [Linktree Getting Started](https://docs.linktree.com/getting-started)
- [Linktree API Reference](https://docs.linktree.com/api)
- [Linktree Examples](https://docs.linktree.com/examples)

## Next Steps
Proceed to `linktree-local-dev-loop` for development workflow setup.