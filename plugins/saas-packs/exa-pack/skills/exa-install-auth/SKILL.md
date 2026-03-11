---
name: exa-install-auth
description: |
  Install and configure Exa SDK/CLI authentication.
  Use when setting up a new Exa integration, configuring API keys,
  or initializing Exa in your project.
  Trigger with phrases like "install exa", "setup exa",
  "exa auth", "configure exa API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Exa Install & Auth

## Overview
Set up Exa SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Exa account with API access
- API key from Exa dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @exa/sdk

# Python
pip install exa
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export EXA_API_KEY="your-api-key"

# Or create .env file
echo 'EXA_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Exa dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.exa.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ExaClient } from '@exa/sdk';

const client = new ExaClient({
  apiKey: process.env.EXA_API_KEY,
});
```

### Python Setup
```python
from exa import ExaClient

client = ExaClient(
    api_key=os.environ.get('EXA_API_KEY')
)
```

## Resources
- [Exa Documentation](https://docs.exa.com)
- [Exa Dashboard](https://api.exa.com)
- [Exa Status](https://status.exa.com)

## Next Steps
After successful auth, proceed to `exa-hello-world` for your first API call.