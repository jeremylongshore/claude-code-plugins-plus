---
name: abridge-hello-world
description: |
  Create a minimal working Abridge example.
  Use when starting a new Abridge integration, testing your setup,
  or learning basic Abridge API patterns.
  Trigger with phrases like "abridge hello world", "abridge example",
  "abridge quick start", "simple abridge code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, abridge]
---

# Abridge Hello World

## Overview
Minimal working example demonstrating core Abridge functionality.

## Prerequisites
- Completed `abridge-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AbridgeClient } from '@abridge/sdk';

const client = new AbridgeClient({
  apiKey: process.env.ABRIDGE_API_KEY,
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
- Working code file with Abridge client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Abridge connection is working.
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
import { AbridgeClient } from '@abridge/sdk';

const client = new AbridgeClient({
  apiKey: process.env.ABRIDGE_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from abridge import AbridgeClient

client = AbridgeClient()

# Your first API call here
```

## Resources
- [Abridge Getting Started](https://docs.abridge.com/getting-started)
- [Abridge API Reference](https://docs.abridge.com/api)
- [Abridge Examples](https://docs.abridge.com/examples)

## Next Steps
Proceed to `abridge-local-dev-loop` for development workflow setup.