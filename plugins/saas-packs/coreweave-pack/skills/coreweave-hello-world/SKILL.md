---
name: coreweave-hello-world
description: |
  Create a minimal working CoreWeave example.
  Use when starting a new CoreWeave integration, testing your setup,
  or learning basic CoreWeave API patterns.
  Trigger with phrases like "coreweave hello world", "coreweave example",
  "coreweave quick start", "simple coreweave code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, coreweave]
---

# CoreWeave Hello World

## Overview

List your monitored projects and check system status via CoreWeave.


## Prerequisites
- Completed `coreweave-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { CoreWeaveClient } from '@coreweave/sdk';

const client = new CoreWeaveClient({

  apiKey: process.env.COREWEAVE_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const projects = await client.projects.list();
console.log(`Monitoring ${projects.length} projects:`);
projects.forEach(p => console.log(`  - ${p.name}: ${p.status} (${p.eventCount} events/24h)`));

}

main().catch(console.error);
```

## Output
- Working code file with CoreWeave client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your CoreWeave connection is working.
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
import { CoreWeaveClient } from '@coreweave/sdk';

const client = new CoreWeaveClient({

  apiKey: process.env.COREWEAVE_API_KEY,

});

async function main() {
  const projects = await client.projects.list();
console.log(`Monitoring ${projects.length} projects:`);
projects.forEach(p => console.log(`  - ${p.name}: ${p.status} (${p.eventCount} events/24h)`));

}

main().catch(console.error);
```

### Python Example
```python
from coreweave import CoreWeaveClient

client = CoreWeaveClient()

projects = client.projects.list()
print(f"Monitoring {len(projects)} projects:")
for p in projects:
    print(f"  - {p.name}: {p.status} ({p.event_count} events/24h)")

```

## Resources
- [CoreWeave Getting Started](https://docs.coreweave.com/getting-started)
- [CoreWeave API Reference](https://docs.coreweave.com/api)
- [CoreWeave Examples](https://docs.coreweave.com/examples)

## Next Steps
Proceed to `coreweave-local-dev-loop` for development workflow setup.