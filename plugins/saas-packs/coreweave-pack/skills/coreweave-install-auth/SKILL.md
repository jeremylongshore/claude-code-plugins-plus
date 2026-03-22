---
name: coreweave-install-auth
description: |
  Install and configure CoreWeave SDK/CLI authentication.
  Use when setting up a new CoreWeave integration, configuring API keys,
  or initializing CoreWeave in your project.
  Trigger with phrases like "install coreweave", "setup coreweave",
  "coreweave auth", "configure coreweave API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, coreweave]
---

# CoreWeave Install & Auth

## Overview
Set up CoreWeave SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- CoreWeave account with API access

- API key from CoreWeave dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @coreweave/sdk

# Python
pip install coreweave
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export COREWEAVE_API_KEY="your-api-key"

# Or create .env file
echo 'COREWEAVE_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const org = await client.organization.get();
console.log(`Connected: ${org.name} — ${org.projects.length} projects`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in CoreWeave dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.coreweave.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { CoreWeaveClient } from '@coreweave/sdk';

const client = new CoreWeaveClient({

  apiKey: process.env.COREWEAVE_API_KEY,

});
```

### Python Setup
```python
from coreweave import CoreWeaveClient

client = CoreWeaveClient(

    api_key=os.environ.get('COREWEAVE_API_KEY')

)
```

## Resources
- [CoreWeave Documentation](https://docs.coreweave.com)
- [CoreWeave Dashboard](https://api.coreweave.com)
- [CoreWeave Status](https://status.coreweave.com)

## Next Steps
After successful auth, proceed to `coreweave-hello-world` for your first API call.