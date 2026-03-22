---
name: wispr-hello-world
description: |
  Create a minimal working Wispr example.
  Use when starting a new Wispr integration, testing your setup,
  or learning basic Wispr API patterns.
  Trigger with phrases like "wispr hello world", "wispr example",
  "wispr quick start", "simple wispr code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, wispr]
---

# Wispr Hello World

## Overview

Send your first prompt to the Wispr API and get a model response back.


## Prerequisites
- Completed `wispr-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { WisprClient } from '@wispr/sdk';

const client = new WisprClient({

  apiKey: process.env.WISPR_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const response = await client.chat.completions.create({
  model: 'default',
  messages: [{ role: 'user', content: 'Say hello in one sentence.' }],
  max_tokens: 64,
});
console.log(response.choices[0].message.content);

}

main().catch(console.error);
```

## Output
- Working code file with Wispr client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Wispr connection is working.
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
import { WisprClient } from '@wispr/sdk';

const client = new WisprClient({

  apiKey: process.env.WISPR_API_KEY,

});

async function main() {
  const response = await client.chat.completions.create({
  model: 'default',
  messages: [{ role: 'user', content: 'Say hello in one sentence.' }],
  max_tokens: 64,
});
console.log(response.choices[0].message.content);

}

main().catch(console.error);
```

### Python Example
```python
from wispr import WisprClient

client = WisprClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Wispr Getting Started](https://docs.wispr.com/getting-started)
- [Wispr API Reference](https://docs.wispr.com/api)
- [Wispr Examples](https://docs.wispr.com/examples)

## Next Steps
Proceed to `wispr-local-dev-loop` for development workflow setup.