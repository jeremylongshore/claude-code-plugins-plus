---
name: stackblitz-hello-world
description: |
  Create a minimal working StackBlitz example.
  Use when starting a new StackBlitz integration, testing your setup,
  or learning basic StackBlitz API patterns.
  Trigger with phrases like "stackblitz hello world", "stackblitz example",
  "stackblitz quick start", "simple stackblitz code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, stackblitz]
---

# StackBlitz Hello World

## Overview
Minimal working example demonstrating core StackBlitz functionality.

## Prerequisites
- Completed `stackblitz-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { StackBlitzClient } from '@stackblitz/sdk';

const client = new StackBlitzClient({
  apiKey: process.env.STACKBLITZ_API_KEY,
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
- Working code file with StackBlitz client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your StackBlitz connection is working.
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
import { StackBlitzClient } from '@stackblitz/sdk';

const client = new StackBlitzClient({
  apiKey: process.env.STACKBLITZ_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from stackblitz import StackBlitzClient

client = StackBlitzClient()

# Your first API call here
```

## Resources
- [StackBlitz Getting Started](https://docs.stackblitz.com/getting-started)
- [StackBlitz API Reference](https://docs.stackblitz.com/api)
- [StackBlitz Examples](https://docs.stackblitz.com/examples)

## Next Steps
Proceed to `stackblitz-local-dev-loop` for development workflow setup.