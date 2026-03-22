---
name: salesforce-install-auth
description: |
  Install and configure Salesforce SDK/CLI authentication.
  Use when setting up a new Salesforce integration, configuring API keys,
  or initializing Salesforce in your project.
  Trigger with phrases like "install salesforce", "setup salesforce",
  "salesforce auth", "configure salesforce API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesforce]
---

# Salesforce Install & Auth

## Overview
Set up Salesforce SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Salesforce account with API access

- OAuth2 access token or personal API token from Salesforce settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @salesforce/sdk

# Python
pip install salesforce
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export SALESFORCE_API_KEY="your-api-key"

# Or create .env file
echo 'SALESFORCE_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in Salesforce dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.salesforce.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { SalesforceClient } from '@salesforce/sdk';

const client = new SalesforceClient({

  apiKey: process.env.SALESFORCE_API_KEY,

});
```

### Python Setup
```python
from salesforce import SalesforceClient

client = SalesforceClient(

    api_key=os.environ.get('SALESFORCE_API_KEY')

)
```

## Resources
- [Salesforce Documentation](https://docs.salesforce.com)
- [Salesforce Dashboard](https://api.salesforce.com)
- [Salesforce Status](https://status.salesforce.com)

## Next Steps
After successful auth, proceed to `salesforce-hello-world` for your first API call.