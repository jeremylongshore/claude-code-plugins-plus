---
name: miro-hello-world
description: |
  Create a minimal working Miro example.
  Use when starting a new Miro integration, testing your setup,
  or learning basic Miro API patterns.
  Trigger with phrases like "miro hello world", "miro example",
  "miro quick start", "simple miro code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, miro]
---

# Miro Hello World

## Overview
Minimal working example demonstrating core Miro functionality.

## Prerequisites
- Completed `miro-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { MiroClient } from '@miro/sdk';

const client = new MiroClient({
  apiKey: process.env.MIRO_API_KEY,
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
- Working code file with Miro client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Miro connection is working.
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
import { MiroClient } from '@miro/sdk';

const client = new MiroClient({
  apiKey: process.env.MIRO_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from miro import MiroClient

client = MiroClient()

# Your first API call here
```

## Resources
- [Miro Getting Started](https://docs.miro.com/getting-started)
- [Miro API Reference](https://docs.miro.com/api)
- [Miro Examples](https://docs.miro.com/examples)

## Next Steps
Proceed to `miro-local-dev-loop` for development workflow setup.