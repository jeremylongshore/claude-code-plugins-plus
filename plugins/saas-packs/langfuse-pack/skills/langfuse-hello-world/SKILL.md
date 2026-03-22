---
name: langfuse-hello-world
description: |
  Create a minimal working Langfuse example.
  Use when starting a new Langfuse integration, testing your setup,
  or learning basic Langfuse API patterns.
  Trigger with phrases like "langfuse hello world", "langfuse example",
  "langfuse quick start", "simple langfuse code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, langfuse]
---

# Langfuse Hello World

## Overview
Minimal working example demonstrating core Langfuse functionality.

## Prerequisites
- Completed `langfuse-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { LangfuseClient } from '@langfuse/sdk';

const client = new LangfuseClient({
  apiKey: process.env.LANGFUSE_API_KEY,
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
- Working code file with Langfuse client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Langfuse connection is working.
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
import { LangfuseClient } from '@langfuse/sdk';

const client = new LangfuseClient({
  apiKey: process.env.LANGFUSE_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from langfuse import LangfuseClient

client = LangfuseClient()

# Your first API call here
```

## Resources
- [Langfuse Getting Started](https://docs.langfuse.com/getting-started)
- [Langfuse API Reference](https://docs.langfuse.com/api)
- [Langfuse Examples](https://docs.langfuse.com/examples)

## Next Steps
Proceed to `langfuse-local-dev-loop` for development workflow setup.