---
name: cursor-install-auth
description: |
  Install and configure Cursor SDK/CLI authentication.
  Use when setting up a new Cursor integration, configuring API keys,
  or initializing Cursor in your project.
  Trigger with phrases like "install cursor", "setup cursor",
  "cursor auth", "configure cursor API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cursor]
---

# Cursor Install & Auth

## Overview
Set up Cursor SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Cursor account with API access

- API key from Cursor dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @cursor/sdk

# Python
pip install cursor
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export CURSOR_API_KEY="your-api-key"

# Or create .env file
echo 'CURSOR_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in Cursor dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.cursor.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { CursorClient } from '@cursor/sdk';

const client = new CursorClient({

  apiKey: process.env.CURSOR_API_KEY,

});
```

### Python Setup
```python
from cursor import CursorClient

client = CursorClient(

    api_key=os.environ.get('CURSOR_API_KEY')

)
```

## Resources
- [Cursor Documentation](https://docs.cursor.com)
- [Cursor Dashboard](https://api.cursor.com)
- [Cursor Status](https://status.cursor.com)

## Next Steps
After successful auth, proceed to `cursor-hello-world` for your first API call.