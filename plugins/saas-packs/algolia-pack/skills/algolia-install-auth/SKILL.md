---
name: algolia-install-auth
description: |
  Install and configure Algolia SDK/CLI authentication.
  Use when setting up a new Algolia integration, configuring API keys,
  or initializing Algolia in your project.
  Trigger with phrases like "install algolia", "setup algolia",
  "algolia auth", "configure algolia API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, algolia]
---

# Algolia Install & Auth

## Overview
Set up Algolia SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Algolia account with API access

- Database connection string or API key from Algolia dashboard
- Network access to database host (check firewall/VPC rules)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @algolia/sdk

# Python
pip install algolia
```

### Step 2: Configure Authentication

```bash
# Set connection string (preferred for database platforms)
export ALGOLIA_DATABASE_URL="postgresql://user:pass@host:5432/db"

# Or use API key
export ALGOLIA_API_KEY="your-api-key"

# Or create .env file
cat >> .env << 'EOF'
ALGOLIA_DATABASE_URL=postgresql://user:pass@host:5432/db
ALGOLIA_API_KEY=your-api-key
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
| Authentication Failed | Wrong password or expired credentials | Reset credentials in Algolia dashboard |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AlgoliaClient } from '@algolia/sdk';

const client = new AlgoliaClient({

  connectionString: process.env.ALGOLIA_DATABASE_URL,

});
```

### Python Setup
```python
from algolia import AlgoliaClient

client = AlgoliaClient(

    connection_string=os.environ.get('ALGOLIA_DATABASE_URL')

)
```

## Resources
- [Algolia Documentation](https://docs.algolia.com)
- [Algolia Dashboard](https://api.algolia.com)
- [Algolia Status](https://status.algolia.com)

## Next Steps
After successful auth, proceed to `algolia-hello-world` for your first API call.