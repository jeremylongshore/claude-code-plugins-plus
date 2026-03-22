---
name: anima-hello-world
description: |
  Create a minimal working Anima example.
  Use when starting a new Anima integration, testing your setup,
  or learning basic Anima API patterns.
  Trigger with phrases like "anima hello world", "anima example",
  "anima quick start", "simple anima code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anima]
---

# Anima Hello World

## Overview

Connect to Anima and list your design files via the API.


## Prerequisites
- Completed `anima-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AnimaClient } from '@anima/sdk';

const client = new AnimaClient({

  accessToken: process.env.ANIMA_ACCESS_TOKEN,

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
- Working code file with Anima client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Anima connection is working.
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
import { AnimaClient } from '@anima/sdk';

const client = new AnimaClient({

  accessToken: process.env.ANIMA_ACCESS_TOKEN,

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
from anima import AnimaClient

client = AnimaClient()

files = client.files.list()
print(f"Found {len(files)} design files:")
for f in files[:5]:
    print(f"  - {f.name} (modified: {f.last_modified})")

```

## Resources
- [Anima Getting Started](https://docs.anima.com/getting-started)
- [Anima API Reference](https://docs.anima.com/api)
- [Anima Examples](https://docs.anima.com/examples)

## Next Steps
Proceed to `anima-local-dev-loop` for development workflow setup.