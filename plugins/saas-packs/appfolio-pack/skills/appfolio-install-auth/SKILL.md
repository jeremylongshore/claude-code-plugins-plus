---
name: appfolio-install-auth
description: |
  Install and configure AppFolio SDK/CLI authentication.
  Use when setting up a new AppFolio integration, configuring API keys,
  or initializing AppFolio in your project.
  Trigger with phrases like "install appfolio", "setup appfolio",
  "appfolio auth", "configure appfolio API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, appfolio]
---

# AppFolio Install & Auth

## Overview
Set up AppFolio SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- AppFolio account with API access
- API key from AppFolio dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @appfolio/sdk

# Python
pip install appfolio
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export APPFOLIO_API_KEY="your-api-key"

# Or create .env file
echo 'APPFOLIO_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in AppFolio dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.appfolio.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AppFolioClient } from '@appfolio/sdk';

const client = new AppFolioClient({
  apiKey: process.env.APPFOLIO_API_KEY,
});
```

### Python Setup
```python
from appfolio import AppFolioClient

client = AppFolioClient(
    api_key=os.environ.get('APPFOLIO_API_KEY')
)
```

## Resources
- [AppFolio Documentation](https://docs.appfolio.com)
- [AppFolio Dashboard](https://api.appfolio.com)
- [AppFolio Status](https://status.appfolio.com)

## Next Steps
After successful auth, proceed to `appfolio-hello-world` for your first API call.