---
name: gamma-hello-world
description: |
  Create a minimal working Gamma example.
  Use when starting a new Gamma integration, testing your setup,
  or learning basic Gamma API patterns.
  Trigger with phrases like "gamma hello world", "gamma example",
  "gamma quick start", "simple gamma code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, gamma]
---

# Gamma Hello World

## Overview

Connect to Gamma and list your design files via the API.


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

const client = new GammaClient({

  accessToken: process.env.GAMMA_ACCESS_TOKEN,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const files = await client.files.list();
console.log(`Found ${files.length} design files:`);
files.slice(0, 5).forEach(f => console.log(`  - ${f.name} (modified: ${f.lastModified})`));

}

main().catch(console.error);
```

## Output
- Working code file with Gamma client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Gamma connection is working.
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

const client = new GammaClient({

  accessToken: process.env.GAMMA_ACCESS_TOKEN,

});

async function main() {
  const files = await client.files.list();
console.log(`Found ${files.length} design files:`);
files.slice(0, 5).forEach(f => console.log(`  - ${f.name} (modified: ${f.lastModified})`));

}

main().catch(console.error);
```

### Python Example
```python
from gamma import GammaClient

client = GammaClient()

files = client.files.list()
print(f"Found {len(files)} design files:")
for f in files[:5]:
    print(f"  - {f.name} (modified: {f.last_modified})")

```

## Resources
- [Gamma Getting Started](https://docs.gamma.com/getting-started)
- [Gamma API Reference](https://docs.gamma.com/api)
- [Gamma Examples](https://docs.gamma.com/examples)

## Next Steps
Proceed to `gamma-local-dev-loop` for development workflow setup.