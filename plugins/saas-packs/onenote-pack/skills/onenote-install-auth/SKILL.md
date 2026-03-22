---
name: onenote-install-auth
description: |
  Install and configure OneNote SDK/CLI authentication.
  Use when setting up a new OneNote integration, configuring API keys,
  or initializing OneNote in your project.
  Trigger with phrases like "install onenote", "setup onenote",
  "onenote auth", "configure onenote API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, onenote]
---

# OneNote Install & Auth

## Overview
Set up OneNote SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- OneNote account with API access
- API key from OneNote dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @onenote/sdk

# Python
pip install onenote
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export ONENOTE_API_KEY="your-api-key"

# Or create .env file
echo 'ONENOTE_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection
```typescript
// Test connection code here
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in OneNote dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.onenote.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { OneNoteClient } from '@onenote/sdk';

const client = new OneNoteClient({
  apiKey: process.env.ONENOTE_API_KEY,
});
```

### Python Setup
```python
from onenote import OneNoteClient

client = OneNoteClient(
    api_key=os.environ.get('ONENOTE_API_KEY')
)
```

## Resources
- [OneNote Documentation](https://docs.onenote.com)
- [OneNote Dashboard](https://api.onenote.com)
- [OneNote Status](https://status.onenote.com)

## Next Steps
After successful auth, proceed to `onenote-hello-world` for your first API call.