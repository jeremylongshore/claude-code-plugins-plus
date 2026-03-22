---
name: anth-hello-world
description: |
  Create a minimal working Anthropic example.
  Use when starting a new Anthropic integration, testing your setup,
  or learning basic Anthropic API patterns.
  Trigger with phrases like "anthropic hello world", "anthropic example",
  "anthropic quick start", "simple anthropic code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Hello World

## Overview
Minimal working example demonstrating core Anthropic functionality.

## Prerequisites
- Completed `anthropic-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AnthropicClient } from '@anthropic/sdk';

const client = new AnthropicClient({
  apiKey: process.env.ANTHROPIC_API_KEY,
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
- Working code file with Anthropic client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Anthropic connection is working.
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
import { AnthropicClient } from '@anthropic/sdk';

const client = new AnthropicClient({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from anthropic import AnthropicClient

client = AnthropicClient()

# Your first API call here
```

## Resources
- [Anthropic Getting Started](https://docs.anthropic.com/getting-started)
- [Anthropic API Reference](https://docs.anthropic.com/api)
- [Anthropic Examples](https://docs.anthropic.com/examples)

## Next Steps
Proceed to `anthropic-local-dev-loop` for development workflow setup.