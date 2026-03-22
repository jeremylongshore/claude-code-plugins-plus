---
name: runway-hello-world
description: |
  Create a minimal working Runway example.
  Use when starting a new Runway integration, testing your setup,
  or learning basic Runway API patterns.
  Trigger with phrases like "runway hello world", "runway example",
  "runway quick start", "simple runway code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, runway]
---

# Runway Hello World

## Overview
Minimal working example demonstrating core Runway functionality.

## Prerequisites
- Completed `runway-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { RunwayClient } from '@runway/sdk';

const client = new RunwayClient({
  apiKey: process.env.RUNWAY_API_KEY,
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
- Working code file with Runway client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Runway connection is working.
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
import { RunwayClient } from '@runway/sdk';

const client = new RunwayClient({
  apiKey: process.env.RUNWAY_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from runway import RunwayClient

client = RunwayClient()

# Your first API call here
```

## Resources
- [Runway Getting Started](https://docs.runway.com/getting-started)
- [Runway API Reference](https://docs.runway.com/api)
- [Runway Examples](https://docs.runway.com/examples)

## Next Steps
Proceed to `runway-local-dev-loop` for development workflow setup.