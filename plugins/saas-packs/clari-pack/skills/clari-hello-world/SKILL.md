---
name: clari-hello-world
description: |
  Create a minimal working Clari example.
  Use when starting a new Clari integration, testing your setup,
  or learning basic Clari API patterns.
  Trigger with phrases like "clari hello world", "clari example",
  "clari quick start", "simple clari code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clari]
---

# Clari Hello World

## Overview

Pull your first contacts from Clari and display them.


## Prerequisites
- Completed `clari-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ClariClient } from '@clari/sdk';

const client = new ClariClient({

  apiKey: process.env.CLARI_API_KEY,

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
- Working code file with Clari client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Clari connection is working.
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
import { ClariClient } from '@clari/sdk';

const client = new ClariClient({

  apiKey: process.env.CLARI_API_KEY,

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
from clari import ClariClient

client = ClariClient()

contacts = client.contacts.list(limit=5)
print(f"Found {contacts.total} contacts. First 5:")
for c in contacts.data:
    print(f"  - {c.name} <{c.email}> ({c.company})")

```

## Resources
- [Clari Getting Started](https://docs.clari.com/getting-started)
- [Clari API Reference](https://docs.clari.com/api)
- [Clari Examples](https://docs.clari.com/examples)

## Next Steps
Proceed to `clari-local-dev-loop` for development workflow setup.