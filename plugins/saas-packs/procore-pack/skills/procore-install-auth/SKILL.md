---
name: procore-install-auth
description: |
  Install and configure Procore SDK/CLI authentication.
  Use when setting up a new Procore integration, configuring API keys,
  or initializing Procore in your project.
  Trigger with phrases like "install procore", "setup procore",
  "procore auth", "configure procore API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, procore]
---

# Procore Install & Auth

## Overview
Set up Procore SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Procore account with API access
- API key from Procore dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @procore/sdk

# Python
pip install procore
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export PROCORE_API_KEY="your-api-key"

# Or create .env file
echo 'PROCORE_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Procore dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.procore.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ProcoreClient } from '@procore/sdk';

const client = new ProcoreClient({
  apiKey: process.env.PROCORE_API_KEY,
});
```

### Python Setup
```python
from procore import ProcoreClient

client = ProcoreClient(
    api_key=os.environ.get('PROCORE_API_KEY')
)
```

## Resources
- [Procore Documentation](https://docs.procore.com)
- [Procore Dashboard](https://api.procore.com)
- [Procore Status](https://status.procore.com)

## Next Steps
After successful auth, proceed to `procore-hello-world` for your first API call.