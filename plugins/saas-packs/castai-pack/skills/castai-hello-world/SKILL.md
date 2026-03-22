---
name: castai-hello-world
description: |
  Create a minimal working Cast AI example.
  Use when starting a new Cast AI integration, testing your setup,
  or learning basic Cast AI API patterns.
  Trigger with phrases like "castai hello world", "castai example",
  "castai quick start", "simple castai code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, castai]
---

# Cast AI Hello World

## Overview
Minimal working example demonstrating core Cast AI functionality.

## Prerequisites
- Completed `castai-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { CastAIClient } from '@castai/sdk';

const client = new CastAIClient({
  apiKey: process.env.CASTAI_API_KEY,
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
- Working code file with Cast AI client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Cast AI connection is working.
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
import { CastAIClient } from '@castai/sdk';

const client = new CastAIClient({
  apiKey: process.env.CASTAI_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from castai import CastAIClient

client = CastAIClient()

# Your first API call here
```

## Resources
- [Cast AI Getting Started](https://docs.castai.com/getting-started)
- [Cast AI API Reference](https://docs.castai.com/api)
- [Cast AI Examples](https://docs.castai.com/examples)

## Next Steps
Proceed to `castai-local-dev-loop` for development workflow setup.