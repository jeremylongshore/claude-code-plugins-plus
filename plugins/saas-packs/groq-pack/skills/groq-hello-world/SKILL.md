---
name: groq-hello-world
description: |
  Create a minimal working Groq example.
  Use when starting a new Groq integration, testing your setup,
  or learning basic Groq API patterns.
  Trigger with phrases like "groq hello world", "groq example",
  "groq quick start", "simple groq code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, groq]
---

# Groq Hello World

## Overview

Send your first prompt to the Groq API and get a model response back.


## Prerequisites
- Completed `groq-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { GroqClient } from '@groq/sdk';

const client = new GroqClient({

  apiKey: process.env.GROQ_API_KEY,

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
- Working code file with Groq client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Groq connection is working.
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
import { GroqClient } from '@groq/sdk';

const client = new GroqClient({

  apiKey: process.env.GROQ_API_KEY,

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
from groq import GroqClient

client = GroqClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Groq Getting Started](https://docs.groq.com/getting-started)
- [Groq API Reference](https://docs.groq.com/api)
- [Groq Examples](https://docs.groq.com/examples)

## Next Steps
Proceed to `groq-local-dev-loop` for development workflow setup.