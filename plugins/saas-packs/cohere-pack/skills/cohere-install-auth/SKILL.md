---
name: cohere-install-auth
description: |
  Install and configure Cohere SDK/CLI authentication.
  Use when setting up a new Cohere integration, configuring API keys,
  or initializing Cohere in your project.
  Trigger with phrases like "install cohere", "setup cohere",
  "cohere auth", "configure cohere API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cohere]
---

# Cohere Install & Auth

## Overview
Set up Cohere SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Cohere account with API access

- API key from Cohere dashboard (starts with `sk-` or similar prefix)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @cohere/sdk

# Python
pip install cohere
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export COHERE_API_KEY="your-api-key"

# Or create .env file
echo 'COHERE_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Key is missing, expired, or has extra whitespace | Verify key in Cohere dashboard. Check for trailing newlines |
| Rate Limited | Exceeded requests/tokens per minute | Check usage at https://docs.cohere.com/usage |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { CohereClient } from '@cohere/sdk';

const client = new CohereClient({

  apiKey: process.env.COHERE_API_KEY,

});
```

### Python Setup
```python
from cohere import CohereClient

client = CohereClient(

    api_key=os.environ.get('COHERE_API_KEY')

)
```

## Resources
- [Cohere Documentation](https://docs.cohere.com)
- [Cohere Dashboard](https://api.cohere.com)
- [Cohere Status](https://status.cohere.com)

## Next Steps
After successful auth, proceed to `cohere-hello-world` for your first API call.