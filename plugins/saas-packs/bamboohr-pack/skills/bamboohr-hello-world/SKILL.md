---
name: bamboohr-hello-world
description: |
  Create a minimal working BambooHR example.
  Use when starting a new BambooHR integration, testing your setup,
  or learning basic BambooHR API patterns.
  Trigger with phrases like "bamboohr hello world", "bamboohr example",
  "bamboohr quick start", "simple bamboohr code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, bamboohr]
---

# BambooHR Hello World

## Overview
Minimal working example demonstrating core BambooHR functionality.

## Prerequisites
- Completed `bamboohr-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { BambooHRClient } from '@bamboohr/sdk';

const client = new BambooHRClient({
  apiKey: process.env.BAMBOOHR_API_KEY,
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
- Working code file with BambooHR client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your BambooHR connection is working.
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
import { BambooHRClient } from '@bamboohr/sdk';

const client = new BambooHRClient({
  apiKey: process.env.BAMBOOHR_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from bamboohr import BambooHRClient

client = BambooHRClient()

# Your first API call here
```

## Resources
- [BambooHR Getting Started](https://docs.bamboohr.com/getting-started)
- [BambooHR API Reference](https://docs.bamboohr.com/api)
- [BambooHR Examples](https://docs.bamboohr.com/examples)

## Next Steps
Proceed to `bamboohr-local-dev-loop` for development workflow setup.