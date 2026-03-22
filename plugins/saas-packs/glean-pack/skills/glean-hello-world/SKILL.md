---
name: glean-hello-world
description: |
  Create a minimal working Glean example.
  Use when starting a new Glean integration, testing your setup,
  or learning basic Glean API patterns.
  Trigger with phrases like "glean hello world", "glean example",
  "glean quick start", "simple glean code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, glean]
---

# Glean Hello World

## Overview
Minimal working example demonstrating core Glean functionality.

## Prerequisites
- Completed `glean-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { GleanClient } from '@glean/sdk';

const client = new GleanClient({
  apiKey: process.env.GLEAN_API_KEY,
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
- Working code file with Glean client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Glean connection is working.
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
import { GleanClient } from '@glean/sdk';

const client = new GleanClient({
  apiKey: process.env.GLEAN_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from glean import GleanClient

client = GleanClient()

# Your first API call here
```

## Resources
- [Glean Getting Started](https://docs.glean.com/getting-started)
- [Glean API Reference](https://docs.glean.com/api)
- [Glean Examples](https://docs.glean.com/examples)

## Next Steps
Proceed to `glean-local-dev-loop` for development workflow setup.