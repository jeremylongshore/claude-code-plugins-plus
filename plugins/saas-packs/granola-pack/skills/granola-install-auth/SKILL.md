---
name: granola-install-auth
description: |
  Install and configure Granola SDK/CLI authentication.
  Use when setting up a new Granola integration, configuring API keys,
  or initializing Granola in your project.
  Trigger with phrases like "install granola", "setup granola",
  "granola auth", "configure granola API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, granola]
---

# Granola Install & Auth

## Overview
Set up Granola SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Granola account with API access

- API key from Granola dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @granola/sdk

# Python
pip install granola
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export GRANOLA_API_KEY="your-api-key"

# Or create .env file
echo 'GRANOLA_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const workspace = await client.workspace.get();
console.log(`Connected to workspace: ${workspace.name}`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in Granola dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.granola.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { GranolaClient } from '@granola/sdk';

const client = new GranolaClient({

  apiKey: process.env.GRANOLA_API_KEY,

});
```

### Python Setup
```python
from granola import GranolaClient

client = GranolaClient(

    api_key=os.environ.get('GRANOLA_API_KEY')

)
```

## Resources
- [Granola Documentation](https://docs.granola.com)
- [Granola Dashboard](https://api.granola.com)
- [Granola Status](https://status.granola.com)

## Next Steps
After successful auth, proceed to `granola-hello-world` for your first API call.