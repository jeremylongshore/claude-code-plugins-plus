---
name: workhuman-install-auth
description: |
  Install and configure Workhuman SDK/CLI authentication.
  Use when setting up a new Workhuman integration, configuring API keys,
  or initializing Workhuman in your project.
  Trigger with phrases like "install workhuman", "setup workhuman",
  "workhuman auth", "configure workhuman API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, workhuman]
---

# Workhuman Install & Auth

## Overview
Set up Workhuman SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Workhuman account with API access
- API key from Workhuman dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @workhuman/sdk

# Python
pip install workhuman
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export WORKHUMAN_API_KEY="your-api-key"

# Or create .env file
echo 'WORKHUMAN_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Workhuman dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.workhuman.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { WorkhumanClient } from '@workhuman/sdk';

const client = new WorkhumanClient({
  apiKey: process.env.WORKHUMAN_API_KEY,
});
```

### Python Setup
```python
from workhuman import WorkhumanClient

client = WorkhumanClient(
    api_key=os.environ.get('WORKHUMAN_API_KEY')
)
```

## Resources
- [Workhuman Documentation](https://docs.workhuman.com)
- [Workhuman Dashboard](https://api.workhuman.com)
- [Workhuman Status](https://status.workhuman.com)

## Next Steps
After successful auth, proceed to `workhuman-hello-world` for your first API call.