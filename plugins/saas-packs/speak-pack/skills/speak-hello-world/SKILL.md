---
name: speak-hello-world
description: |
  Create a minimal working Speak example.
  Use when starting a new Speak integration, testing your setup,
  or learning basic Speak API patterns.
  Trigger with phrases like "speak hello world", "speak example",
  "speak quick start", "simple speak code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, speak]
---

# Speak Hello World

## Overview

Send your first prompt to the Speak API and get a model response back.


## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { SpeakClient } from '@speak/sdk';

const client = new SpeakClient({

  apiKey: process.env.SPEAK_API_KEY,

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
- Working code file with Speak client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Speak connection is working.
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
import { SpeakClient } from '@speak/sdk';

const client = new SpeakClient({

  apiKey: process.env.SPEAK_API_KEY,

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
from speak import SpeakClient

client = SpeakClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Speak Getting Started](https://docs.speak.com/getting-started)
- [Speak API Reference](https://docs.speak.com/api)
- [Speak Examples](https://docs.speak.com/examples)

## Next Steps
Proceed to `speak-local-dev-loop` for development workflow setup.