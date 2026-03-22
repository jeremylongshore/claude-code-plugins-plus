---
name: shopify-install-auth
description: |
  Install and configure Shopify SDK/CLI authentication.
  Use when setting up a new Shopify integration, configuring API keys,
  or initializing Shopify in your project.
  Trigger with phrases like "install shopify", "setup shopify",
  "shopify auth", "configure shopify API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, shopify]
---

# Shopify Install & Auth

## Overview
Set up Shopify SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Shopify account with API access

- OAuth2 access token or personal API token from Shopify settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @shopify/sdk

# Python
pip install shopify
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export SHOPIFY_API_KEY="your-api-key"

# Or create .env file
echo 'SHOPIFY_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const org = await client.organization.get();
console.log(`Connected: ${org.name} (${org.plan} plan)`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in Shopify dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.shopify.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ShopifyClient } from '@shopify/sdk';

const client = new ShopifyClient({

  apiKey: process.env.SHOPIFY_API_KEY,

});
```

### Python Setup
```python
from shopify import ShopifyClient

client = ShopifyClient(

    api_key=os.environ.get('SHOPIFY_API_KEY')

)
```

## Resources
- [Shopify Documentation](https://docs.shopify.com)
- [Shopify Dashboard](https://api.shopify.com)
- [Shopify Status](https://status.shopify.com)

## Next Steps
After successful auth, proceed to `shopify-hello-world` for your first API call.