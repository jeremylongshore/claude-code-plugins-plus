---
name: gamma-hello-world
description: |
  Create a minimal working Gamma example.
  Use when starting a new Gamma integration, testing your setup,
  or learning basic Gamma API patterns.
  Trigger with phrases like "gamma hello world", "gamma example",
  "gamma quick start", "simple gamma code", "create gamma presentation".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Hello World

## Overview
Minimal working example demonstrating core Gamma presentation generation functionality.

## Prerequisites
- Completed `gamma-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { GammaClient } from '@gamma/sdk';

const gamma = new GammaClient({
  apiKey: process.env.GAMMA_API_KEY,
});
```

### Step 3: Generate Your First Presentation
```typescript
async function main() {
  const presentation = await gamma.presentations.create({
    title: 'Hello Gamma!',
    prompt: 'Create a 3-slide introduction to AI presentations',
    style: 'professional',
  });

  console.log('Presentation created:', presentation.url);
}

main().catch(console.error);
```

## Output
- Working code file with Gamma client initialization
- Successful API response with presentation URL
- Console output showing:
```
Presentation created: https://gamma.app/docs/abcd1234
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
import { GammaClient } from '@gamma/sdk';

const gamma = new GammaClient({
  apiKey: process.env.GAMMA_API_KEY,
});

async function main() {
  const result = await gamma.presentations.create({
    title: 'My First Presentation',
    prompt: 'Explain the benefits of AI-powered presentations',
  });

  console.log('View at:', result.url);
}

main().catch(console.error);
```

### Python Example
```python
from gamma import GammaClient

client = GammaClient()

response = client.presentations.create(
    title='My First Presentation',
    prompt='Explain the benefits of AI-powered presentations'
)

print(f'View at: {response.url}')
```

## Resources
- [Gamma Getting Started](https://gamma.app/docs/getting-started)
- [Gamma API Reference](https://gamma.app/docs/api)
- [Gamma Examples](https://gamma.app/docs/examples)

## Next Steps
Proceed to `gamma-local-dev-loop` for development workflow setup.