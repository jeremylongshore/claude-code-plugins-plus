---
name: ideogram-install-auth
description: |
  Install and configure Ideogram SDK/CLI authentication.
  Use when setting up a new Ideogram integration, configuring API keys,
  or initializing Ideogram in your project.
  Trigger with phrases like "install ideogram", "setup ideogram",
  "ideogram auth", "configure ideogram API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Ideogram Install & Auth

## Overview
Set up Ideogram SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Ideogram account with API access
- API key from Ideogram dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @ideogram/sdk

# Python
pip install ideogram
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export IDEOGRAM_API_KEY="your-api-key"

# Or create .env file
echo 'IDEOGRAM_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Ideogram dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.ideogram.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { IdeogramClient } from '@ideogram/sdk';

const client = new IdeogramClient({
  apiKey: process.env.IDEOGRAM_API_KEY,
});
```

### Python Setup
```python
from ideogram import IdeogramClient

client = IdeogramClient(
    api_key=os.environ.get('IDEOGRAM_API_KEY')
)
```

## Resources
- [Ideogram Documentation](https://docs.ideogram.com)
- [Ideogram Dashboard](https://api.ideogram.com)
- [Ideogram Status](https://status.ideogram.com)

## Next Steps
After successful auth, proceed to `ideogram-hello-world` for your first API call.