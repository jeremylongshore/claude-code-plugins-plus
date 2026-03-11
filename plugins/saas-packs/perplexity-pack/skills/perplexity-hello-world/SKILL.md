---
name: perplexity-hello-world
description: |
  Create a minimal working Perplexity example.
  Use when starting a new Perplexity integration, testing your setup,
  or learning basic Perplexity API patterns.
  Trigger with phrases like "perplexity hello world", "perplexity example",
  "perplexity quick start", "simple perplexity code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Perplexity Hello World

## Overview
Minimal working example demonstrating core Perplexity functionality.

## Prerequisites
- Completed `perplexity-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { PerplexityClient } from '@perplexity/sdk';

const client = new PerplexityClient({
  apiKey: process.env.PERPLEXITY_API_KEY,
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
- Working code file with Perplexity client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Perplexity connection is working.
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
import { PerplexityClient } from '@perplexity/sdk';

const client = new PerplexityClient({
  apiKey: process.env.PERPLEXITY_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from perplexity import PerplexityClient

client = PerplexityClient()

# Your first API call here
```

## Resources
- [Perplexity Getting Started](https://docs.perplexity.com/getting-started)
- [Perplexity API Reference](https://docs.perplexity.com/api)
- [Perplexity Examples](https://docs.perplexity.com/examples)

## Next Steps
Proceed to `perplexity-local-dev-loop` for development workflow setup.