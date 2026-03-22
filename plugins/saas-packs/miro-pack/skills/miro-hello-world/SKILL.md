---
name: miro-hello-world
description: |
  Create a minimal working Miro example.
  Use when starting a new Miro integration, testing your setup,
  or learning basic Miro API patterns.
  Trigger with phrases like "miro hello world", "miro example",
  "miro quick start", "simple miro code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, miro]
---

# Miro Hello World

## Overview

Connect to Miro and list your design files via the API.


## Prerequisites
- Completed `miro-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { MiroClient } from '@miro/sdk';

const client = new MiroClient({

  accessToken: process.env.MIRO_ACCESS_TOKEN,

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
- Working code file with Miro client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Miro connection is working.
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
import { MiroClient } from '@miro/sdk';

const client = new MiroClient({

  accessToken: process.env.MIRO_ACCESS_TOKEN,

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
from miro import MiroClient

client = MiroClient()

files = client.files.list()
print(f"Found {len(files)} design files:")
for f in files[:5]:
    print(f"  - {f.name} (modified: {f.last_modified})")

```

## Resources
- [Miro Getting Started](https://docs.miro.com/getting-started)
- [Miro API Reference](https://docs.miro.com/api)
- [Miro Examples](https://docs.miro.com/examples)

## Next Steps
Proceed to `miro-local-dev-loop` for development workflow setup.