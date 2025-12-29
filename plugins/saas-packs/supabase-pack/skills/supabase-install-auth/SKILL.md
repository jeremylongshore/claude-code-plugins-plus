---
name: supabase-install-auth
description: |
  Supabase installation and authentication setup. Trigger phrases:
  "install supabase", "setup supabase", "supabase auth",
  "configure supabase API key", "supabase SDK setup".
allowed-tools: Read, Write, Bash, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Install & Auth

## Overview
Set up Supabase SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Supabase account with API access

## Installation Steps

### 1. Install SDK
```bash
# Node.js
npm install @supabase/supabase-js

# Python
pip install supabase
```

### 2. Configure Authentication
```bash
# Set environment variable
export SUPABASE_API_KEY="your-api-key"

# Or create .env file
echo 'SUPABASE_API_KEY=your-api-key' >> .env
```

### 3. Verify Connection
```typescript
const result = await supabase.from('_test').select('*').limit(1); console.log(result.error ? 'Failed' : 'OK');
```

## Common Issues
- **Invalid API Key**: Verify key in Supabase dashboard
- **Rate Limited**: Check quota at https://supabase.com/docs
- **Network Error**: Ensure firewall allows outbound HTTPS

## Next Steps
After successful auth, proceed to `supabase-hello-world` for your first API call.