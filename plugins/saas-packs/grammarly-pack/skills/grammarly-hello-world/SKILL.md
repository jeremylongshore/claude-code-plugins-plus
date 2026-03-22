---
name: grammarly-hello-world
description: |
  Create a minimal working Grammarly example.
  Use when starting a new Grammarly integration, testing your setup,
  or learning basic Grammarly API patterns.
  Trigger with phrases like "grammarly hello world", "grammarly example",
  "grammarly quick start", "simple grammarly code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, grammarly]
---

# Grammarly Hello World

## Overview

Send your first prompt to the Grammarly API and get a model response back.


## Prerequisites
- Completed `grammarly-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { GrammarlyClient } from '@grammarly/sdk';

const client = new GrammarlyClient({

  apiKey: process.env.GRAMMARLY_API_KEY,

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
- Working code file with Grammarly client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Grammarly connection is working.
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
import { GrammarlyClient } from '@grammarly/sdk';

const client = new GrammarlyClient({

  apiKey: process.env.GRAMMARLY_API_KEY,

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
from grammarly import GrammarlyClient

client = GrammarlyClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Grammarly Getting Started](https://docs.grammarly.com/getting-started)
- [Grammarly API Reference](https://docs.grammarly.com/api)
- [Grammarly Examples](https://docs.grammarly.com/examples)

## Next Steps
Proceed to `grammarly-local-dev-loop` for development workflow setup.