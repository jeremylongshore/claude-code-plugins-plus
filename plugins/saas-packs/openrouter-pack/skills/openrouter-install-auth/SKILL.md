---
name: openrouter-install-auth
description: |
  Install and configure OpenRouter SDK/CLI authentication.
  Use when setting up a new OpenRouter integration, configuring API keys,
  or initializing OpenRouter in your project.
  Trigger with phrases like "install openrouter", "setup openrouter",
  "openrouter auth", "configure openrouter API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openrouter]
---

# OpenRouter Install & Auth

## Overview
Set up OpenRouter SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- OpenRouter account with API access

- API key from OpenRouter dashboard (starts with `sk-` or similar prefix)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @openrouter/sdk

# Python
pip install openrouter
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export OPENROUTER_API_KEY="your-api-key"

# Or create .env file
echo 'OPENROUTER_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Key is missing, expired, or has extra whitespace | Verify key in OpenRouter dashboard. Check for trailing newlines |
| Rate Limited | Exceeded requests/tokens per minute | Check usage at https://docs.openrouter.com/usage |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { OpenRouterClient } from '@openrouter/sdk';

const client = new OpenRouterClient({

  apiKey: process.env.OPENROUTER_API_KEY,

});
```

### Python Setup
```python
from openrouter import OpenRouterClient

client = OpenRouterClient(

    api_key=os.environ.get('OPENROUTER_API_KEY')

)
```

## Resources
- [OpenRouter Documentation](https://docs.openrouter.com)
- [OpenRouter Dashboard](https://api.openrouter.com)
- [OpenRouter Status](https://status.openrouter.com)

## Next Steps
After successful auth, proceed to `openrouter-hello-world` for your first API call.