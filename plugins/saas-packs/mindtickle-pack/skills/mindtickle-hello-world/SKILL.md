---
name: mindtickle-hello-world
description: |
  Create a minimal working Mindtickle example.
  Use when starting a new Mindtickle integration, testing your setup,
  or learning basic Mindtickle API patterns.
  Trigger with phrases like "mindtickle hello world", "mindtickle example",
  "mindtickle quick start", "simple mindtickle code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, mindtickle]
---

# Mindtickle Hello World

## Overview

Pull your first contacts from Mindtickle and display them.


## Prerequisites
- Completed `mindtickle-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { MindtickleClient } from '@mindtickle/sdk';

const client = new MindtickleClient({

  apiKey: process.env.MINDTICKLE_API_KEY,

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
- Working code file with Mindtickle client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Mindtickle connection is working.
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
import { MindtickleClient } from '@mindtickle/sdk';

const client = new MindtickleClient({

  apiKey: process.env.MINDTICKLE_API_KEY,

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
from mindtickle import MindtickleClient

client = MindtickleClient()

contacts = client.contacts.list(limit=5)
print(f"Found {contacts.total} contacts. First 5:")
for c in contacts.data:
    print(f"  - {c.name} <{c.email}> ({c.company})")

```

## Resources
- [Mindtickle Getting Started](https://docs.mindtickle.com/getting-started)
- [Mindtickle API Reference](https://docs.mindtickle.com/api)
- [Mindtickle Examples](https://docs.mindtickle.com/examples)

## Next Steps
Proceed to `mindtickle-local-dev-loop` for development workflow setup.