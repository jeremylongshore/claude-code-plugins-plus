---
name: salesloft-hello-world
description: |
  Create a minimal working Salesloft example.
  Use when starting a new Salesloft integration, testing your setup,
  or learning basic Salesloft API patterns.
  Trigger with phrases like "salesloft hello world", "salesloft example",
  "salesloft quick start", "simple salesloft code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesloft]
---

# Salesloft Hello World

## Overview
Minimal working example demonstrating core Salesloft functionality.

## Prerequisites
- Completed `salesloft-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { SalesloftClient } from '@salesloft/sdk';

const client = new SalesloftClient({
  apiKey: process.env.SALESLOFT_API_KEY,
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
- Working code file with Salesloft client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Salesloft connection is working.
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
import { SalesloftClient } from '@salesloft/sdk';

const client = new SalesloftClient({
  apiKey: process.env.SALESLOFT_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from salesloft import SalesloftClient

client = SalesloftClient()

# Your first API call here
```

## Resources
- [Salesloft Getting Started](https://docs.salesloft.com/getting-started)
- [Salesloft API Reference](https://docs.salesloft.com/api)
- [Salesloft Examples](https://docs.salesloft.com/examples)

## Next Steps
Proceed to `salesloft-local-dev-loop` for development workflow setup.