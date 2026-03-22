---
name: hootsuite-hello-world
description: |
  Create a minimal working Hootsuite example.
  Use when starting a new Hootsuite integration, testing your setup,
  or learning basic Hootsuite API patterns.
  Trigger with phrases like "hootsuite hello world", "hootsuite example",
  "hootsuite quick start", "simple hootsuite code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hootsuite]
---

# Hootsuite Hello World

## Overview

Send your first test message through the Hootsuite API.


## Prerequisites
- Completed `hootsuite-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { HootsuiteClient } from '@hootsuite/sdk';

const client = new HootsuiteClient({

  apiKey: process.env.HOOTSUITE_API_KEY,

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
- Working code file with Hootsuite client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Hootsuite connection is working.
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
import { HootsuiteClient } from '@hootsuite/sdk';

const client = new HootsuiteClient({

  apiKey: process.env.HOOTSUITE_API_KEY,

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
from hootsuite import HootsuiteClient

client = HootsuiteClient()

result = client.messages.send(
    to="test@example.com",
    subject="Hello from SDK",
    body="This is a test message sent via the API.",
)
print(f"Message sent: {result.message_id} (status: {result.status})")

```

## Resources
- [Hootsuite Getting Started](https://docs.hootsuite.com/getting-started)
- [Hootsuite API Reference](https://docs.hootsuite.com/api)
- [Hootsuite Examples](https://docs.hootsuite.com/examples)

## Next Steps
Proceed to `hootsuite-local-dev-loop` for development workflow setup.