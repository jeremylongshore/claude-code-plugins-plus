---
name: onenote-install-auth
description: |
  Install and configure OneNote SDK/API authentication.
  Use when setting up a new OneNote integration.
  Trigger: "install onenote", "setup onenote", "onenote auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote Install & Auth

## Overview
Set up Microsoft Graph API for OneNote notebooks, sections, and pages management.

## Prerequisites
- OneNote account and API access
- API key/credentials from OneNote dashboard
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Install SDK
```bash
npm install @microsoft/microsoft-graph-client @azure/identity
# or: pip install msgraph-sdk azure-identity
```

### Step 2: Configure Authentication
```bash
export MICROSOFT_GRAPH_TOKEN="your-api-key-here"
echo 'MICROSOFT_GRAPH_TOKEN=your-api-key' >> .env
```

### Step 3: Verify Connection (TypeScript)
```typescript
import { Client } from '@microsoft/microsoft-graph-client';
import { TokenCredentialAuthenticationProvider } from '@microsoft/microsoft-graph-client/authProviders/azureTokenCredentials';
import { ClientSecretCredential } from '@azure/identity';

const credential = new ClientSecretCredential(
  process.env.AZURE_TENANT_ID!,
  process.env.AZURE_CLIENT_ID!,
  process.env.AZURE_CLIENT_SECRET!
);
const authProvider = new TokenCredentialAuthenticationProvider(credential, {
  scopes: ['https://graph.microsoft.com/.default']
});
const client = Client.initWithMiddleware({ authProvider });

const notebooks = await client.api('/me/onenote/notebooks').get();
console.log(`Found ${notebooks.value.length} notebooks`);
```

### Step 4: Verify Connection (Python)
```python
from msgraph import GraphServiceClient
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id=os.environ['AZURE_TENANT_ID'],
    client_id=os.environ['AZURE_CLIENT_ID'],
    client_secret=os.environ['AZURE_CLIENT_SECRET']
)
client = GraphServiceClient(credential)
notebooks = await client.me.onenote.notebooks.get()
print(f'Found {len(notebooks.value)} notebooks')
```

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Invalid API key | 401 | Verify credentials in dashboard |
| Permission denied | 403 | Check API scopes/permissions |
| Rate limited | 429 | Implement backoff |

## Resources
- [OneNote Documentation](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
After auth, proceed to `onenote-hello-world`.
