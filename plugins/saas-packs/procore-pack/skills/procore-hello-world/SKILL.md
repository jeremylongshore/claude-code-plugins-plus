---
name: procore-hello-world
description: |
  Create a minimal working Procore example.
  Use when starting a new Procore integration, testing your setup,
  or learning basic Procore API patterns.
  Trigger with phrases like "procore hello world", "procore example",
  "procore quick start", "simple procore code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, procore]
---

# Procore Hello World

## Overview
Minimal working example demonstrating core Procore functionality.

## Prerequisites
- Completed `procore-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ProcoreClient } from '@procore/sdk';

const client = new ProcoreClient({
  apiKey: process.env.PROCORE_API_KEY,
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
- Working code file with Procore client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Procore connection is working.
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
import { ProcoreClient } from '@procore/sdk';

const client = new ProcoreClient({
  apiKey: process.env.PROCORE_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from procore import ProcoreClient

client = ProcoreClient()

# Your first API call here
```

## Resources
- [Procore Getting Started](https://docs.procore.com/getting-started)
- [Procore API Reference](https://docs.procore.com/api)
- [Procore Examples](https://docs.procore.com/examples)

## Next Steps
Proceed to `procore-local-dev-loop` for development workflow setup.