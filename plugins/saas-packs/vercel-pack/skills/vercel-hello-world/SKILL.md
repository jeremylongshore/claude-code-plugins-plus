---
name: vercel-hello-world
description: |
  Create a minimal working Vercel example.
  Use when starting a new Vercel integration, testing your setup,
  or learning basic Vercel API patterns.
  Trigger with phrases like "vercel hello world", "vercel example",
  "vercel quick start", "simple vercel code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Hello World

## Overview
Minimal working example demonstrating core Vercel functionality.

## Prerequisites
- Completed `vercel-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { VercelClient } from 'vercel';

const client = new VercelClient({
  apiKey: process.env.VERCEL_API_KEY,
});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const projects = await vercel.projects.list(); console.log('Projects:', projects.map(p => p.name));
}

main().catch(console.error);
```

## Output
- Working code file with Vercel client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Vercel connection is working.
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
import { VercelClient } from 'vercel';

const client = new VercelClient({
  apiKey: process.env.VERCEL_API_KEY,
});

async function main() {
  const projects = await vercel.projects.list(); console.log('Projects:', projects.map(p => p.name));
}

main().catch(console.error);
```

### Python Example
```python
from None import VercelClient

client = VercelClient()

None
```

## Resources
- [Vercel Getting Started](https://vercel.com/docs/getting-started)
- [Vercel API Reference](https://vercel.com/docs/api)
- [Vercel Examples](https://vercel.com/docs/examples)

## Next Steps
Proceed to `vercel-local-dev-loop` for development workflow setup.