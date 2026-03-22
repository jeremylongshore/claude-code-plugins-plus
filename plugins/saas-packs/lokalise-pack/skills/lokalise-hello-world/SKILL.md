---
name: lokalise-hello-world
description: |
  Create a minimal working Lokalise example.
  Use when starting a new Lokalise integration, testing your setup,
  or learning basic Lokalise API patterns.
  Trigger with phrases like "lokalise hello world", "lokalise example",
  "lokalise quick start", "simple lokalise code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lokalise]
---

# Lokalise Hello World

## Overview

List your projects and trigger your first action via the Lokalise API.


## Prerequisites
- Completed `lokalise-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { LokaliseClient } from '@lokalise/sdk';

const client = new LokaliseClient({

  apiKey: process.env.LOKALISE_API_KEY,

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
- Working code file with Lokalise client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Lokalise connection is working.
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
import { LokaliseClient } from '@lokalise/sdk';

const client = new LokaliseClient({

  apiKey: process.env.LOKALISE_API_KEY,

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
from lokalise import LokaliseClient

client = LokaliseClient()

projects = client.projects.list()
print(f"Found {len(projects)} projects:")
for p in projects:
    print(f"  - {p.name} ({p.status})")

```

## Resources
- [Lokalise Getting Started](https://docs.lokalise.com/getting-started)
- [Lokalise API Reference](https://docs.lokalise.com/api)
- [Lokalise Examples](https://docs.lokalise.com/examples)

## Next Steps
Proceed to `lokalise-local-dev-loop` for development workflow setup.