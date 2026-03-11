---
name: exa-hello-world
description: |
  Create a minimal working Exa example.
  Use when starting a new Exa integration, testing your setup,
  or learning basic Exa API patterns.
  Trigger with phrases like "exa hello world", "exa example",
  "exa quick start", "simple exa code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Exa Hello World

## Overview
Minimal working example demonstrating core Exa functionality.

## Prerequisites
- Completed `exa-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ExaClient } from '@exa/sdk';

const client = new ExaClient({
  apiKey: process.env.EXA_API_KEY,
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
- Working code file with Exa client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Exa connection is working.
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
import { ExaClient } from '@exa/sdk';

const client = new ExaClient({
  apiKey: process.env.EXA_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from exa import ExaClient

client = ExaClient()

# Your first API call here
```

## Resources
- [Exa Getting Started](https://docs.exa.com/getting-started)
- [Exa API Reference](https://docs.exa.com/api)
- [Exa Examples](https://docs.exa.com/examples)

## Next Steps
Proceed to `exa-local-dev-loop` for development workflow setup.