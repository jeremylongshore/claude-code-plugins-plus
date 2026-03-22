---
name: techsmith-hello-world
description: |
  Create a minimal working TechSmith example.
  Use when starting a new TechSmith integration, testing your setup,
  or learning basic TechSmith API patterns.
  Trigger with phrases like "techsmith hello world", "techsmith example",
  "techsmith quick start", "simple techsmith code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, techsmith]
---

# TechSmith Hello World

## Overview

Connect to TechSmith and list your design files via the API.


## Prerequisites
- Completed `techsmith-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { TechSmithClient } from '@techsmith/sdk';

const client = new TechSmithClient({

  accessToken: process.env.TECHSMITH_ACCESS_TOKEN,

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
- Working code file with TechSmith client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your TechSmith connection is working.
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
import { TechSmithClient } from '@techsmith/sdk';

const client = new TechSmithClient({

  accessToken: process.env.TECHSMITH_ACCESS_TOKEN,

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
from techsmith import TechSmithClient

client = TechSmithClient()

files = client.files.list()
print(f"Found {len(files)} design files:")
for f in files[:5]:
    print(f"  - {f.name} (modified: {f.last_modified})")

```

## Resources
- [TechSmith Getting Started](https://docs.techsmith.com/getting-started)
- [TechSmith API Reference](https://docs.techsmith.com/api)
- [TechSmith Examples](https://docs.techsmith.com/examples)

## Next Steps
Proceed to `techsmith-local-dev-loop` for development workflow setup.