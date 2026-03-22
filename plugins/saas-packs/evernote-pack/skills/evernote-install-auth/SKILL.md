---
name: evernote-install-auth
description: |
  Install and configure Evernote SDK/CLI authentication.
  Use when setting up a new Evernote integration, configuring API keys,
  or initializing Evernote in your project.
  Trigger with phrases like "install evernote", "setup evernote",
  "evernote auth", "configure evernote API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, evernote]
---

# Evernote Install & Auth

## Overview
Set up Evernote SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Evernote account with API access

- API key from Evernote dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @evernote/sdk

# Python
pip install evernote
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export EVERNOTE_API_KEY="your-api-key"

# Or create .env file
echo 'EVERNOTE_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const workspace = await client.workspace.get();
console.log(`Connected to workspace: ${workspace.name}`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in Evernote dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.evernote.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { EvernoteClient } from '@evernote/sdk';

const client = new EvernoteClient({

  apiKey: process.env.EVERNOTE_API_KEY,

});
```

### Python Setup
```python
from evernote import EvernoteClient

client = EvernoteClient(

    api_key=os.environ.get('EVERNOTE_API_KEY')

)
```

## Resources
- [Evernote Documentation](https://docs.evernote.com)
- [Evernote Dashboard](https://api.evernote.com)
- [Evernote Status](https://status.evernote.com)

## Next Steps
After successful auth, proceed to `evernote-hello-world` for your first API call.