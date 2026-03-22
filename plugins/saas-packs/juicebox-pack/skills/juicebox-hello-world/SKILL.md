---
name: juicebox-hello-world
description: |
  Create a minimal working Juicebox example.
  Use when starting a new Juicebox integration, testing your setup,
  or learning basic Juicebox API patterns.
  Trigger with phrases like "juicebox hello world", "juicebox example",
  "juicebox quick start", "simple juicebox code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, juicebox]
---

# Juicebox Hello World

## Overview

Pull your first contacts from Juicebox and display them.


## Prerequisites
- Completed `juicebox-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { JuiceboxClient } from '@juicebox/sdk';

const client = new JuiceboxClient({

  apiKey: process.env.JUICEBOX_API_KEY,

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
- Working code file with Juicebox client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Juicebox connection is working.
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
import { JuiceboxClient } from '@juicebox/sdk';

const client = new JuiceboxClient({

  apiKey: process.env.JUICEBOX_API_KEY,

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
from juicebox import JuiceboxClient

client = JuiceboxClient()

contacts = client.contacts.list(limit=5)
print(f"Found {contacts.total} contacts. First 5:")
for c in contacts.data:
    print(f"  - {c.name} <{c.email}> ({c.company})")

```

## Resources
- [Juicebox Getting Started](https://docs.juicebox.com/getting-started)
- [Juicebox API Reference](https://docs.juicebox.com/api)
- [Juicebox Examples](https://docs.juicebox.com/examples)

## Next Steps
Proceed to `juicebox-local-dev-loop` for development workflow setup.