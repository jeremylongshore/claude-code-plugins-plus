---
name: figma-hello-world
description: |
  Create a minimal working Figma example.
  Use when starting a new Figma integration, testing your setup,
  or learning basic Figma API patterns.
  Trigger with phrases like "figma hello world", "figma example",
  "figma quick start", "simple figma code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, figma]
---

# Figma Hello World

## Overview

Connect to Figma and list your design files via the API.


## Prerequisites
- Completed `figma-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { FigmaClient } from '@figma/sdk';

const client = new FigmaClient({

  accessToken: process.env.FIGMA_ACCESS_TOKEN,

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
- Working code file with Figma client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Figma connection is working.
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
import { FigmaClient } from '@figma/sdk';

const client = new FigmaClient({

  accessToken: process.env.FIGMA_ACCESS_TOKEN,

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
from figma import FigmaClient

client = FigmaClient()

files = client.files.list()
print(f"Found {len(files)} design files:")
for f in files[:5]:
    print(f"  - {f.name} (modified: {f.last_modified})")

```

## Resources
- [Figma Getting Started](https://docs.figma.com/getting-started)
- [Figma API Reference](https://docs.figma.com/api)
- [Figma Examples](https://docs.figma.com/examples)

## Next Steps
Proceed to `figma-local-dev-loop` for development workflow setup.