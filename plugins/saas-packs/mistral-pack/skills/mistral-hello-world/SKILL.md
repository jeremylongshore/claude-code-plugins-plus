---
name: mistral-hello-world
description: |
  Create a minimal working Mistral AI example.
  Use when starting a new Mistral AI integration, testing your setup,
  or learning basic Mistral AI API patterns.
  Trigger with phrases like "mistral hello world", "mistral example",
  "mistral quick start", "simple mistral code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, mistral]
---

# Mistral AI Hello World

## Overview
Minimal working example demonstrating core Mistral AI functionality.

## Prerequisites
- Completed `mistral-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { MistralAIClient } from '@mistral/sdk';

const client = new MistralAIClient({
  apiKey: process.env.MISTRAL_API_KEY,
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
- Working code file with Mistral AI client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Mistral AI connection is working.
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
import { MistralAIClient } from '@mistral/sdk';

const client = new MistralAIClient({
  apiKey: process.env.MISTRAL_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from mistral import MistralAIClient

client = MistralAIClient()

# Your first API call here
```

## Resources
- [Mistral AI Getting Started](https://docs.mistral.com/getting-started)
- [Mistral AI API Reference](https://docs.mistral.com/api)
- [Mistral AI Examples](https://docs.mistral.com/examples)

## Next Steps
Proceed to `mistral-local-dev-loop` for development workflow setup.