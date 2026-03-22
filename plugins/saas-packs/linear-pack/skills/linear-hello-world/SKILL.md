---
name: linear-hello-world
description: |
  Create a minimal working Linear example.
  Use when starting a new Linear integration, testing your setup,
  or learning basic Linear API patterns.
  Trigger with phrases like "linear hello world", "linear example",
  "linear quick start", "simple linear code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linear]
---

# Linear Hello World

## Overview
Minimal working example demonstrating core Linear functionality.

## Prerequisites
- Completed `linear-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { LinearClient } from '@linear/sdk';

const client = new LinearClient({
  apiKey: process.env.LINEAR_API_KEY,
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
- Working code file with Linear client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Linear connection is working.
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
import { LinearClient } from '@linear/sdk';

const client = new LinearClient({
  apiKey: process.env.LINEAR_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from linear import LinearClient

client = LinearClient()

# Your first API call here
```

## Resources
- [Linear Getting Started](https://docs.linear.com/getting-started)
- [Linear API Reference](https://docs.linear.com/api)
- [Linear Examples](https://docs.linear.com/examples)

## Next Steps
Proceed to `linear-local-dev-loop` for development workflow setup.