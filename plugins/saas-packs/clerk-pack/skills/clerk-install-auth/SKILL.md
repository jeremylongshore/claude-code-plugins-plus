---
name: clerk-install-auth
description: |
  Install and configure Clerk SDK/CLI authentication.
  Use when setting up a new Clerk integration, configuring API keys,
  or initializing Clerk in your project.
  Trigger with phrases like "install clerk", "setup clerk",
  "clerk auth", "configure clerk API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clerk]
---

# Clerk Install & Auth

## Overview
Set up Clerk SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Clerk account with API access

- API key from Clerk dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @clerk/sdk

# Python
pip install clerk
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export CLERK_API_KEY="your-api-key"

# Or create .env file
echo 'CLERK_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const user = await client.user.get();
console.log(`Authenticated as ${user.name} (${user.email})`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in Clerk dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.clerk.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ClerkClient } from '@clerk/sdk';

const client = new ClerkClient({

  apiKey: process.env.CLERK_API_KEY,

});
```

### Python Setup
```python
from clerk import ClerkClient

client = ClerkClient(

    api_key=os.environ.get('CLERK_API_KEY')

)
```

## Resources
- [Clerk Documentation](https://docs.clerk.com)
- [Clerk Dashboard](https://api.clerk.com)
- [Clerk Status](https://status.clerk.com)

## Next Steps
After successful auth, proceed to `clerk-hello-world` for your first API call.