---
name: oraclecloud-install-auth
description: |
  Install and configure Oracle Cloud SDK/CLI authentication.
  Use when setting up a new Oracle Cloud integration, configuring API keys,
  or initializing Oracle Cloud in your project.
  Trigger with phrases like "install oraclecloud", "setup oraclecloud",
  "oraclecloud auth", "configure oraclecloud API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, oraclecloud]
---

# Oracle Cloud Install & Auth

## Overview
Set up Oracle Cloud SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Oracle Cloud account with API access
- API key from Oracle Cloud dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @oraclecloud/sdk

# Python
pip install oraclecloud
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export ORACLECLOUD_API_KEY="your-api-key"

# Or create .env file
echo 'ORACLECLOUD_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Oracle Cloud dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.oraclecloud.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { OracleCloudClient } from '@oraclecloud/sdk';

const client = new OracleCloudClient({
  apiKey: process.env.ORACLECLOUD_API_KEY,
});
```

### Python Setup
```python
from oraclecloud import OracleCloudClient

client = OracleCloudClient(
    api_key=os.environ.get('ORACLECLOUD_API_KEY')
)
```

## Resources
- [Oracle Cloud Documentation](https://docs.oraclecloud.com)
- [Oracle Cloud Dashboard](https://api.oraclecloud.com)
- [Oracle Cloud Status](https://status.oraclecloud.com)

## Next Steps
After successful auth, proceed to `oraclecloud-hello-world` for your first API call.