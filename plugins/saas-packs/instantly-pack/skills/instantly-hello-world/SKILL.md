---
name: instantly-hello-world
description: |
  Create a minimal working Instantly example.
  Use when starting a new Instantly integration, testing your setup,
  or learning basic Instantly API patterns.
  Trigger with phrases like "instantly hello world", "instantly example",
  "instantly quick start", "simple instantly code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, instantly]
---

# Instantly Hello World

## Overview

Pull your first contacts from Instantly and display them.


## Prerequisites
- Completed `instantly-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { InstantlyClient } from '@instantly/sdk';

const client = new InstantlyClient({

  apiKey: process.env.INSTANTLY_API_KEY,

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
- Working code file with Instantly client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Instantly connection is working.
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
import { InstantlyClient } from '@instantly/sdk';

const client = new InstantlyClient({

  apiKey: process.env.INSTANTLY_API_KEY,

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
from instantly import InstantlyClient

client = InstantlyClient()

contacts = client.contacts.list(limit=5)
print(f"Found {contacts.total} contacts. First 5:")
for c in contacts.data:
    print(f"  - {c.name} <{c.email}> ({c.company})")

```

## Resources
- [Instantly Getting Started](https://docs.instantly.com/getting-started)
- [Instantly API Reference](https://docs.instantly.com/api)
- [Instantly Examples](https://docs.instantly.com/examples)

## Next Steps
Proceed to `instantly-local-dev-loop` for development workflow setup.