---
name: fathom-hello-world
description: |
  Create a minimal working Fathom example.
  Use when starting a new Fathom integration, testing your setup,
  or learning basic Fathom API patterns.
  Trigger with phrases like "fathom hello world", "fathom example",
  "fathom quick start", "simple fathom code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fathom]
---

# Fathom Hello World

## Overview
Minimal working example demonstrating core Fathom functionality.

## Prerequisites
- Completed `fathom-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { FathomClient } from '@fathom/sdk';

const client = new FathomClient({
  apiKey: process.env.FATHOM_API_KEY,
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
- Working code file with Fathom client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Fathom connection is working.
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
import { FathomClient } from '@fathom/sdk';

const client = new FathomClient({
  apiKey: process.env.FATHOM_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from fathom import FathomClient

client = FathomClient()

# Your first API call here
```

## Resources
- [Fathom Getting Started](https://docs.fathom.com/getting-started)
- [Fathom API Reference](https://docs.fathom.com/api)
- [Fathom Examples](https://docs.fathom.com/examples)

## Next Steps
Proceed to `fathom-local-dev-loop` for development workflow setup.