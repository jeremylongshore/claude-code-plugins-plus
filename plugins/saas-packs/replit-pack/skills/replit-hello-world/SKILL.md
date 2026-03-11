---
name: replit-hello-world
description: |
  Create a minimal working Replit example.
  Use when starting a new Replit integration, testing your setup,
  or learning basic Replit API patterns.
  Trigger with phrases like "replit hello world", "replit example",
  "replit quick start", "simple replit code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Hello World

## Overview
Minimal working example demonstrating core Replit functionality.

## Prerequisites
- Completed `replit-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ReplitClient } from '@replit/sdk';

const client = new ReplitClient({
  apiKey: process.env.REPLIT_API_KEY,
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
- Working code file with Replit client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Replit connection is working.
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
import { ReplitClient } from '@replit/sdk';

const client = new ReplitClient({
  apiKey: process.env.REPLIT_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from replit import ReplitClient

client = ReplitClient()

# Your first API call here
```

## Resources
- [Replit Getting Started](https://docs.replit.com/getting-started)
- [Replit API Reference](https://docs.replit.com/api)
- [Replit Examples](https://docs.replit.com/examples)

## Next Steps
Proceed to `replit-local-dev-loop` for development workflow setup.