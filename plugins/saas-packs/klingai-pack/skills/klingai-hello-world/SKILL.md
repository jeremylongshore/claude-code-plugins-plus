---
name: klingai-hello-world
description: |
  Create a minimal working Kling AI example.
  Use when starting a new Kling AI integration, testing your setup,
  or learning basic Kling AI API patterns.
  Trigger with phrases like "klingai hello world", "klingai example",
  "klingai quick start", "simple klingai code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klingai]
---

# Kling AI Hello World

## Overview

Send your first prompt to the Kling AI API and get a model response back.


## Prerequisites
- Completed `klingai-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { KlingAIClient } from '@klingai/sdk';

const client = new KlingAIClient({

  apiKey: process.env.KLINGAI_API_KEY,

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
- Working code file with Kling AI client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Kling AI connection is working.
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
import { KlingAIClient } from '@klingai/sdk';

const client = new KlingAIClient({

  apiKey: process.env.KLINGAI_API_KEY,

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
from klingai import KlingAIClient

client = KlingAIClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Kling AI Getting Started](https://docs.klingai.com/getting-started)
- [Kling AI API Reference](https://docs.klingai.com/api)
- [Kling AI Examples](https://docs.klingai.com/examples)

## Next Steps
Proceed to `klingai-local-dev-loop` for development workflow setup.