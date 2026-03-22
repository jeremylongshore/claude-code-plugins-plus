---
name: apollo-install-auth
description: |
  Install and configure Apollo SDK/CLI authentication.
  Use when setting up a new Apollo integration, configuring API keys,
  or initializing Apollo in your project.
  Trigger with phrases like "install apollo", "setup apollo",
  "apollo auth", "configure apollo API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apollo]
---

# Apollo Install & Auth

## Overview
Set up Apollo SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Apollo account with API access

- OAuth2 access token or personal API token from Apollo settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @apollo/sdk

# Python
pip install apollo
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export APOLLO_API_KEY="your-api-key"

# Or create .env file
echo 'APOLLO_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const me = await client.users.me();
console.log(`Authenticated: ${me.name} — ${me.organization.name}`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in Apollo dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.apollo.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ApolloClient } from '@apollo/sdk';

const client = new ApolloClient({

  apiKey: process.env.APOLLO_API_KEY,

});
```

### Python Setup
```python
from apollo import ApolloClient

client = ApolloClient(

    api_key=os.environ.get('APOLLO_API_KEY')

)
```

## Resources
- [Apollo Documentation](https://docs.apollo.com)
- [Apollo Dashboard](https://api.apollo.com)
- [Apollo Status](https://status.apollo.com)

## Next Steps
After successful auth, proceed to `apollo-hello-world` for your first API call.