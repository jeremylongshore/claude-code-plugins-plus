---
name: openrouter-hello-world
description: |
  Create a minimal working OpenRouter example.
  Use when starting a new OpenRouter integration, testing your setup,
  or learning basic OpenRouter API patterns.
  Trigger with phrases like "openrouter hello world", "openrouter example",
  "openrouter quick start", "simple openrouter code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openrouter]
---

# OpenRouter Hello World

## Overview
Minimal working example demonstrating core OpenRouter functionality.

## Prerequisites
- Completed `openrouter-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { OpenRouterClient } from '@openrouter/sdk';

const client = new OpenRouterClient({
  apiKey: process.env.OPENROUTER_API_KEY,
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
- Working code file with OpenRouter client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your OpenRouter connection is working.
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
import { OpenRouterClient } from '@openrouter/sdk';

const client = new OpenRouterClient({
  apiKey: process.env.OPENROUTER_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from openrouter import OpenRouterClient

client = OpenRouterClient()

# Your first API call here
```

## Resources
- [OpenRouter Getting Started](https://docs.openrouter.com/getting-started)
- [OpenRouter API Reference](https://docs.openrouter.com/api)
- [OpenRouter Examples](https://docs.openrouter.com/examples)

## Next Steps
Proceed to `openrouter-local-dev-loop` for development workflow setup.