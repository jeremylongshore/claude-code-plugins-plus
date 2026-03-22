---
name: attio-hello-world
description: |
  Create a minimal working Attio example.
  Use when starting a new Attio integration, testing your setup,
  or learning basic Attio API patterns.
  Trigger with phrases like "attio hello world", "attio example",
  "attio quick start", "simple attio code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, attio]
---

# Attio Hello World

## Overview

Pull your first contacts from Attio and display them.


## Prerequisites
- Completed `attio-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AttioClient } from '@attio/sdk';

const client = new AttioClient({

  apiKey: process.env.ATTIO_API_KEY,

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
- Working code file with Attio client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Attio connection is working.
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
import { AttioClient } from '@attio/sdk';

const client = new AttioClient({

  apiKey: process.env.ATTIO_API_KEY,

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
from attio import AttioClient

client = AttioClient()

contacts = client.contacts.list(limit=5)
print(f"Found {contacts.total} contacts. First 5:")
for c in contacts.data:
    print(f"  - {c.name} <{c.email}> ({c.company})")

```

## Resources
- [Attio Getting Started](https://docs.attio.com/getting-started)
- [Attio API Reference](https://docs.attio.com/api)
- [Attio Examples](https://docs.attio.com/examples)

## Next Steps
Proceed to `attio-local-dev-loop` for development workflow setup.