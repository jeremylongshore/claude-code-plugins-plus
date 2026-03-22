---
name: customerio-hello-world
description: |
  Create a minimal working Customer.io example.
  Use when starting a new Customer.io integration, testing your setup,
  or learning basic Customer.io API patterns.
  Trigger with phrases like "customerio hello world", "customerio example",
  "customerio quick start", "simple customerio code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, customerio]
---

# Customer.io Hello World

## Overview
Minimal working example demonstrating core Customer.io functionality.

## Prerequisites
- Completed `customerio-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { Customer.ioClient } from '@customerio/sdk';

const client = new Customer.ioClient({
  apiKey: process.env.CUSTOMERIO_API_KEY,
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
- Working code file with Customer.io client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Customer.io connection is working.
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
import { Customer.ioClient } from '@customerio/sdk';

const client = new Customer.ioClient({
  apiKey: process.env.CUSTOMERIO_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from customerio import Customer.ioClient

client = Customer.ioClient()

# Your first API call here
```

## Resources
- [Customer.io Getting Started](https://docs.customerio.com/getting-started)
- [Customer.io API Reference](https://docs.customerio.com/api)
- [Customer.io Examples](https://docs.customerio.com/examples)

## Next Steps
Proceed to `customerio-local-dev-loop` for development workflow setup.