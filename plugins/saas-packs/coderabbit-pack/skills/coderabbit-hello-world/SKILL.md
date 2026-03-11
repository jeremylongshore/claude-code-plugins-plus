---
name: coderabbit-hello-world
description: |
  Create a minimal working CodeRabbit example.
  Use when starting a new CodeRabbit integration, testing your setup,
  or learning basic CodeRabbit API patterns.
  Trigger with phrases like "coderabbit hello world", "coderabbit example",
  "coderabbit quick start", "simple coderabbit code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit Hello World

## Overview
Minimal working example demonstrating core CodeRabbit functionality.

## Prerequisites
- Completed `coderabbit-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { CodeRabbitClient } from '@coderabbit/sdk';

const client = new CodeRabbitClient({
  apiKey: process.env.CODERABBIT_API_KEY,
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
- Working code file with CodeRabbit client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your CodeRabbit connection is working.
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
import { CodeRabbitClient } from '@coderabbit/sdk';

const client = new CodeRabbitClient({
  apiKey: process.env.CODERABBIT_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from coderabbit import CodeRabbitClient

client = CodeRabbitClient()

# Your first API call here
```

## Resources
- [CodeRabbit Getting Started](https://docs.coderabbit.com/getting-started)
- [CodeRabbit API Reference](https://docs.coderabbit.com/api)
- [CodeRabbit Examples](https://docs.coderabbit.com/examples)

## Next Steps
Proceed to `coderabbit-local-dev-loop` for development workflow setup.