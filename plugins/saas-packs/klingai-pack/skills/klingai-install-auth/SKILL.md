---
name: klingai-install-auth
description: |
  Install and configure Kling AI SDK/CLI authentication.
  Use when setting up a new Kling AI integration, configuring API keys,
  or initializing Kling AI in your project.
  Trigger with phrases like "install klingai", "setup klingai",
  "klingai auth", "configure klingai API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klingai]
---

# Kling AI Install & Auth

## Overview
Set up Kling AI SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Kling AI account with API access

- API key from Kling AI dashboard (starts with `sk-` or similar prefix)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @klingai/sdk

# Python
pip install klingai
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export KLINGAI_API_KEY="your-api-key"

# Or create .env file
echo 'KLINGAI_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Key is missing, expired, or has extra whitespace | Verify key in Kling AI dashboard. Check for trailing newlines |
| Rate Limited | Exceeded requests/tokens per minute | Check usage at https://docs.klingai.com/usage |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { KlingAIClient } from '@klingai/sdk';

const client = new KlingAIClient({

  apiKey: process.env.KLINGAI_API_KEY,

});
```

### Python Setup
```python
from klingai import KlingAIClient

client = KlingAIClient(

    api_key=os.environ.get('KLINGAI_API_KEY')

)
```

## Resources
- [Kling AI Documentation](https://docs.klingai.com)
- [Kling AI Dashboard](https://api.klingai.com)
- [Kling AI Status](https://status.klingai.com)

## Next Steps
After successful auth, proceed to `klingai-hello-world` for your first API call.