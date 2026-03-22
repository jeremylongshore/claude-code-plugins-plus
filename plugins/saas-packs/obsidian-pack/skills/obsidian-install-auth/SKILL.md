---
name: obsidian-install-auth
description: |
  Install and configure Obsidian SDK/CLI authentication.
  Use when setting up a new Obsidian integration, configuring API keys,
  or initializing Obsidian in your project.
  Trigger with phrases like "install obsidian", "setup obsidian",
  "obsidian auth", "configure obsidian API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, obsidian]
---

# Obsidian Install & Auth

## Overview
Set up Obsidian SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Obsidian account with API access

- API key from Obsidian dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @obsidian/sdk

# Python
pip install obsidian
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export OBSIDIAN_API_KEY="your-api-key"

# Or create .env file
echo 'OBSIDIAN_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in Obsidian dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.obsidian.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ObsidianClient } from '@obsidian/sdk';

const client = new ObsidianClient({

  apiKey: process.env.OBSIDIAN_API_KEY,

});
```

### Python Setup
```python
from obsidian import ObsidianClient

client = ObsidianClient(

    api_key=os.environ.get('OBSIDIAN_API_KEY')

)
```

## Resources
- [Obsidian Documentation](https://docs.obsidian.com)
- [Obsidian Dashboard](https://api.obsidian.com)
- [Obsidian Status](https://status.obsidian.com)

## Next Steps
After successful auth, proceed to `obsidian-hello-world` for your first API call.