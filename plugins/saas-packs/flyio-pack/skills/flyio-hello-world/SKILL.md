---
name: flyio-hello-world
description: |
  Create a minimal working Fly.io example.
  Use when starting a new Fly.io integration, testing your setup,
  or learning basic Fly.io API patterns.
  Trigger with phrases like "flyio hello world", "flyio example",
  "flyio quick start", "simple flyio code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flyio]
---

# Fly.io Hello World

## Overview
Minimal working example demonstrating core Fly.io functionality.

## Prerequisites
- Completed `flyio-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { Fly.ioClient } from '@flyio/sdk';

const client = new Fly.ioClient({
  apiKey: process.env.FLYIO_API_KEY,
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
- Working code file with Fly.io client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Fly.io connection is working.
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
import { Fly.ioClient } from '@flyio/sdk';

const client = new Fly.ioClient({
  apiKey: process.env.FLYIO_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from flyio import Fly.ioClient

client = Fly.ioClient()

# Your first API call here
```

## Resources
- [Fly.io Getting Started](https://docs.flyio.com/getting-started)
- [Fly.io API Reference](https://docs.flyio.com/api)
- [Fly.io Examples](https://docs.flyio.com/examples)

## Next Steps
Proceed to `flyio-local-dev-loop` for development workflow setup.