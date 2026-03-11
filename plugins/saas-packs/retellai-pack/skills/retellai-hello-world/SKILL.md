---
name: retellai-hello-world
description: |
  Create a minimal working Retell AI example.
  Use when starting a new Retell AI integration, testing your setup,
  or learning basic Retell AI API patterns.
  Trigger with phrases like "retellai hello world", "retellai example",
  "retellai quick start", "simple retellai code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Retell AI Hello World

## Overview
Minimal working example demonstrating core Retell AI functionality.

## Prerequisites
- Completed `retellai-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { RetellAIClient } from '@retellai/sdk';

const client = new RetellAIClient({
  apiKey: process.env.RETELLAI_API_KEY,
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
- Working code file with Retell AI client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Retell AI connection is working.
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
import { RetellAIClient } from '@retellai/sdk';

const client = new RetellAIClient({
  apiKey: process.env.RETELLAI_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from retellai import RetellAIClient

client = RetellAIClient()

# Your first API call here
```

## Resources
- [Retell AI Getting Started](https://docs.retellai.com/getting-started)
- [Retell AI API Reference](https://docs.retellai.com/api)
- [Retell AI Examples](https://docs.retellai.com/examples)

## Next Steps
Proceed to `retellai-local-dev-loop` for development workflow setup.