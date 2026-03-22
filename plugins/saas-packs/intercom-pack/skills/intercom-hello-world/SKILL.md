---
name: intercom-hello-world
description: |
  Create a minimal working Intercom example.
  Use when starting a new Intercom integration, testing your setup,
  or learning basic Intercom API patterns.
  Trigger with phrases like "intercom hello world", "intercom example",
  "intercom quick start", "simple intercom code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, intercom]
---

# Intercom Hello World

## Overview

Send your first test message through the Intercom API.


## Prerequisites
- Completed `intercom-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { IntercomClient } from '@intercom/sdk';

const client = new IntercomClient({

  apiKey: process.env.INTERCOM_API_KEY,

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
- Working code file with Intercom client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Intercom connection is working.
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
import { IntercomClient } from '@intercom/sdk';

const client = new IntercomClient({

  apiKey: process.env.INTERCOM_API_KEY,

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
from intercom import IntercomClient

client = IntercomClient()

result = client.messages.send(
    to="test@example.com",
    subject="Hello from SDK",
    body="This is a test message sent via the API.",
)
print(f"Message sent: {result.message_id} (status: {result.status})")

```

## Resources
- [Intercom Getting Started](https://docs.intercom.com/getting-started)
- [Intercom API Reference](https://docs.intercom.com/api)
- [Intercom Examples](https://docs.intercom.com/examples)

## Next Steps
Proceed to `intercom-local-dev-loop` for development workflow setup.