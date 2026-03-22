---
name: canva-hello-world
description: |
  Create a minimal working Canva example.
  Use when starting a new Canva integration, testing your setup,
  or learning basic Canva API patterns.
  Trigger with phrases like "canva hello world", "canva example",
  "canva quick start", "simple canva code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, canva]
---

# Canva Hello World

## Overview
Minimal working example demonstrating core Canva functionality.

## Prerequisites
- Completed `canva-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { CanvaClient } from '@canva/sdk';

const client = new CanvaClient({
  apiKey: process.env.CANVA_API_KEY,
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
- Working code file with Canva client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Canva connection is working.
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
import { CanvaClient } from '@canva/sdk';

const client = new CanvaClient({
  apiKey: process.env.CANVA_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from canva import CanvaClient

client = CanvaClient()

# Your first API call here
```

## Resources
- [Canva Getting Started](https://docs.canva.com/getting-started)
- [Canva API Reference](https://docs.canva.com/api)
- [Canva Examples](https://docs.canva.com/examples)

## Next Steps
Proceed to `canva-local-dev-loop` for development workflow setup.