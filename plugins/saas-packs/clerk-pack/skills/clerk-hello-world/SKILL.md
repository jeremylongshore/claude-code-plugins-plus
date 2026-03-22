---
name: clerk-hello-world
description: |
  Create a minimal working Clerk example.
  Use when starting a new Clerk integration, testing your setup,
  or learning basic Clerk API patterns.
  Trigger with phrases like "clerk hello world", "clerk example",
  "clerk quick start", "simple clerk code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clerk]
---

# Clerk Hello World

## Overview

List your projects and trigger your first action via the Clerk API.


## Prerequisites
- Completed `clerk-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ClerkClient } from '@clerk/sdk';

const client = new ClerkClient({

  apiKey: process.env.CLERK_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const projects = await client.projects.list();
console.log(`Found ${projects.length} projects:`);
projects.forEach(p => console.log(`  - ${p.name} (${p.status})`));

}

main().catch(console.error);
```

## Output
- Working code file with Clerk client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Clerk connection is working.
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
import { ClerkClient } from '@clerk/sdk';

const client = new ClerkClient({

  apiKey: process.env.CLERK_API_KEY,

});

async function main() {
  const projects = await client.projects.list();
console.log(`Found ${projects.length} projects:`);
projects.forEach(p => console.log(`  - ${p.name} (${p.status})`));

}

main().catch(console.error);
```

### Python Example
```python
from clerk import ClerkClient

client = ClerkClient()

projects = client.projects.list()
print(f"Found {len(projects)} projects:")
for p in projects:
    print(f"  - {p.name} ({p.status})")

```

## Resources
- [Clerk Getting Started](https://docs.clerk.com/getting-started)
- [Clerk API Reference](https://docs.clerk.com/api)
- [Clerk Examples](https://docs.clerk.com/examples)

## Next Steps
Proceed to `clerk-local-dev-loop` for development workflow setup.