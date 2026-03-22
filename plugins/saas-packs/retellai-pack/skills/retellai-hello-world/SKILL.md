---
name: retellai-hello-world
description: |
  Create a minimal working Retell AI example.
  Use when starting a new Retell AI integration, testing your setup,
  or learning basic Retell AI API patterns.
  Trigger with phrases like "retellai hello world", "retellai example",
  "retellai quick start", "simple retellai code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, retellai]
---

# Retell AI Hello World

## Overview

Send your first prompt to the Retell AI API and get a model response back.


## Prerequisites
- Completed `retellai-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { RetellAIClient } from '@retellai/sdk';

const client = new RetellAIClient({

  apiKey: process.env.RETELLAI_API_KEY,

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
- Working code file with Retell AI client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Retell AI connection is working.
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
import { RetellAIClient } from '@retellai/sdk';

const client = new RetellAIClient({

  apiKey: process.env.RETELLAI_API_KEY,

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
from retellai import RetellAIClient

client = RetellAIClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Retell AI Getting Started](https://docs.retellai.com/getting-started)
- [Retell AI API Reference](https://docs.retellai.com/api)
- [Retell AI Examples](https://docs.retellai.com/examples)

## Next Steps
Proceed to `retellai-local-dev-loop` for development workflow setup.