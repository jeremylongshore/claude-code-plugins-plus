---
name: palantir-hello-world
description: |
  Create a minimal working Palantir example.
  Use when starting a new Palantir integration, testing your setup,
  or learning basic Palantir API patterns.
  Trigger with phrases like "palantir hello world", "palantir example",
  "palantir quick start", "simple palantir code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, palantir]
---

# Palantir Hello World

## Overview
Minimal working example demonstrating core Palantir functionality.

## Prerequisites
- Completed `palantir-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { PalantirClient } from '@palantir/sdk';

const client = new PalantirClient({
  apiKey: process.env.PALANTIR_API_KEY,
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
- Working code file with Palantir client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Palantir connection is working.
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
import { PalantirClient } from '@palantir/sdk';

const client = new PalantirClient({
  apiKey: process.env.PALANTIR_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from palantir import PalantirClient

client = PalantirClient()

# Your first API call here
```

## Resources
- [Palantir Getting Started](https://docs.palantir.com/getting-started)
- [Palantir API Reference](https://docs.palantir.com/api)
- [Palantir Examples](https://docs.palantir.com/examples)

## Next Steps
Proceed to `palantir-local-dev-loop` for development workflow setup.