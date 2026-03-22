---
name: cohere-hello-world
description: |
  Create a minimal working Cohere example.
  Use when starting a new Cohere integration, testing your setup,
  or learning basic Cohere API patterns.
  Trigger with phrases like "cohere hello world", "cohere example",
  "cohere quick start", "simple cohere code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cohere]
---

# Cohere Hello World

## Overview

Send your first prompt to the Cohere API and get a model response back.


## Prerequisites
- Completed `cohere-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { CohereClient } from '@cohere/sdk';

const client = new CohereClient({

  apiKey: process.env.COHERE_API_KEY,

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
- Working code file with Cohere client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Cohere connection is working.
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
import { CohereClient } from '@cohere/sdk';

const client = new CohereClient({

  apiKey: process.env.COHERE_API_KEY,

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
from cohere import CohereClient

client = CohereClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Cohere Getting Started](https://docs.cohere.com/getting-started)
- [Cohere API Reference](https://docs.cohere.com/api)
- [Cohere Examples](https://docs.cohere.com/examples)

## Next Steps
Proceed to `cohere-local-dev-loop` for development workflow setup.