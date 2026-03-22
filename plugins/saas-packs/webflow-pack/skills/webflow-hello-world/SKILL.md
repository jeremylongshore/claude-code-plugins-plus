---
name: webflow-hello-world
description: |
  Create a minimal working Webflow example.
  Use when starting a new Webflow integration, testing your setup,
  or learning basic Webflow API patterns.
  Trigger with phrases like "webflow hello world", "webflow example",
  "webflow quick start", "simple webflow code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, webflow]
---

# Webflow Hello World

## Overview
Minimal working example demonstrating core Webflow functionality.

## Prerequisites
- Completed `webflow-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { WebflowClient } from '@webflow/sdk';

const client = new WebflowClient({
  apiKey: process.env.WEBFLOW_API_KEY,
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
- Working code file with Webflow client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Webflow connection is working.
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
import { WebflowClient } from '@webflow/sdk';

const client = new WebflowClient({
  apiKey: process.env.WEBFLOW_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from webflow import WebflowClient

client = WebflowClient()

# Your first API call here
```

## Resources
- [Webflow Getting Started](https://docs.webflow.com/getting-started)
- [Webflow API Reference](https://docs.webflow.com/api)
- [Webflow Examples](https://docs.webflow.com/examples)

## Next Steps
Proceed to `webflow-local-dev-loop` for development workflow setup.