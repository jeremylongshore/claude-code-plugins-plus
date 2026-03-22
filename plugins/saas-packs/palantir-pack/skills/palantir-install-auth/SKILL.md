---
name: palantir-install-auth
description: |
  Install and configure Palantir SDK/CLI authentication.
  Use when setting up a new Palantir integration, configuring API keys,
  or initializing Palantir in your project.
  Trigger with phrases like "install palantir", "setup palantir",
  "palantir auth", "configure palantir API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, palantir]
---

# Palantir Install & Auth

## Overview
Set up Palantir SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Palantir account with API access
- API key from Palantir dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @palantir/sdk

# Python
pip install palantir
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export PALANTIR_API_KEY="your-api-key"

# Or create .env file
echo 'PALANTIR_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection
```typescript
// Test connection code here
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Palantir dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.palantir.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { PalantirClient } from '@palantir/sdk';

const client = new PalantirClient({
  apiKey: process.env.PALANTIR_API_KEY,
});
```

### Python Setup
```python
from palantir import PalantirClient

client = PalantirClient(
    api_key=os.environ.get('PALANTIR_API_KEY')
)
```

## Resources
- [Palantir Documentation](https://docs.palantir.com)
- [Palantir Dashboard](https://api.palantir.com)
- [Palantir Status](https://status.palantir.com)

## Next Steps
After successful auth, proceed to `palantir-hello-world` for your first API call.