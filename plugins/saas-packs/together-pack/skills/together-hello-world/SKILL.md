---
name: together-hello-world
description: |
  Create a minimal working Together AI example.
  Use when starting a new Together AI integration, testing your setup,
  or learning basic Together AI API patterns.
  Trigger with phrases like "together hello world", "together example",
  "together quick start", "simple together code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, together]
---

# Together AI Hello World

## Overview

Send your first prompt to the Together AI API and get a model response back.


## Prerequisites
- Completed `together-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { TogetherAIClient } from '@together/sdk';

const client = new TogetherAIClient({

  apiKey: process.env.TOGETHER_API_KEY,

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
- Working code file with Together AI client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Together AI connection is working.
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
import { TogetherAIClient } from '@together/sdk';

const client = new TogetherAIClient({

  apiKey: process.env.TOGETHER_API_KEY,

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
from together import TogetherAIClient

client = TogetherAIClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Together AI Getting Started](https://docs.together.com/getting-started)
- [Together AI API Reference](https://docs.together.com/api)
- [Together AI Examples](https://docs.together.com/examples)

## Next Steps
Proceed to `together-local-dev-loop` for development workflow setup.