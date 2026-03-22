---
name: brightdata-install-auth
description: |
  Install and configure Bright Data SDK/CLI authentication.
  Use when setting up a new Bright Data integration, configuring API keys,
  or initializing Bright Data in your project.
  Trigger with phrases like "install brightdata", "setup brightdata",
  "brightdata auth", "configure brightdata API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, brightdata]
---

# Bright Data Install & Auth

## Overview
Set up Bright Data SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Bright Data account with API access

- API key from Bright Data dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @brightdata/sdk

# Python
pip install brightdata
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export BRIGHTDATA_API_KEY="your-api-key"

# Or create .env file
echo 'BRIGHTDATA_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in Bright Data dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.brightdata.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { BrightDataClient } from '@brightdata/sdk';

const client = new BrightDataClient({

  apiKey: process.env.BRIGHTDATA_API_KEY,

});
```

### Python Setup
```python
from brightdata import BrightDataClient

client = BrightDataClient(

    api_key=os.environ.get('BRIGHTDATA_API_KEY')

)
```

## Resources
- [Bright Data Documentation](https://docs.brightdata.com)
- [Bright Data Dashboard](https://api.brightdata.com)
- [Bright Data Status](https://status.brightdata.com)

## Next Steps
After successful auth, proceed to `brightdata-hello-world` for your first API call.