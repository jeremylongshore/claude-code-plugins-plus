---
name: firecrawl-hello-world
description: |
  Create a minimal working FireCrawl example.
  Use when starting a new FireCrawl integration, testing your setup,
  or learning basic FireCrawl API patterns.
  Trigger with phrases like "firecrawl hello world", "firecrawl example",
  "firecrawl quick start", "simple firecrawl code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# FireCrawl Hello World

## Overview
Minimal working example demonstrating core FireCrawl functionality.

## Prerequisites
- Completed `firecrawl-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { FireCrawlClient } from '@firecrawl/sdk';

const client = new FireCrawlClient({
  apiKey: process.env.FIRECRAWL_API_KEY,
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
- Working code file with FireCrawl client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your FireCrawl connection is working.
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
import { FireCrawlClient } from '@firecrawl/sdk';

const client = new FireCrawlClient({
  apiKey: process.env.FIRECRAWL_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from firecrawl import FireCrawlClient

client = FireCrawlClient()

# Your first API call here
```

## Resources
- [FireCrawl Getting Started](https://docs.firecrawl.com/getting-started)
- [FireCrawl API Reference](https://docs.firecrawl.com/api)
- [FireCrawl Examples](https://docs.firecrawl.com/examples)

## Next Steps
Proceed to `firecrawl-local-dev-loop` for development workflow setup.