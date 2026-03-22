---
name: documenso-install-auth
description: |
  Install and configure Documenso SDK/CLI authentication.
  Use when setting up a new Documenso integration, configuring API keys,
  or initializing Documenso in your project.
  Trigger with phrases like "install documenso", "setup documenso",
  "documenso auth", "configure documenso API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, documenso]
---

# Documenso Install & Auth

## Overview
Set up Documenso SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Documenso account with API access
- API key from Documenso dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @documenso/sdk

# Python
pip install documenso
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export DOCUMENSO_API_KEY="your-api-key"

# Or create .env file
echo 'DOCUMENSO_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Documenso dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.documenso.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { DocumensoClient } from '@documenso/sdk';

const client = new DocumensoClient({
  apiKey: process.env.DOCUMENSO_API_KEY,
});
```

### Python Setup
```python
from documenso import DocumensoClient

client = DocumensoClient(
    api_key=os.environ.get('DOCUMENSO_API_KEY')
)
```

## Resources
- [Documenso Documentation](https://docs.documenso.com)
- [Documenso Dashboard](https://api.documenso.com)
- [Documenso Status](https://status.documenso.com)

## Next Steps
After successful auth, proceed to `documenso-hello-world` for your first API call.