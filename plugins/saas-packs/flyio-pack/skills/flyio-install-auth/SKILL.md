---
name: flyio-install-auth
description: |
  Install and configure Fly.io SDK/CLI authentication.
  Use when setting up a new Fly.io integration, configuring API keys,
  or initializing Fly.io in your project.
  Trigger with phrases like "install flyio", "setup flyio",
  "flyio auth", "configure flyio API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flyio]
---

# Fly.io Install & Auth

## Overview
Set up Fly.io SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Fly.io account with API access

- API key from Fly.io dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @flyio/sdk

# Python
pip install flyio
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export FLYIO_API_KEY="your-api-key"

# Or create .env file
echo 'FLYIO_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const user = await client.user.get();
console.log(`Authenticated as ${user.name} (${user.email})`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in Fly.io dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.flyio.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { Fly.ioClient } from '@flyio/sdk';

const client = new Fly.ioClient({

  apiKey: process.env.FLYIO_API_KEY,

});
```

### Python Setup
```python
from flyio import Fly.ioClient

client = Fly.ioClient(

    api_key=os.environ.get('FLYIO_API_KEY')

)
```

## Resources
- [Fly.io Documentation](https://docs.flyio.com)
- [Fly.io Dashboard](https://api.flyio.com)
- [Fly.io Status](https://status.flyio.com)

## Next Steps
After successful auth, proceed to `flyio-hello-world` for your first API call.