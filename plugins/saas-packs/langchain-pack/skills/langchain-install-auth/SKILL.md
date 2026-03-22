---
name: langchain-install-auth
description: |
  Install and configure LangChain SDK/CLI authentication.
  Use when setting up a new LangChain integration, configuring API keys,
  or initializing LangChain in your project.
  Trigger with phrases like "install langchain", "setup langchain",
  "langchain auth", "configure langchain API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, langchain]
---

# LangChain Install & Auth

## Overview
Set up LangChain SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- LangChain account with API access

- API key from LangChain dashboard (starts with `sk-` or similar prefix)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @langchain/sdk

# Python
pip install langchain
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export LANGCHAIN_API_KEY="your-api-key"

# Or create .env file
echo 'LANGCHAIN_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Key is missing, expired, or has extra whitespace | Verify key in LangChain dashboard. Check for trailing newlines |
| Rate Limited | Exceeded requests/tokens per minute | Check usage at https://docs.langchain.com/usage |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { LangChainClient } from '@langchain/sdk';

const client = new LangChainClient({

  apiKey: process.env.LANGCHAIN_API_KEY,

});
```

### Python Setup
```python
from langchain import LangChainClient

client = LangChainClient(

    api_key=os.environ.get('LANGCHAIN_API_KEY')

)
```

## Resources
- [LangChain Documentation](https://docs.langchain.com)
- [LangChain Dashboard](https://api.langchain.com)
- [LangChain Status](https://status.langchain.com)

## Next Steps
After successful auth, proceed to `langchain-hello-world` for your first API call.