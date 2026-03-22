---
name: sentry-hello-world
description: |
  Create a minimal working Sentry example.
  Use when starting a new Sentry integration, testing your setup,
  or learning basic Sentry API patterns.
  Trigger with phrases like "sentry hello world", "sentry example",
  "sentry quick start", "simple sentry code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, sentry]
---

# Sentry Hello World

## Overview
Minimal working example demonstrating core Sentry functionality.

## Prerequisites
- Completed `sentry-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { SentryClient } from '@sentry/sdk';

const client = new SentryClient({
  apiKey: process.env.SENTRY_API_KEY,
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
- Working code file with Sentry client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Sentry connection is working.
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
import { SentryClient } from '@sentry/sdk';

const client = new SentryClient({
  apiKey: process.env.SENTRY_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from sentry import SentryClient

client = SentryClient()

# Your first API call here
```

## Resources
- [Sentry Getting Started](https://docs.sentry.com/getting-started)
- [Sentry API Reference](https://docs.sentry.com/api)
- [Sentry Examples](https://docs.sentry.com/examples)

## Next Steps
Proceed to `sentry-local-dev-loop` for development workflow setup.