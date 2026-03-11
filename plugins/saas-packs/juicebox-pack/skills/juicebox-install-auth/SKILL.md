---
name: juicebox-install-auth
description: |
  Install and configure Juicebox SDK/CLI authentication.
  Use when setting up a new Juicebox integration, configuring API keys,
  or initializing Juicebox in your project.
  Trigger with phrases like "install juicebox", "setup juicebox",
  "juicebox auth", "configure juicebox API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Install & Auth

## Overview
Set up Juicebox SDK and configure authentication credentials for the AI-powered people search platform.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Juicebox account with API access
- API key from Juicebox dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @juicebox/sdk

# Python
pip install juicebox-sdk
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export JUICEBOX_API_KEY="your-api-key"

# Or create .env file
echo 'JUICEBOX_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection
```typescript
import { JuiceboxClient } from '@juicebox/sdk';

const client = new JuiceboxClient({
  apiKey: process.env.JUICEBOX_API_KEY
});

const result = await client.search.test();
console.log(result.success ? 'OK' : 'Failed');
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Juicebox dashboard |
| Rate Limited | Exceeded quota | Check quota at https://juicebox.ai/docs |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { JuiceboxClient } from '@juicebox/sdk';

const client = new JuiceboxClient({
  apiKey: process.env.JUICEBOX_API_KEY,
  timeout: 30000  # 30000: 30 seconds in ms
});
```

### Python Setup
```python
from juicebox import JuiceboxClient
import os

client = JuiceboxClient(
    api_key=os.environ.get('JUICEBOX_API_KEY')
)
```

## Resources
- [Juicebox Documentation](https://juicebox.ai/docs)
- [Juicebox Dashboard](https://app.juicebox.ai)
- [API Reference](https://juicebox.ai/docs/api)

## Next Steps
After successful auth, proceed to `juicebox-hello-world` for your first people search.