---
name: hex-install-auth
description: |
  Install and configure Hex SDK/CLI authentication.
  Use when setting up a new Hex integration, configuring API keys,
  or initializing Hex in your project.
  Trigger with phrases like "install hex", "setup hex",
  "hex auth", "configure hex API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hex]
---

# Hex Install & Auth

## Overview
Set up Hex SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Hex account with API access

- Database connection string or API key from Hex dashboard
- Network access to database host (check firewall/VPC rules)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @hex/sdk

# Python
pip install hex
```

### Step 2: Configure Authentication

```bash
# Set connection string (preferred for database platforms)
export HEX_DATABASE_URL="postgresql://user:pass@host:5432/db"

# Or use API key
export HEX_API_KEY="your-api-key"

# Or create .env file
cat >> .env << 'EOF'
HEX_DATABASE_URL=postgresql://user:pass@host:5432/db
HEX_API_KEY=your-api-key
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
| Authentication Failed | Wrong password or expired credentials | Reset credentials in Hex dashboard |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { HexClient } from '@hex/sdk';

const client = new HexClient({

  connectionString: process.env.HEX_DATABASE_URL,

});
```

### Python Setup
```python
from hex import HexClient

client = HexClient(

    connection_string=os.environ.get('HEX_DATABASE_URL')

)
```

## Resources
- [Hex Documentation](https://docs.hex.com)
- [Hex Dashboard](https://api.hex.com)
- [Hex Status](https://status.hex.com)

## Next Steps
After successful auth, proceed to `hex-hello-world` for your first API call.