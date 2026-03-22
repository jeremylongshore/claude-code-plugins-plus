---
name: lucidchart-install-auth
description: |
  Install and configure Lucidchart SDK/API authentication.
  Use when setting up a new Lucidchart integration.
  Trigger: "install lucidchart", "setup lucidchart", "lucidchart auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Install & Auth

## Overview
Set up Lucid REST API for programmatic diagram creation and document management.

## Prerequisites
- Lucidchart account and API access
- API key/credentials from Lucidchart dashboard
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Install SDK
```bash
npm install @lucid-co/sdk
# OAuth2 app credentials from developer.lucid.co
```

### Step 2: Configure Authentication
```bash
export LUCID_API_KEY="your-api-key-here"
echo 'LUCID_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection (TypeScript)
```typescript
import { LucidClient } from '@lucid-co/sdk';
const client = new LucidClient({
  clientId: process.env.LUCID_CLIENT_ID,
  clientSecret: process.env.LUCID_CLIENT_SECRET
});
const docs = await client.documents.list();
console.log(`Found ${docs.length} documents`);
```

### Step 4: Verify Connection (Python)
```python
import lucid
client = lucid.Client(client_id=os.environ['LUCID_CLIENT_ID'],
                      client_secret=os.environ['LUCID_CLIENT_SECRET'])
docs = client.documents.list()
print(f'Found {len(docs)} documents')
```

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Invalid API key | 401 | Verify credentials in dashboard |
| Permission denied | 403 | Check API scopes/permissions |
| Rate limited | 429 | Implement backoff |

## Resources
- [Lucidchart Documentation](https://developer.lucid.co/reference/overview)

## Next Steps
After auth, proceed to `lucidchart-hello-world`.
