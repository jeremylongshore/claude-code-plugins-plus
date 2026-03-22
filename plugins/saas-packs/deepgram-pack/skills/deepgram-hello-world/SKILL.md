---
name: deepgram-hello-world
description: |
  Create a minimal working Deepgram example.
  Use when starting a new Deepgram integration, testing your setup,
  or learning basic Deepgram API patterns.
  Trigger with phrases like "deepgram hello world", "deepgram example",
  "deepgram quick start", "simple deepgram code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, deepgram]
---

# Deepgram Hello World

## Overview

Send your first prompt to the Deepgram API and get a model response back.


## Prerequisites
- Completed `deepgram-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { DeepgramClient } from '@deepgram/sdk';

const client = new DeepgramClient({

  apiKey: process.env.DEEPGRAM_API_KEY,

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
- Working code file with Deepgram client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Deepgram connection is working.
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
import { DeepgramClient } from '@deepgram/sdk';

const client = new DeepgramClient({

  apiKey: process.env.DEEPGRAM_API_KEY,

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
from deepgram import DeepgramClient

client = DeepgramClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Deepgram Getting Started](https://docs.deepgram.com/getting-started)
- [Deepgram API Reference](https://docs.deepgram.com/api)
- [Deepgram Examples](https://docs.deepgram.com/examples)

## Next Steps
Proceed to `deepgram-local-dev-loop` for development workflow setup.