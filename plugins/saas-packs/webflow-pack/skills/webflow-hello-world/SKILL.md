---
name: webflow-hello-world
description: |
  Create a minimal working Webflow example.
  Use when starting a new Webflow integration, testing your setup,
  or learning basic Webflow API patterns.
  Trigger with phrases like "webflow hello world", "webflow example",
  "webflow quick start", "simple webflow code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, webflow]
---

# Webflow Hello World

## Overview

Connect to Webflow and list your design files via the API.


## Prerequisites
- Completed `webflow-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { WebflowClient } from '@webflow/sdk';

const client = new WebflowClient({

  accessToken: process.env.WEBFLOW_ACCESS_TOKEN,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const files = await client.files.list();
console.log(`Found ${files.length} design files:`);
files.slice(0, 5).forEach(f => console.log(`  - ${f.name} (modified: ${f.lastModified})`));

}

main().catch(console.error);
```

## Output
- Working code file with Webflow client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Webflow connection is working.
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
import { WebflowClient } from '@webflow/sdk';

const client = new WebflowClient({

  accessToken: process.env.WEBFLOW_ACCESS_TOKEN,

});

async function main() {
  const files = await client.files.list();
console.log(`Found ${files.length} design files:`);
files.slice(0, 5).forEach(f => console.log(`  - ${f.name} (modified: ${f.lastModified})`));

}

main().catch(console.error);
```

### Python Example
```python
from webflow import WebflowClient

client = WebflowClient()

files = client.files.list()
print(f"Found {len(files)} design files:")
for f in files[:5]:
    print(f"  - {f.name} (modified: {f.last_modified})")

```

## Resources
- [Webflow Getting Started](https://docs.webflow.com/getting-started)
- [Webflow API Reference](https://docs.webflow.com/api)
- [Webflow Examples](https://docs.webflow.com/examples)

## Next Steps
Proceed to `webflow-local-dev-loop` for development workflow setup.