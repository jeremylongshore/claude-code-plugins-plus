---
name: podium-hello-world
description: |
  Create a minimal working Podium example.
  Use when starting a new Podium integration, testing your setup,
  or learning basic Podium API patterns.
  Trigger with phrases like "podium hello world", "podium example",
  "podium quick start", "simple podium code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, podium]
---

# Podium Hello World

## Overview

Send your first test message through the Podium API.


## Prerequisites
- Completed `podium-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { PodiumClient } from '@podium/sdk';

const client = new PodiumClient({

  apiKey: process.env.PODIUM_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const result = await client.messages.send({
  to: 'test@example.com',
  subject: 'Hello from SDK',
  body: 'This is a test message sent via the API.',
});
console.log(`Message sent: ${result.messageId} (status: ${result.status})`);

}

main().catch(console.error);
```

## Output
- Working code file with Podium client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Podium connection is working.
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
import { PodiumClient } from '@podium/sdk';

const client = new PodiumClient({

  apiKey: process.env.PODIUM_API_KEY,

});

async function main() {
  const result = await client.messages.send({
  to: 'test@example.com',
  subject: 'Hello from SDK',
  body: 'This is a test message sent via the API.',
});
console.log(`Message sent: ${result.messageId} (status: ${result.status})`);

}

main().catch(console.error);
```

### Python Example
```python
from podium import PodiumClient

client = PodiumClient()

result = client.messages.send(
    to="test@example.com",
    subject="Hello from SDK",
    body="This is a test message sent via the API.",
)
print(f"Message sent: {result.message_id} (status: {result.status})")

```

## Resources
- [Podium Getting Started](https://docs.podium.com/getting-started)
- [Podium API Reference](https://docs.podium.com/api)
- [Podium Examples](https://docs.podium.com/examples)

## Next Steps
Proceed to `podium-local-dev-loop` for development workflow setup.