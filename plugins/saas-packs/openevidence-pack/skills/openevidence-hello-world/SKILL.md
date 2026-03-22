---
name: openevidence-hello-world
description: |
  Create a minimal working OpenEvidence example.
  Use when starting a new OpenEvidence integration, testing your setup,
  or learning basic OpenEvidence API patterns.
  Trigger with phrases like "openevidence hello world", "openevidence example",
  "openevidence quick start", "simple openevidence code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openevidence]
---

# OpenEvidence Hello World

## Overview

Send your first prompt to the OpenEvidence API and get a model response back.


## Prerequisites
- Completed `openevidence-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { OpenEvidenceClient } from '@openevidence/sdk';

const client = new OpenEvidenceClient({

  apiKey: process.env.OPENEVIDENCE_API_KEY,

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
- Working code file with OpenEvidence client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your OpenEvidence connection is working.
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
import { OpenEvidenceClient } from '@openevidence/sdk';

const client = new OpenEvidenceClient({

  apiKey: process.env.OPENEVIDENCE_API_KEY,

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
from openevidence import OpenEvidenceClient

client = OpenEvidenceClient()

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=64,
)
print(response.choices[0].message.content)

```

## Resources
- [OpenEvidence Getting Started](https://docs.openevidence.com/getting-started)
- [OpenEvidence API Reference](https://docs.openevidence.com/api)
- [OpenEvidence Examples](https://docs.openevidence.com/examples)

## Next Steps
Proceed to `openevidence-local-dev-loop` for development workflow setup.