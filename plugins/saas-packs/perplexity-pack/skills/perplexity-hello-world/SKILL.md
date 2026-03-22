---
name: perplexity-hello-world
description: |
  Create a minimal working Perplexity example.
  Use when starting a new Perplexity integration, testing your setup,
  or learning basic Perplexity API patterns.
  Trigger with phrases like "perplexity hello world", "perplexity example",
  "perplexity quick start", "simple perplexity code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, perplexity]
---

# Perplexity Hello World

## Overview

Send your first prompt to the Perplexity API and get a model response back.


## Prerequisites
- Completed `perplexity-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { PerplexityClient } from '@perplexity/sdk';

const client = new PerplexityClient({

  apiKey: process.env.PERPLEXITY_API_KEY,

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
- Working code file with Perplexity client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Perplexity connection is working.
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
import { PerplexityClient } from '@perplexity/sdk';

const client = new PerplexityClient({

  apiKey: process.env.PERPLEXITY_API_KEY,

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
from perplexity import PerplexityClient

client = PerplexityClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [Perplexity Getting Started](https://docs.perplexity.com/getting-started)
- [Perplexity API Reference](https://docs.perplexity.com/api)
- [Perplexity Examples](https://docs.perplexity.com/examples)

## Next Steps
Proceed to `perplexity-local-dev-loop` for development workflow setup.