---
name: fondo-hello-world
description: |
  Create a minimal working Fondo example.
  Use when starting a new Fondo integration, testing your setup,
  or learning basic Fondo API patterns.
  Trigger with phrases like "fondo hello world", "fondo example",
  "fondo quick start", "simple fondo code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fondo]
---

# Fondo Hello World

## Overview
Minimal working example demonstrating core Fondo functionality.

## Prerequisites
- Completed `fondo-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { FondoClient } from '@fondo/sdk';

const client = new FondoClient({
  apiKey: process.env.FONDO_API_KEY,
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
- Working code file with Fondo client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Fondo connection is working.
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
import { FondoClient } from '@fondo/sdk';

const client = new FondoClient({
  apiKey: process.env.FONDO_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from fondo import FondoClient

client = FondoClient()

# Your first API call here
```

## Resources
- [Fondo Getting Started](https://docs.fondo.com/getting-started)
- [Fondo API Reference](https://docs.fondo.com/api)
- [Fondo Examples](https://docs.fondo.com/examples)

## Next Steps
Proceed to `fondo-local-dev-loop` for development workflow setup.