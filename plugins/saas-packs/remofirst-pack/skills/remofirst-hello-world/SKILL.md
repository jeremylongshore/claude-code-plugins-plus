---
name: remofirst-hello-world
description: |
  Create a minimal working RemoFirst example.
  Use when starting a new RemoFirst integration, testing your setup,
  or learning basic RemoFirst API patterns.
  Trigger with phrases like "remofirst hello world", "remofirst example",
  "remofirst quick start", "simple remofirst code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, remofirst]
---

# RemoFirst Hello World

## Overview
Minimal working example demonstrating core RemoFirst functionality.

## Prerequisites
- Completed `remofirst-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { RemoFirstClient } from '@remofirst/sdk';

const client = new RemoFirstClient({
  apiKey: process.env.REMOFIRST_API_KEY,
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
- Working code file with RemoFirst client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your RemoFirst connection is working.
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
import { RemoFirstClient } from '@remofirst/sdk';

const client = new RemoFirstClient({
  apiKey: process.env.REMOFIRST_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from remofirst import RemoFirstClient

client = RemoFirstClient()

# Your first API call here
```

## Resources
- [RemoFirst Getting Started](https://docs.remofirst.com/getting-started)
- [RemoFirst API Reference](https://docs.remofirst.com/api)
- [RemoFirst Examples](https://docs.remofirst.com/examples)

## Next Steps
Proceed to `remofirst-local-dev-loop` for development workflow setup.