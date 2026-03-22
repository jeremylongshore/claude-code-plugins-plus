---
name: openevidence-install-auth
description: |
  Install and configure OpenEvidence SDK/CLI authentication.
  Use when setting up a new OpenEvidence integration, configuring API keys,
  or initializing OpenEvidence in your project.
  Trigger with phrases like "install openevidence", "setup openevidence",
  "openevidence auth", "configure openevidence API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openevidence]
---

# OpenEvidence Install & Auth

## Overview
Set up OpenEvidence SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- OpenEvidence account with API access
- API key from OpenEvidence dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @openevidence/sdk

# Python
pip install openevidence
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export OPENEVIDENCE_API_KEY="your-api-key"

# Or create .env file
echo 'OPENEVIDENCE_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in OpenEvidence dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.openevidence.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { OpenEvidenceClient } from '@openevidence/sdk';

const client = new OpenEvidenceClient({
  apiKey: process.env.OPENEVIDENCE_API_KEY,
});
```

### Python Setup
```python
from openevidence import OpenEvidenceClient

client = OpenEvidenceClient(
    api_key=os.environ.get('OPENEVIDENCE_API_KEY')
)
```

## Resources
- [OpenEvidence Documentation](https://docs.openevidence.com)
- [OpenEvidence Dashboard](https://api.openevidence.com)
- [OpenEvidence Status](https://status.openevidence.com)

## Next Steps
After successful auth, proceed to `openevidence-hello-world` for your first API call.