---
name: shopify-hello-world
description: |
  Create a minimal working Shopify example.
  Use when starting a new Shopify integration, testing your setup,
  or learning basic Shopify API patterns.
  Trigger with phrases like "shopify hello world", "shopify example",
  "shopify quick start", "simple shopify code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, shopify]
---

# Shopify Hello World

## Overview

Minimal working example demonstrating core Shopify functionality.


## Prerequisites
- Completed `shopify-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { ShopifyClient } from '@shopify/sdk';

const client = new ShopifyClient({

  apiKey: process.env.SHOPIFY_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const resources = await client.resources.list({ limit: 5 });
console.log(`Found ${resources.total} resources:`);
resources.data.forEach(r => console.log(`  - ${r.name} (${r.type}) — ${r.status}`));

}

main().catch(console.error);
```

## Output
- Working code file with Shopify client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Shopify connection is working.
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
import { ShopifyClient } from '@shopify/sdk';

const client = new ShopifyClient({

  apiKey: process.env.SHOPIFY_API_KEY,

});

async function main() {
  const resources = await client.resources.list({ limit: 5 });
console.log(`Found ${resources.total} resources:`);
resources.data.forEach(r => console.log(`  - ${r.name} (${r.type}) — ${r.status}`));

}

main().catch(console.error);
```

### Python Example
```python
from shopify import ShopifyClient

client = ShopifyClient()

resources = client.resources.list(limit=5)
print(f"Found {resources.total} resources:")
for r in resources.data:
    print(f"  - {r.name} ({r.type}) — {r.status}")

```

## Resources
- [Shopify Getting Started](https://docs.shopify.com/getting-started)
- [Shopify API Reference](https://docs.shopify.com/api)
- [Shopify Examples](https://docs.shopify.com/examples)

## Next Steps
Proceed to `shopify-local-dev-loop` for development workflow setup.