---
name: brightdata-hello-world
description: |
  Create a minimal working Bright Data example.
  Use when starting a new Bright Data integration, testing your setup,
  or learning basic Bright Data API patterns.
  Trigger with phrases like "brightdata hello world", "brightdata example",
  "brightdata quick start", "simple brightdata code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, brightdata]
---

# Bright Data Hello World

## Overview
Minimal working example demonstrating core Bright Data functionality.

## Prerequisites
- Completed `brightdata-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { BrightDataClient } from '@brightdata/sdk';

const client = new BrightDataClient({
  apiKey: process.env.BRIGHTDATA_API_KEY,
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
- Working code file with Bright Data client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Bright Data connection is working.
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
import { BrightDataClient } from '@brightdata/sdk';

const client = new BrightDataClient({
  apiKey: process.env.BRIGHTDATA_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from brightdata import BrightDataClient

client = BrightDataClient()

# Your first API call here
```

## Resources
- [Bright Data Getting Started](https://docs.brightdata.com/getting-started)
- [Bright Data API Reference](https://docs.brightdata.com/api)
- [Bright Data Examples](https://docs.brightdata.com/examples)

## Next Steps
Proceed to `brightdata-local-dev-loop` for development workflow setup.