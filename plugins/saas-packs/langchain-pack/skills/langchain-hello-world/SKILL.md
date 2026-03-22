---
name: langchain-hello-world
description: |
  Create a minimal working LangChain example.
  Use when starting a new LangChain integration, testing your setup,
  or learning basic LangChain API patterns.
  Trigger with phrases like "langchain hello world", "langchain example",
  "langchain quick start", "simple langchain code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, langchain]
---

# LangChain Hello World

## Overview
Minimal working example demonstrating core LangChain functionality.

## Prerequisites
- Completed `langchain-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { LangChainClient } from '@langchain/sdk';

const client = new LangChainClient({
  apiKey: process.env.LANGCHAIN_API_KEY,
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
- Working code file with LangChain client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your LangChain connection is working.
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
import { LangChainClient } from '@langchain/sdk';

const client = new LangChainClient({
  apiKey: process.env.LANGCHAIN_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from langchain import LangChainClient

client = LangChainClient()

# Your first API call here
```

## Resources
- [LangChain Getting Started](https://docs.langchain.com/getting-started)
- [LangChain API Reference](https://docs.langchain.com/api)
- [LangChain Examples](https://docs.langchain.com/examples)

## Next Steps
Proceed to `langchain-local-dev-loop` for development workflow setup.