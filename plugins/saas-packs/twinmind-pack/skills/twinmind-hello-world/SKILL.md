---
name: twinmind-hello-world
description: |
  Create a minimal working TwinMind example.
  Use when starting a new TwinMind integration, testing your setup,
  or learning basic TwinMind API patterns.
  Trigger with phrases like "twinmind hello world", "twinmind example",
  "twinmind quick start", "simple twinmind code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, twinmind]
---

# TwinMind Hello World

## Overview
Minimal working example demonstrating core TwinMind functionality.

## Prerequisites
- Completed `twinmind-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { TwinMindClient } from '@twinmind/sdk';

const client = new TwinMindClient({
  apiKey: process.env.TWINMIND_API_KEY,
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
- Working code file with TwinMind client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your TwinMind connection is working.
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
import { TwinMindClient } from '@twinmind/sdk';

const client = new TwinMindClient({
  apiKey: process.env.TWINMIND_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from twinmind import TwinMindClient

client = TwinMindClient()

# Your first API call here
```

## Resources
- [TwinMind Getting Started](https://docs.twinmind.com/getting-started)
- [TwinMind API Reference](https://docs.twinmind.com/api)
- [TwinMind Examples](https://docs.twinmind.com/examples)

## Next Steps
Proceed to `twinmind-local-dev-loop` for development workflow setup.