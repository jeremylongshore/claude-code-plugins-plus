---
name: elevenlabs-hello-world
description: |
  Create a minimal working ElevenLabs example.
  Use when starting a new ElevenLabs integration, testing your setup,
  or learning basic ElevenLabs API patterns.
  Trigger with phrases like "elevenlabs hello world", "elevenlabs example",
  "elevenlabs quick start", "simple elevenlabs code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, elevenlabs]
---

# ElevenLabs Hello World

## Overview
Minimal working example demonstrating core ElevenLabs functionality.

## Prerequisites
- Completed `elevenlabs-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ElevenLabsClient } from '@elevenlabs/sdk';

const client = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
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
- Working code file with ElevenLabs client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your ElevenLabs connection is working.
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
import { ElevenLabsClient } from '@elevenlabs/sdk';

const client = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from elevenlabs import ElevenLabsClient

client = ElevenLabsClient()

# Your first API call here
```

## Resources
- [ElevenLabs Getting Started](https://docs.elevenlabs.com/getting-started)
- [ElevenLabs API Reference](https://docs.elevenlabs.com/api)
- [ElevenLabs Examples](https://docs.elevenlabs.com/examples)

## Next Steps
Proceed to `elevenlabs-local-dev-loop` for development workflow setup.