---
name: apollo-hello-world
description: |
  Create a minimal working Apollo example.
  Use when starting a new Apollo integration, testing your setup,
  or learning basic Apollo API patterns.
  Trigger with phrases like "apollo hello world", "apollo example",
  "apollo quick start", "simple apollo code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apollo]
---

# Apollo Hello World

## Overview

Pull your first contacts from Apollo and display them.


## Prerequisites
- Completed `apollo-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ApolloClient } from '@apollo/sdk';

const client = new ApolloClient({

  apiKey: process.env.APOLLO_API_KEY,

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
- Working code file with Apollo client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Apollo connection is working.
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
import { ApolloClient } from '@apollo/sdk';

const client = new ApolloClient({

  apiKey: process.env.APOLLO_API_KEY,

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
from apollo import ApolloClient

client = ApolloClient()

contacts = client.contacts.list(limit=5)
print(f"Found {contacts.total} contacts. First 5:")
for c in contacts.data:
    print(f"  - {c.name} <{c.email}> ({c.company})")

```

## Resources
- [Apollo Getting Started](https://docs.apollo.com/getting-started)
- [Apollo API Reference](https://docs.apollo.com/api)
- [Apollo Examples](https://docs.apollo.com/examples)

## Next Steps
Proceed to `apollo-local-dev-loop` for development workflow setup.