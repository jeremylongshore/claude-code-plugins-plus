---
name: anima-hello-world
description: |
  Create a minimal working Anima example.
  Use when starting a new Anima integration, testing your setup,
  or learning basic Anima API patterns.
  Trigger with phrases like "anima hello world", "anima example",
  "anima quick start", "simple anima code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anima]
---

# Anima Hello World

## Overview
Minimal working example demonstrating core Anima functionality.

## Prerequisites
- Completed `anima-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AnimaClient } from '@anima/sdk';

const client = new AnimaClient({
  apiKey: process.env.ANIMA_API_KEY,
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
- Working code file with Anima client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Anima connection is working.
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
import { AnimaClient } from '@anima/sdk';

const client = new AnimaClient({
  apiKey: process.env.ANIMA_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from anima import AnimaClient

client = AnimaClient()

# Your first API call here
```

## Resources
- [Anima Getting Started](https://docs.anima.com/getting-started)
- [Anima API Reference](https://docs.anima.com/api)
- [Anima Examples](https://docs.anima.com/examples)

## Next Steps
Proceed to `anima-local-dev-loop` for development workflow setup.