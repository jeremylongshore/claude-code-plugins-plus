---
name: adobe-install-auth
description: |
  Install and configure Adobe SDK/CLI authentication.
  Use when setting up a new Adobe integration, configuring API keys,
  or initializing Adobe in your project.
  Trigger with phrases like "install adobe", "setup adobe",
  "adobe auth", "configure adobe API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, adobe]
---

# Adobe Install & Auth

## Overview
Set up Adobe SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Adobe account with API access
- API key from Adobe dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @adobe/sdk

# Python
pip install adobe
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export ADOBE_API_KEY="your-api-key"

# Or create .env file
echo 'ADOBE_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Adobe dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.adobe.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AdobeClient } from '@adobe/sdk';

const client = new AdobeClient({
  apiKey: process.env.ADOBE_API_KEY,
});
```

### Python Setup
```python
from adobe import AdobeClient

client = AdobeClient(
    api_key=os.environ.get('ADOBE_API_KEY')
)
```

## Resources
- [Adobe Documentation](https://docs.adobe.com)
- [Adobe Dashboard](https://api.adobe.com)
- [Adobe Status](https://status.adobe.com)

## Next Steps
After successful auth, proceed to `adobe-hello-world` for your first API call.