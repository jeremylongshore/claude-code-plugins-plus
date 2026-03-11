---
name: coderabbit-install-auth
description: |
  Install and configure CodeRabbit SDK/CLI authentication.
  Use when setting up a new CodeRabbit integration, configuring API keys,
  or initializing CodeRabbit in your project.
  Trigger with phrases like "install coderabbit", "setup coderabbit",
  "coderabbit auth", "configure coderabbit API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit Install & Auth

## Overview
Set up CodeRabbit SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- CodeRabbit account with API access
- API key from CodeRabbit dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @coderabbit/sdk

# Python
pip install coderabbit
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export CODERABBIT_API_KEY="your-api-key"

# Or create .env file
echo 'CODERABBIT_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in CodeRabbit dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.coderabbit.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { CodeRabbitClient } from '@coderabbit/sdk';

const client = new CodeRabbitClient({
  apiKey: process.env.CODERABBIT_API_KEY,
});
```

### Python Setup
```python
from coderabbit import CodeRabbitClient

client = CodeRabbitClient(
    api_key=os.environ.get('CODERABBIT_API_KEY')
)
```

## Resources
- [CodeRabbit Documentation](https://docs.coderabbit.com)
- [CodeRabbit Dashboard](https://api.coderabbit.com)
- [CodeRabbit Status](https://status.coderabbit.com)

## Next Steps
After successful auth, proceed to `coderabbit-hello-world` for your first API call.