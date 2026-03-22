---
name: framer-hello-world
description: |
  Create a minimal working Framer example.
  Use when starting a new Framer integration, testing your setup,
  or learning basic Framer API patterns.
  Trigger with phrases like "framer hello world", "framer example",
  "framer quick start", "simple framer code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, framer]
---

# Framer Hello World

## Overview

Connect to Framer and list your design files via the API.


## Prerequisites
- Completed `framer-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { FramerClient } from '@framer/sdk';

const client = new FramerClient({

  accessToken: process.env.FRAMER_ACCESS_TOKEN,

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
- Working code file with Framer client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Framer connection is working.
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
import { FramerClient } from '@framer/sdk';

const client = new FramerClient({

  accessToken: process.env.FRAMER_ACCESS_TOKEN,

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
from framer import FramerClient

client = FramerClient()

files = client.files.list()
print(f"Found {len(files)} design files:")
for f in files[:5]:
    print(f"  - {f.name} (modified: {f.last_modified})")

```

## Resources
- [Framer Getting Started](https://docs.framer.com/getting-started)
- [Framer API Reference](https://docs.framer.com/api)
- [Framer Examples](https://docs.framer.com/examples)

## Next Steps
Proceed to `framer-local-dev-loop` for development workflow setup.