---
name: mindtickle-install-auth
description: |
  Install and configure Mindtickle SDK/CLI authentication.
  Use when setting up a new Mindtickle integration, configuring API keys,
  or initializing Mindtickle in your project.
  Trigger with phrases like "install mindtickle", "setup mindtickle",
  "mindtickle auth", "configure mindtickle API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, mindtickle]
---

# Mindtickle Install & Auth

## Overview
Set up Mindtickle SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Mindtickle account with API access

- OAuth2 access token or personal API token from Mindtickle settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @mindtickle/sdk

# Python
pip install mindtickle
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export MINDTICKLE_API_KEY="your-api-key"

# Or create .env file
echo 'MINDTICKLE_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in Mindtickle dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.mindtickle.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { MindtickleClient } from '@mindtickle/sdk';

const client = new MindtickleClient({

  apiKey: process.env.MINDTICKLE_API_KEY,

});
```

### Python Setup
```python
from mindtickle import MindtickleClient

client = MindtickleClient(

    api_key=os.environ.get('MINDTICKLE_API_KEY')

)
```

## Resources
- [Mindtickle Documentation](https://docs.mindtickle.com)
- [Mindtickle Dashboard](https://api.mindtickle.com)
- [Mindtickle Status](https://status.mindtickle.com)

## Next Steps
After successful auth, proceed to `mindtickle-hello-world` for your first API call.