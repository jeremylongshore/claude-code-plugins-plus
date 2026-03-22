---
name: wispr-hello-world
description: |
  Create a minimal working Wispr example.
  Use when starting a new Wispr integration, testing your setup,
  or learning basic Wispr API patterns.
  Trigger with phrases like "wispr hello world", "wispr example",
  "wispr quick start", "simple wispr code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, wispr]
---

# Wispr Hello World

## Overview
Minimal working example demonstrating core Wispr functionality.

## Prerequisites
- Completed `wispr-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { WisprClient } from '@wispr/sdk';

const client = new WisprClient({
  apiKey: process.env.WISPR_API_KEY,
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
- Working code file with Wispr client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Wispr connection is working.
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
import { WisprClient } from '@wispr/sdk';

const client = new WisprClient({
  apiKey: process.env.WISPR_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from wispr import WisprClient

client = WisprClient()

# Your first API call here
```

## Resources
- [Wispr Getting Started](https://docs.wispr.com/getting-started)
- [Wispr API Reference](https://docs.wispr.com/api)
- [Wispr Examples](https://docs.wispr.com/examples)

## Next Steps
Proceed to `wispr-local-dev-loop` for development workflow setup.