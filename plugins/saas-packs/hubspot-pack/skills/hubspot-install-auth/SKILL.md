---
name: hubspot-install-auth
description: |
  Install and configure HubSpot SDK/CLI authentication.
  Use when setting up a new HubSpot integration, configuring API keys,
  or initializing HubSpot in your project.
  Trigger with phrases like "install hubspot", "setup hubspot",
  "hubspot auth", "configure hubspot API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hubspot]
---

# HubSpot Install & Auth

## Overview
Set up HubSpot SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- HubSpot account with API access

- OAuth2 access token or personal API token from HubSpot settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @hubspot/sdk

# Python
pip install hubspot
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export HUBSPOT_API_KEY="your-api-key"

# Or create .env file
echo 'HUBSPOT_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in HubSpot dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.hubspot.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { HubSpotClient } from '@hubspot/sdk';

const client = new HubSpotClient({

  apiKey: process.env.HUBSPOT_API_KEY,

});
```

### Python Setup
```python
from hubspot import HubSpotClient

client = HubSpotClient(

    api_key=os.environ.get('HUBSPOT_API_KEY')

)
```

## Resources
- [HubSpot Documentation](https://docs.hubspot.com)
- [HubSpot Dashboard](https://api.hubspot.com)
- [HubSpot Status](https://status.hubspot.com)

## Next Steps
After successful auth, proceed to `hubspot-hello-world` for your first API call.