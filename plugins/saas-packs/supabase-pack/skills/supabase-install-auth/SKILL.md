---
name: supabase-install-auth
description: |
  Install and configure Supabase SDK/CLI authentication.
  Use when setting up a new Supabase integration, configuring API keys,
  or initializing Supabase in your project.
  Trigger with phrases like "install supabase", "setup supabase",
  "supabase auth", "configure supabase API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, supabase]
---

# Supabase Install & Auth

## Overview
Set up Supabase SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Supabase account with API access

- Database connection string or API key from Supabase dashboard
- Network access to database host (check firewall/VPC rules)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @supabase/supabase-js

# Python
pip install supabase
```

### Step 2: Configure Authentication

```bash
# Set connection string (preferred for database platforms)
export SUPABASE_DATABASE_URL="postgresql://user:pass@host:5432/db"

# Or use API key
export SUPABASE_API_KEY="your-api-key"

# Or create .env file
cat >> .env << 'EOF'
SUPABASE_DATABASE_URL=postgresql://user:pass@host:5432/db
SUPABASE_API_KEY=your-api-key
EOF
```


### Step 3: Verify Connection
```typescript
const result = await supabase.from('_test').select('*').limit(1); console.log(result.error ? 'Failed' : 'OK');
```

## Output
- Installed SDK package in node_modules or site-packages

- Connection string or API key configured in environment
- Successful query execution confirming database connectivity


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Connection Refused | Wrong host/port or firewall blocking | Check connection string, verify network access |
| Authentication Failed | Wrong password or expired credentials | Reset credentials in Supabase dashboard |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { SupabaseClient } from '@supabase/supabase-js';

const client = new SupabaseClient({

  connectionString: process.env.SUPABASE_DATABASE_URL,

});
```

### Python Setup
```python
from supabase import SupabaseClient

client = SupabaseClient(

    connection_string=os.environ.get('SUPABASE_DATABASE_URL')

)
```

## Resources
- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Dashboard](https://api.supabase.com)
- [Supabase Status](https://status.supabase.com)

## Next Steps
After successful auth, proceed to `supabase-hello-world` for your first API call.