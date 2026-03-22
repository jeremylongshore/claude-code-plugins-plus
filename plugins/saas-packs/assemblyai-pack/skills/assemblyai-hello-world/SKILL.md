---
name: assemblyai-hello-world
description: |
  Create a minimal working AssemblyAI example.
  Use when starting a new AssemblyAI integration, testing your setup,
  or learning basic AssemblyAI API patterns.
  Trigger with phrases like "assemblyai hello world", "assemblyai example",
  "assemblyai quick start", "simple assemblyai code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, assemblyai]
---

# AssemblyAI Hello World

## Overview

Send your first prompt to the AssemblyAI API and get a model response back.


## Prerequisites
- Completed `assemblyai-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AssemblyAIClient } from '@assemblyai/sdk';

const client = new AssemblyAIClient({

  apiKey: process.env.ASSEMBLYAI_API_KEY,

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
- Working code file with AssemblyAI client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your AssemblyAI connection is working.
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
import { AssemblyAIClient } from '@assemblyai/sdk';

const client = new AssemblyAIClient({

  apiKey: process.env.ASSEMBLYAI_API_KEY,

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
from assemblyai import AssemblyAIClient

client = AssemblyAIClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [AssemblyAI Getting Started](https://docs.assemblyai.com/getting-started)
- [AssemblyAI API Reference](https://docs.assemblyai.com/api)
- [AssemblyAI Examples](https://docs.assemblyai.com/examples)

## Next Steps
Proceed to `assemblyai-local-dev-loop` for development workflow setup.