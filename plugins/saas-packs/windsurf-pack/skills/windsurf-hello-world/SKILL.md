---
name: windsurf-hello-world
description: |
  Create a minimal working Windsurf example.
  Use when starting a new Windsurf integration, testing your setup,
  or learning basic Windsurf API patterns.
  Trigger with phrases like "windsurf hello world", "windsurf example",
  "windsurf quick start", "simple windsurf code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Hello World

## Overview
Minimal working example demonstrating core Windsurf functionality.

## Prerequisites
- Completed `windsurf-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { WindsurfClient } from '@windsurf/sdk';

const client = new WindsurfClient({
  apiKey: process.env.WINDSURF_API_KEY,
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
- Working code file with Windsurf client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Windsurf connection is working.
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
import { WindsurfClient } from '@windsurf/sdk';

const client = new WindsurfClient({
  apiKey: process.env.WINDSURF_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from windsurf import WindsurfClient

client = WindsurfClient()

# Your first API call here
```

## Resources
- [Windsurf Getting Started](https://docs.windsurf.com/getting-started)
- [Windsurf API Reference](https://docs.windsurf.com/api)
- [Windsurf Examples](https://docs.windsurf.com/examples)

## Next Steps
Proceed to `windsurf-local-dev-loop` for development workflow setup.