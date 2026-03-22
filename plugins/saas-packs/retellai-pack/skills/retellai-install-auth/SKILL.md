---
name: retellai-install-auth
description: |
  Install and configure Retell AI SDK/CLI authentication.
  Use when setting up a new Retell AI integration, configuring API keys,
  or initializing Retell AI in your project.
  Trigger with phrases like "install retellai", "setup retellai",
  "retellai auth", "configure retellai API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, retellai]
---

# Retell AI Install & Auth

## Overview
Set up Retell AI SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Retell AI account with API access

- API key from Retell AI dashboard (starts with `sk-` or similar prefix)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @retellai/sdk

# Python
pip install retellai
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export RETELLAI_API_KEY="your-api-key"

# Or create .env file
echo 'RETELLAI_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const models = await client.models.list();
console.log(`Connected — ${models.data.length} models available`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Key is missing, expired, or has extra whitespace | Verify key in Retell AI dashboard. Check for trailing newlines |
| Rate Limited | Exceeded requests/tokens per minute | Check usage at https://docs.retellai.com/usage |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { RetellAIClient } from '@retellai/sdk';

const client = new RetellAIClient({

  apiKey: process.env.RETELLAI_API_KEY,

});
```

### Python Setup
```python
from retellai import RetellAIClient

client = RetellAIClient(

    api_key=os.environ.get('RETELLAI_API_KEY')

)
```

## Resources
- [Retell AI Documentation](https://docs.retellai.com)
- [Retell AI Dashboard](https://api.retellai.com)
- [Retell AI Status](https://status.retellai.com)

## Next Steps
After successful auth, proceed to `retellai-hello-world` for your first API call.