---
name: fireflies-hello-world
description: |
  Create a minimal working Fireflies.ai example.
  Use when starting a new Fireflies.ai integration, testing your setup,
  or learning basic Fireflies.ai API patterns.
  Trigger with phrases like "fireflies hello world", "fireflies example",
  "fireflies quick start", "simple fireflies code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Fireflies.ai Hello World

## Overview
Minimal working example demonstrating core Fireflies.ai functionality.

## Prerequisites
- Completed `fireflies-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { Fireflies.aiClient } from '@fireflies/sdk';

const client = new Fireflies.aiClient({
  apiKey: process.env.FIREFLIES_API_KEY,
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
- Working code file with Fireflies.ai client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Fireflies.ai connection is working.
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
import { Fireflies.aiClient } from '@fireflies/sdk';

const client = new Fireflies.aiClient({
  apiKey: process.env.FIREFLIES_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from fireflies import Fireflies.aiClient

client = Fireflies.aiClient()

# Your first API call here
```

## Resources
- [Fireflies.ai Getting Started](https://docs.fireflies.com/getting-started)
- [Fireflies.ai API Reference](https://docs.fireflies.com/api)
- [Fireflies.ai Examples](https://docs.fireflies.com/examples)

## Next Steps
Proceed to `fireflies-local-dev-loop` for development workflow setup.