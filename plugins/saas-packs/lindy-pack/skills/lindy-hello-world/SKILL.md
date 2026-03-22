---
name: lindy-hello-world
description: |
  Create a minimal working Lindy example.
  Use when starting a new Lindy integration, testing your setup,
  or learning basic Lindy API patterns.
  Trigger with phrases like "lindy hello world", "lindy example",
  "lindy quick start", "simple lindy code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lindy]
---

# Lindy Hello World

## Overview

Send your first prompt to the Lindy API and get a model response back.


## Prerequisites
- Completed `lindy-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { LindyClient } from '@lindy/sdk';

const client = new LindyClient({

  apiKey: process.env.LINDY_API_KEY,

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
- Working code file with Lindy client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Lindy connection is working.
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
import { LindyClient } from '@lindy/sdk';

const client = new LindyClient({

  apiKey: process.env.LINDY_API_KEY,

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
from lindy import LindyClient

client = LindyClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Lindy Getting Started](https://docs.lindy.com/getting-started)
- [Lindy API Reference](https://docs.lindy.com/api)
- [Lindy Examples](https://docs.lindy.com/examples)

## Next Steps
Proceed to `lindy-local-dev-loop` for development workflow setup.