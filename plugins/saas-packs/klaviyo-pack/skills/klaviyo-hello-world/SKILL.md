---
name: klaviyo-hello-world
description: |
  Create a minimal working Klaviyo example.
  Use when starting a new Klaviyo integration, testing your setup,
  or learning basic Klaviyo API patterns.
  Trigger with phrases like "klaviyo hello world", "klaviyo example",
  "klaviyo quick start", "simple klaviyo code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klaviyo]
---

# Klaviyo Hello World

## Overview
Minimal working example demonstrating core Klaviyo functionality.

## Prerequisites
- Completed `klaviyo-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { KlaviyoClient } from '@klaviyo/sdk';

const client = new KlaviyoClient({
  apiKey: process.env.KLAVIYO_API_KEY,
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
- Working code file with Klaviyo client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Klaviyo connection is working.
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
import { KlaviyoClient } from '@klaviyo/sdk';

const client = new KlaviyoClient({
  apiKey: process.env.KLAVIYO_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from klaviyo import KlaviyoClient

client = KlaviyoClient()

# Your first API call here
```

## Resources
- [Klaviyo Getting Started](https://docs.klaviyo.com/getting-started)
- [Klaviyo API Reference](https://docs.klaviyo.com/api)
- [Klaviyo Examples](https://docs.klaviyo.com/examples)

## Next Steps
Proceed to `klaviyo-local-dev-loop` for development workflow setup.