---
name: framer-hello-world
description: |
  Create a minimal working Framer example.
  Use when starting a new Framer integration, testing your setup,
  or learning basic Framer API patterns.
  Trigger with phrases like "framer hello world", "framer example",
  "framer quick start", "simple framer code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, framer]
---

# Framer Hello World

## Overview
Minimal working example demonstrating core Framer functionality.

## Prerequisites
- Completed `framer-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { FramerClient } from '@framer/sdk';

const client = new FramerClient({
  apiKey: process.env.FRAMER_API_KEY,
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
- Working code file with Framer client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Framer connection is working.
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
import { FramerClient } from '@framer/sdk';

const client = new FramerClient({
  apiKey: process.env.FRAMER_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from framer import FramerClient

client = FramerClient()

# Your first API call here
```

## Resources
- [Framer Getting Started](https://docs.framer.com/getting-started)
- [Framer API Reference](https://docs.framer.com/api)
- [Framer Examples](https://docs.framer.com/examples)

## Next Steps
Proceed to `framer-local-dev-loop` for development workflow setup.