---
name: clay-hello-world
description: |
  Create a minimal working Clay example.
  Use when starting a new Clay integration, testing your setup,
  or learning basic Clay API patterns.
  Trigger with phrases like "clay hello world", "clay example",
  "clay quick start", "simple clay code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clay]
---

# Clay Hello World

## Overview

Pull your first contacts from Clay and display them.


## Prerequisites
- Completed `clay-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ClayClient } from '@clay/sdk';

const client = new ClayClient({

  apiKey: process.env.CLAY_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const contacts = await client.contacts.list({ limit: 5 });
console.log(`Found ${contacts.total} contacts. First 5:`);
contacts.data.forEach(c => console.log(`  - ${c.name} <${c.email}> (${c.company})`));

}

main().catch(console.error);
```

## Output
- Working code file with Clay client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Clay connection is working.
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
import { ClayClient } from '@clay/sdk';

const client = new ClayClient({

  apiKey: process.env.CLAY_API_KEY,

});

async function main() {
  const contacts = await client.contacts.list({ limit: 5 });
console.log(`Found ${contacts.total} contacts. First 5:`);
contacts.data.forEach(c => console.log(`  - ${c.name} <${c.email}> (${c.company})`));

}

main().catch(console.error);
```

### Python Example
```python
from clay import ClayClient

client = ClayClient()

contacts = client.contacts.list(limit=5)
print(f"Found {contacts.total} contacts. First 5:")
for c in contacts.data:
    print(f"  - {c.name} <{c.email}> ({c.company})")

```

## Resources
- [Clay Getting Started](https://docs.clay.com/getting-started)
- [Clay API Reference](https://docs.clay.com/api)
- [Clay Examples](https://docs.clay.com/examples)

## Next Steps
Proceed to `clay-local-dev-loop` for development workflow setup.