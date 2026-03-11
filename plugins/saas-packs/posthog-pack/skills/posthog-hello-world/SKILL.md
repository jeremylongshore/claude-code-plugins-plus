---
name: posthog-hello-world
description: |
  Create a minimal working PostHog example.
  Use when starting a new PostHog integration, testing your setup,
  or learning basic PostHog API patterns.
  Trigger with phrases like "posthog hello world", "posthog example",
  "posthog quick start", "simple posthog code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# PostHog Hello World

## Overview
Minimal working example demonstrating core PostHog functionality.

## Prerequisites
- Completed `posthog-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { PostHogClient } from '@posthog/sdk';

const client = new PostHogClient({
  apiKey: process.env.POSTHOG_API_KEY,
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
- Working code file with PostHog client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your PostHog connection is working.
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
import { PostHogClient } from '@posthog/sdk';

const client = new PostHogClient({
  apiKey: process.env.POSTHOG_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from posthog import PostHogClient

client = PostHogClient()

# Your first API call here
```

## Resources
- [PostHog Getting Started](https://docs.posthog.com/getting-started)
- [PostHog API Reference](https://docs.posthog.com/api)
- [PostHog Examples](https://docs.posthog.com/examples)

## Next Steps
Proceed to `posthog-local-dev-loop` for development workflow setup.