---
name: vastai-hello-world
description: |
  Create a minimal working Vast.ai example.
  Use when starting a new Vast.ai integration, testing your setup,
  or learning basic Vast.ai API patterns.
  Trigger with phrases like "vastai hello world", "vastai example",
  "vastai quick start", "simple vastai code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vast.ai Hello World

## Overview
Minimal working example demonstrating core Vast.ai functionality.

## Prerequisites
- Completed `vastai-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { Vast.aiClient } from '@vastai/sdk';

const client = new Vast.aiClient({
  apiKey: process.env.VASTAI_API_KEY,
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
- Working code file with Vast.ai client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Vast.ai connection is working.
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
import { Vast.aiClient } from '@vastai/sdk';

const client = new Vast.aiClient({
  apiKey: process.env.VASTAI_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from vastai import Vast.aiClient

client = Vast.aiClient()

# Your first API call here
```

## Resources
- [Vast.ai Getting Started](https://docs.vastai.com/getting-started)
- [Vast.ai API Reference](https://docs.vastai.com/api)
- [Vast.ai Examples](https://docs.vastai.com/examples)

## Next Steps
Proceed to `vastai-local-dev-loop` for development workflow setup.