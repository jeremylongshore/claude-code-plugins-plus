---
name: adobe-hello-world
description: |
  Create a minimal working Adobe example.
  Use when starting a new Adobe integration, testing your setup,
  or learning basic Adobe API patterns.
  Trigger with phrases like "adobe hello world", "adobe example",
  "adobe quick start", "simple adobe code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, adobe]
---

# Adobe Hello World

## Overview

Connect to Adobe and list your design files via the API.


## Prerequisites
- Completed `adobe-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AdobeClient } from '@adobe/sdk';

const client = new AdobeClient({

  accessToken: process.env.ADOBE_ACCESS_TOKEN,

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
- Working code file with Adobe client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Adobe connection is working.
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
import { AdobeClient } from '@adobe/sdk';

const client = new AdobeClient({

  accessToken: process.env.ADOBE_ACCESS_TOKEN,

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
from adobe import AdobeClient

client = AdobeClient()

files = client.files.list()
print(f"Found {len(files)} design files:")
for f in files[:5]:
    print(f"  - {f.name} (modified: {f.last_modified})")

```

## Resources
- [Adobe Getting Started](https://docs.adobe.com/getting-started)
- [Adobe API Reference](https://docs.adobe.com/api)
- [Adobe Examples](https://docs.adobe.com/examples)

## Next Steps
Proceed to `adobe-local-dev-loop` for development workflow setup.