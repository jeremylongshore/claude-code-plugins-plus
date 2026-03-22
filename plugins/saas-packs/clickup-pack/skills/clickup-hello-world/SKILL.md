---
name: clickup-hello-world
description: |
  Create a minimal working ClickUp example.
  Use when starting a new ClickUp integration, testing your setup,
  or learning basic ClickUp API patterns.
  Trigger with phrases like "clickup hello world", "clickup example",
  "clickup quick start", "simple clickup code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickup]
---

# ClickUp Hello World

## Overview
Minimal working example demonstrating core ClickUp functionality.

## Prerequisites
- Completed `clickup-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ClickUpClient } from '@clickup/sdk';

const client = new ClickUpClient({
  apiKey: process.env.CLICKUP_API_KEY,
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
- Working code file with ClickUp client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your ClickUp connection is working.
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
import { ClickUpClient } from '@clickup/sdk';

const client = new ClickUpClient({
  apiKey: process.env.CLICKUP_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from clickup import ClickUpClient

client = ClickUpClient()

# Your first API call here
```

## Resources
- [ClickUp Getting Started](https://docs.clickup.com/getting-started)
- [ClickUp API Reference](https://docs.clickup.com/api)
- [ClickUp Examples](https://docs.clickup.com/examples)

## Next Steps
Proceed to `clickup-local-dev-loop` for development workflow setup.