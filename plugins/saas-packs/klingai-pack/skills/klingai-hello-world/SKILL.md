---
name: klingai-hello-world
description: |
  Create a minimal working Kling AI example.
  Use when starting a new Kling AI integration, testing your setup,
  or learning basic Kling AI API patterns.
  Trigger with phrases like "klingai hello world", "klingai example",
  "klingai quick start", "simple klingai code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klingai]
---

# Kling AI Hello World

## Overview
Minimal working example demonstrating core Kling AI functionality.

## Prerequisites
- Completed `klingai-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { KlingAIClient } from '@klingai/sdk';

const client = new KlingAIClient({
  apiKey: process.env.KLINGAI_API_KEY,
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
- Working code file with Kling AI client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Kling AI connection is working.
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
import { KlingAIClient } from '@klingai/sdk';

const client = new KlingAIClient({
  apiKey: process.env.KLINGAI_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from klingai import KlingAIClient

client = KlingAIClient()

# Your first API call here
```

## Resources
- [Kling AI Getting Started](https://docs.klingai.com/getting-started)
- [Kling AI API Reference](https://docs.klingai.com/api)
- [Kling AI Examples](https://docs.klingai.com/examples)

## Next Steps
Proceed to `klingai-local-dev-loop` for development workflow setup.