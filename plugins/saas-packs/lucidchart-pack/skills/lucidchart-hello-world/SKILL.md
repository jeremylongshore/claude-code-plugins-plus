---
name: lucidchart-hello-world
description: |
  Create a minimal working Lucidchart example.
  Use when starting a new Lucidchart integration, testing your setup,
  or learning basic Lucidchart API patterns.
  Trigger with phrases like "lucidchart hello world", "lucidchart example",
  "lucidchart quick start", "simple lucidchart code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lucidchart]
---

# Lucidchart Hello World

## Overview
Minimal working example demonstrating core Lucidchart functionality.

## Prerequisites
- Completed `lucidchart-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { LucidchartClient } from '@lucidchart/sdk';

const client = new LucidchartClient({
  apiKey: process.env.LUCIDCHART_API_KEY,
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
- Working code file with Lucidchart client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Lucidchart connection is working.
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
import { LucidchartClient } from '@lucidchart/sdk';

const client = new LucidchartClient({
  apiKey: process.env.LUCIDCHART_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from lucidchart import LucidchartClient

client = LucidchartClient()

# Your first API call here
```

## Resources
- [Lucidchart Getting Started](https://docs.lucidchart.com/getting-started)
- [Lucidchart API Reference](https://docs.lucidchart.com/api)
- [Lucidchart Examples](https://docs.lucidchart.com/examples)

## Next Steps
Proceed to `lucidchart-local-dev-loop` for development workflow setup.