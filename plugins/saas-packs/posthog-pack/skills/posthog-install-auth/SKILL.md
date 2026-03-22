---
name: posthog-install-auth
description: |
  Install and configure PostHog SDK/CLI authentication.
  Use when setting up a new PostHog integration, configuring API keys,
  or initializing PostHog in your project.
  Trigger with phrases like "install posthog", "setup posthog",
  "posthog auth", "configure posthog API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, posthog]
---

# PostHog Install & Auth

## Overview
Set up PostHog SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- PostHog account with API access

- Database connection string or API key from PostHog dashboard
- Network access to database host (check firewall/VPC rules)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @posthog/sdk

# Python
pip install posthog
```

### Step 2: Configure Authentication

```bash
# Set connection string (preferred for database platforms)
export POSTHOG_DATABASE_URL="postgresql://user:pass@host:5432/db"

# Or use API key
export POSTHOG_API_KEY="your-api-key"

# Or create .env file
cat >> .env << 'EOF'
POSTHOG_DATABASE_URL=postgresql://user:pass@host:5432/db
POSTHOG_API_KEY=your-api-key
EOF
```


### Step 3: Verify Connection
```typescript
const tables = await client.query("SELECT table_name FROM information_schema.tables LIMIT 5");
console.log(`Connected — ${tables.rows.length} tables found`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Connection string or API key configured in environment
- Successful query execution confirming database connectivity


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Connection Refused | Wrong host/port or firewall blocking | Check connection string, verify network access |
| Authentication Failed | Wrong password or expired credentials | Reset credentials in PostHog dashboard |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { PostHogClient } from '@posthog/sdk';

const client = new PostHogClient({

  connectionString: process.env.POSTHOG_DATABASE_URL,

});
```

### Python Setup
```python
from posthog import PostHogClient

client = PostHogClient(

    connection_string=os.environ.get('POSTHOG_DATABASE_URL')

)
```

## Resources
- [PostHog Documentation](https://docs.posthog.com)
- [PostHog Dashboard](https://api.posthog.com)
- [PostHog Status](https://status.posthog.com)

## Next Steps
After successful auth, proceed to `posthog-hello-world` for your first API call.