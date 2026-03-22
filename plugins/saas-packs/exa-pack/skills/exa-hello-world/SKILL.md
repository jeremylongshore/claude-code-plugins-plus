---
name: exa-hello-world
description: |
  Create a minimal working Exa example.
  Use when starting a new Exa integration, testing your setup,
  or learning basic Exa API patterns.
  Trigger with phrases like "exa hello world", "exa example",
  "exa quick start", "simple exa code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, exa]
---

# Exa Hello World

## Overview

Send your first prompt to the Exa API and get a model response back.


## Prerequisites
- Completed `exa-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ExaClient } from '@exa/sdk';

const client = new ExaClient({

  apiKey: process.env.EXA_API_KEY,

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
- Working code file with Exa client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Exa connection is working.
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
import { ExaClient } from '@exa/sdk';

const client = new ExaClient({

  apiKey: process.env.EXA_API_KEY,

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
from exa import ExaClient

client = ExaClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Exa Getting Started](https://docs.exa.com/getting-started)
- [Exa API Reference](https://docs.exa.com/api)
- [Exa Examples](https://docs.exa.com/examples)

## Next Steps
Proceed to `exa-local-dev-loop` for development workflow setup.