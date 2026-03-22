---
name: mindtickle-install-auth
description: |
  Install and configure MindTickle SDK/API authentication.
  Use when setting up a new MindTickle integration.
  Trigger: "install mindtickle", "setup mindtickle", "mindtickle auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Install & Auth

## Overview
Set up MindTickle API for sales readiness, training content management, and rep performance analytics.

## Prerequisites
- MindTickle account and API access
- API key/credentials from MindTickle dashboard
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Install SDK
```bash
npm install @mindtickle/sdk
# API key from MindTickle Admin > Integrations > API
```

### Step 2: Configure Authentication
```bash
export MINDTICKLE_API_KEY="your-api-key-here"
echo 'MINDTICKLE_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection (TypeScript)
```typescript
import { MindTickleClient } from '@mindtickle/sdk';
const client = new MindTickleClient({ apiKey: process.env.MINDTICKLE_API_KEY });
const users = await client.users.list({ limit: 5 });
console.log(`Found ${users.total} users`);
```

### Step 4: Verify Connection (Python)
```python
import mindtickle
client = mindtickle.Client(api_key=os.environ['MINDTICKLE_API_KEY'])
users = client.users.list(limit=5)
print(f'Found {users.total} users')
```

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Invalid API key | 401 | Verify credentials in dashboard |
| Permission denied | 403 | Check API scopes/permissions |
| Rate limited | 429 | Implement backoff |

## Resources
- [MindTickle Documentation](https://www.mindtickle.com/platform/integrations/)

## Next Steps
After auth, proceed to `mindtickle-hello-world`.
