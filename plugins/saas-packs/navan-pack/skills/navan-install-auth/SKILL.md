---
name: navan-install-auth
description: |
  Install and configure Navan SDK/API authentication.
  Use when setting up a new Navan integration.
  Trigger: "install navan", "setup navan", "navan auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Install & Auth

## Overview
Set up Navan API for corporate travel booking, expense management, and spend analytics.

## Prerequisites
- Navan account and API access
- API key/credentials from Navan dashboard
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Install SDK
```bash
npm install @navan/sdk
# API credentials from Navan Admin > Integrations
```

### Step 2: Configure Authentication
```bash
export NAVAN_API_KEY="your-api-key-here"
echo 'NAVAN_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection (TypeScript)
```typescript
import { NavanClient } from '@navan/sdk';
const client = new NavanClient({
  apiKey: process.env.NAVAN_API_KEY,
  companyId: process.env.NAVAN_COMPANY_ID
});
const trips = await client.trips.list({ limit: 5 });
console.log(`Found ${trips.total} trips`);
```

### Step 4: Verify Connection (Python)
```python
import navan
client = navan.Client(api_key=os.environ['NAVAN_API_KEY'],
                      company_id=os.environ['NAVAN_COMPANY_ID'])
trips = client.trips.list(limit=5)
print(f'Found {trips.total} trips')
```

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Invalid API key | 401 | Verify credentials in dashboard |
| Permission denied | 403 | Check API scopes/permissions |
| Rate limited | 429 | Implement backoff |

## Resources
- [Navan Documentation](https://app.navan.com/app/helpcenter)

## Next Steps
After auth, proceed to `navan-hello-world`.
