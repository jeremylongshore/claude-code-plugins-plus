---
name: guidewire-hello-world
description: |
  Create a minimal working Guidewire example.
  Use when starting a new Guidewire integration, testing your setup,
  or learning basic Guidewire API patterns.
  Trigger with phrases like "guidewire hello world", "guidewire example",
  "guidewire quick start", "simple guidewire code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, guidewire]
---

# Guidewire Hello World

## Overview
Minimal working example demonstrating core Guidewire functionality.

## Prerequisites
- Completed `guidewire-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { GuidewireClient } from '@guidewire/sdk';

const client = new GuidewireClient({
  apiKey: process.env.GUIDEWIRE_API_KEY,
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
- Working code file with Guidewire client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Guidewire connection is working.
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
import { GuidewireClient } from '@guidewire/sdk';

const client = new GuidewireClient({
  apiKey: process.env.GUIDEWIRE_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from guidewire import GuidewireClient

client = GuidewireClient()

# Your first API call here
```

## Resources
- [Guidewire Getting Started](https://docs.guidewire.com/getting-started)
- [Guidewire API Reference](https://docs.guidewire.com/api)
- [Guidewire Examples](https://docs.guidewire.com/examples)

## Next Steps
Proceed to `guidewire-local-dev-loop` for development workflow setup.