---
name: ideogram-hello-world
description: |
  Create a minimal working Ideogram example.
  Use when starting a new Ideogram integration, testing your setup,
  or learning basic Ideogram API patterns.
  Trigger with phrases like "ideogram hello world", "ideogram example",
  "ideogram quick start", "simple ideogram code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Ideogram Hello World

## Overview
Minimal working example demonstrating core Ideogram functionality.

## Prerequisites
- Completed `ideogram-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { IdeogramClient } from '@ideogram/sdk';

const client = new IdeogramClient({
  apiKey: process.env.IDEOGRAM_API_KEY,
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
- Working code file with Ideogram client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Ideogram connection is working.
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
import { IdeogramClient } from '@ideogram/sdk';

const client = new IdeogramClient({
  apiKey: process.env.IDEOGRAM_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from ideogram import IdeogramClient

client = IdeogramClient()

# Your first API call here
```

## Resources
- [Ideogram Getting Started](https://docs.ideogram.com/getting-started)
- [Ideogram API Reference](https://docs.ideogram.com/api)
- [Ideogram Examples](https://docs.ideogram.com/examples)

## Next Steps
Proceed to `ideogram-local-dev-loop` for development workflow setup.