---
name: webflow-install-auth
description: |
  Install and configure Webflow SDK/CLI authentication.
  Use when setting up a new Webflow integration, configuring API keys,
  or initializing Webflow in your project.
  Trigger with phrases like "install webflow", "setup webflow",
  "webflow auth", "configure webflow API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, webflow]
---

# Webflow Install & Auth

## Overview
Set up Webflow SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Webflow account with API access
- API key from Webflow dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @webflow/sdk

# Python
pip install webflow
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export WEBFLOW_API_KEY="your-api-key"

# Or create .env file
echo 'WEBFLOW_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Webflow dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.webflow.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { WebflowClient } from '@webflow/sdk';

const client = new WebflowClient({
  apiKey: process.env.WEBFLOW_API_KEY,
});
```

### Python Setup
```python
from webflow import WebflowClient

client = WebflowClient(
    api_key=os.environ.get('WEBFLOW_API_KEY')
)
```

## Resources
- [Webflow Documentation](https://docs.webflow.com)
- [Webflow Dashboard](https://api.webflow.com)
- [Webflow Status](https://status.webflow.com)

## Next Steps
After successful auth, proceed to `webflow-hello-world` for your first API call.