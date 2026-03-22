---
name: oraclecloud-install-auth
description: |
  Install and configure Oracle Cloud SDK/CLI authentication.
  Use when setting up a new Oracle Cloud integration, configuring API keys,
  or initializing Oracle Cloud in your project.
  Trigger with phrases like "install oraclecloud", "setup oraclecloud",
  "oraclecloud auth", "configure oraclecloud API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, oraclecloud]
---

# Oracle Cloud Install & Auth

## Overview
Set up Oracle Cloud SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Oracle Cloud account with API access

- Database connection string or API key from Oracle Cloud dashboard
- Network access to database host (check firewall/VPC rules)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @oraclecloud/sdk

# Python
pip install oraclecloud
```

### Step 2: Configure Authentication

```bash
# Set connection string (preferred for database platforms)
export ORACLECLOUD_DATABASE_URL="postgresql://user:pass@host:5432/db"

# Or use API key
export ORACLECLOUD_API_KEY="your-api-key"

# Or create .env file
cat >> .env << 'EOF'
ORACLECLOUD_DATABASE_URL=postgresql://user:pass@host:5432/db
ORACLECLOUD_API_KEY=your-api-key
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
| Authentication Failed | Wrong password or expired credentials | Reset credentials in Oracle Cloud dashboard |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { OracleCloudClient } from '@oraclecloud/sdk';

const client = new OracleCloudClient({

  connectionString: process.env.ORACLECLOUD_DATABASE_URL,

});
```

### Python Setup
```python
from oraclecloud import OracleCloudClient

client = OracleCloudClient(

    connection_string=os.environ.get('ORACLECLOUD_DATABASE_URL')

)
```

## Resources
- [Oracle Cloud Documentation](https://docs.oraclecloud.com)
- [Oracle Cloud Dashboard](https://api.oraclecloud.com)
- [Oracle Cloud Status](https://status.oraclecloud.com)

## Next Steps
After successful auth, proceed to `oraclecloud-hello-world` for your first API call.