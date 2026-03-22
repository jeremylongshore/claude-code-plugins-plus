---
name: sentry-install-auth
description: |
  Install and configure Sentry SDK/CLI authentication.
  Use when setting up a new Sentry integration, configuring API keys,
  or initializing Sentry in your project.
  Trigger with phrases like "install sentry", "setup sentry",
  "sentry auth", "configure sentry API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, sentry]
---

# Sentry Install & Auth

## Overview
Set up Sentry SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Sentry account with API access

- API key from Sentry dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @sentry/sdk

# Python
pip install sentry
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export SENTRY_API_KEY="your-api-key"

# Or create .env file
echo 'SENTRY_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in Sentry dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.sentry.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { SentryClient } from '@sentry/sdk';

const client = new SentryClient({

  apiKey: process.env.SENTRY_API_KEY,

});
```

### Python Setup
```python
from sentry import SentryClient

client = SentryClient(

    api_key=os.environ.get('SENTRY_API_KEY')

)
```

## Resources
- [Sentry Documentation](https://docs.sentry.com)
- [Sentry Dashboard](https://api.sentry.com)
- [Sentry Status](https://status.sentry.com)

## Next Steps
After successful auth, proceed to `sentry-hello-world` for your first API call.