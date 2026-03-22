---
name: techsmith-install-auth
description: |
  Install and configure TechSmith SDK/CLI authentication.
  Use when setting up a new TechSmith integration, configuring API keys,
  or initializing TechSmith in your project.
  Trigger with phrases like "install techsmith", "setup techsmith",
  "techsmith auth", "configure techsmith API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, techsmith]
---

# TechSmith Install & Auth

## Overview
Set up TechSmith SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- TechSmith account with API access
- API key from TechSmith dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @techsmith/sdk

# Python
pip install techsmith
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export TECHSMITH_API_KEY="your-api-key"

# Or create .env file
echo 'TECHSMITH_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in TechSmith dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.techsmith.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { TechSmithClient } from '@techsmith/sdk';

const client = new TechSmithClient({
  apiKey: process.env.TECHSMITH_API_KEY,
});
```

### Python Setup
```python
from techsmith import TechSmithClient

client = TechSmithClient(
    api_key=os.environ.get('TECHSMITH_API_KEY')
)
```

## Resources
- [TechSmith Documentation](https://docs.techsmith.com)
- [TechSmith Dashboard](https://api.techsmith.com)
- [TechSmith Status](https://status.techsmith.com)

## Next Steps
After successful auth, proceed to `techsmith-hello-world` for your first API call.