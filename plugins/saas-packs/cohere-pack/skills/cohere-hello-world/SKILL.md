---
name: cohere-hello-world
description: |
  Create a minimal working Cohere example.
  Use when starting a new Cohere integration, testing your setup,
  or learning basic Cohere API patterns.
  Trigger with phrases like "cohere hello world", "cohere example",
  "cohere quick start", "simple cohere code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cohere]
---

# Cohere Hello World

## Overview
Minimal working example demonstrating core Cohere functionality.

## Prerequisites
- Completed `cohere-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { CohereClient } from '@cohere/sdk';

const client = new CohereClient({
  apiKey: process.env.COHERE_API_KEY,
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
- Working code file with Cohere client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Cohere connection is working.
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
import { CohereClient } from '@cohere/sdk';

const client = new CohereClient({
  apiKey: process.env.COHERE_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from cohere import CohereClient

client = CohereClient()

# Your first API call here
```

## Resources
- [Cohere Getting Started](https://docs.cohere.com/getting-started)
- [Cohere API Reference](https://docs.cohere.com/api)
- [Cohere Examples](https://docs.cohere.com/examples)

## Next Steps
Proceed to `cohere-local-dev-loop` for development workflow setup.