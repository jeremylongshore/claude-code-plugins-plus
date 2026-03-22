---
name: documenso-hello-world
description: |
  Create a minimal working Documenso example.
  Use when starting a new Documenso integration, testing your setup,
  or learning basic Documenso API patterns.
  Trigger with phrases like "documenso hello world", "documenso example",
  "documenso quick start", "simple documenso code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, documenso]
---

# Documenso Hello World

## Overview
Minimal working example demonstrating core Documenso functionality.

## Prerequisites
- Completed `documenso-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { DocumensoClient } from '@documenso/sdk';

const client = new DocumensoClient({
  apiKey: process.env.DOCUMENSO_API_KEY,
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
- Working code file with Documenso client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Documenso connection is working.
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
import { DocumensoClient } from '@documenso/sdk';

const client = new DocumensoClient({
  apiKey: process.env.DOCUMENSO_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from documenso import DocumensoClient

client = DocumensoClient()

# Your first API call here
```

## Resources
- [Documenso Getting Started](https://docs.documenso.com/getting-started)
- [Documenso API Reference](https://docs.documenso.com/api)
- [Documenso Examples](https://docs.documenso.com/examples)

## Next Steps
Proceed to `documenso-local-dev-loop` for development workflow setup.