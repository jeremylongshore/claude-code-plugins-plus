---
name: onenote-install-auth
description: 'Install and configure OneNote SDK/API authentication with delegated
  auth (MSAL).

  Use when setting up a new OneNote integration, configuring Azure AD app registration,
  or migrating from deprecated app-only auth.

  Trigger with "install onenote", "setup onenote auth", "onenote credentials", "azure
  ad onenote".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote Install & Auth

## Overview

Set up Microsoft Graph API authentication for OneNote using delegated credentials via MSAL. This skill walks through Azure AD app registration, SDK installation, permission scope selection, token caching, and connection verification for both Python and TypeScript.

**BREAKING CHANGE (March 31, 2025):** App-only authentication (ClientSecretCredential) was deprecated for OneNote APIs. All integrations MUST use delegated auth — DeviceCodeCredential or InteractiveBrowserCredential. If your existing code uses `ClientSecretCredential` with OneNote endpoints, it will receive 403 Forbidden on every call. This skill provides the correct migration path.

## Prerequisites

- Azure account with permission to register applications (Azure AD admin or Application Developer role)
- Node.js 18+ or Python 3.10+
- Access to [Azure Portal App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
- A OneNote account (personal Microsoft account or Microsoft 365 work/school account)

## Instructions

### Step 1: Register an Azure AD Application

1. Navigate to [Azure Portal > App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
2. Click **New registration**
3. Set the **Name** (e.g., `onenote-integration-dev`)
4. Under **Supported account types**, choose:
   - **Single tenant** — only your organization (most restrictive, recommended for internal tools)
   - **Multi-tenant** — any Azure AD directory (needed if serving multiple orgs)
   - **Multi-tenant + personal** — includes personal Microsoft accounts (needed if targeting consumer OneNote)
5. Under **Redirect URI**, select **Public client/native** and set URI to `http://localhost`
6. Click **Register** and note the **Application (client) ID** and **Directory (tenant) ID**

### Step 2: Configure API Permissions

1. In your app registration, go to **API permissions > Add a permission > Microsoft Graph > Delegated permissions**
2. Add the appropriate scope:

| Scope | Use Case |
|-------|----------|
| `Notes.Read` | Read-only access to user's notebooks |
| `Notes.ReadWrite` | Read and write to user's notebooks |
| `Notes.ReadWrite.All` | Read/write all notebooks the user can access (including shared) |
| `Notes.Read.All` | Read all notebooks the user can access (including shared) |

3. Click **Grant admin consent** if you have admin rights (otherwise users see a consent prompt on first login)

### Step 3: Install SDKs

**Python:**
```bash
pip install msgraph-sdk azure-identity
```

**TypeScript/Node:**
```bash
npm install @microsoft/microsoft-graph-client @azure/identity @azure/msal-node
```

### Step 4: Configure Environment Variables

```bash
# .env file — NEVER commit this to version control
AZURE_CLIENT_ID=your-application-client-id
AZURE_TENANT_ID=your-directory-tenant-id
# Do NOT set AZURE_CLIENT_SECRET — app-only auth is deprecated for OneNote
```

### Step 5: Authenticate with Python (DeviceCodeCredential)

```python
import os
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient

CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
TENANT_ID = os.environ["AZURE_TENANT_ID"]

# DeviceCodeCredential prompts user to visit a URL and enter a code
# This is the recommended flow for CLI tools and headless environments
credential = DeviceCodeCredential(
    client_id=CLIENT_ID,
    tenant_id=TENANT_ID,
)

scopes = ["Notes.ReadWrite"]
client = GraphServiceClient(credentials=credential, scopes=scopes)

# Verify connection
notebooks = await client.me.onenote.notebooks.get()
if notebooks and notebooks.value:
    for nb in notebooks.value:
        print(f"Notebook: {nb.display_name} (id: {nb.id})")
else:
    print("No notebooks found — connection succeeded but account has no notebooks")
```

### Step 6: Authenticate with TypeScript (DeviceCodeCredential)

```typescript
import { Client } from "@microsoft/microsoft-graph-client";
import { TokenCredentialAuthenticationProvider } from
  "@microsoft/microsoft-graph-client/authProviders/azureTokenCredentials";
import { DeviceCodeCredential } from "@azure/identity";

const credential = new DeviceCodeCredential({
  clientId: process.env.AZURE_CLIENT_ID!,
  tenantId: process.env.AZURE_TENANT_ID!,
  userPromptCallback: (info) => {
    // Display the device code login instructions to the user
    console.log(info.message);
  },
});

const scopes = ["Notes.ReadWrite"];

const authProvider = new TokenCredentialAuthenticationProvider(credential, {
  scopes,
});

const client = Client.initWithMiddleware({ authProvider });

// Verify connection
const notebooks = await client.api("/me/onenote/notebooks").get();
console.log(`Found ${notebooks.value.length} notebooks`);
for (const nb of notebooks.value) {
  console.log(`  - ${nb.displayName} (${nb.id})`);
}
```

### Step 7: Token Caching (MSAL SerializableTokenCache)

Without token caching, users must re-authenticate on every run. MSAL supports persistent token caching:

```typescript
import { PublicClientApplication } from "@azure/msal-node";
import * as fs from "fs";

const CACHE_PATH = "./.msal-token-cache.json";

const pca = new PublicClientApplication({
  auth: {
    clientId: process.env.AZURE_CLIENT_ID!,
    authority: `https://login.microsoftonline.com/${process.env.AZURE_TENANT_ID}`,
  },
});

// Load cached tokens on startup
const cache = pca.getTokenCache();
if (fs.existsSync(CACHE_PATH)) {
  cache.deserialize(fs.readFileSync(CACHE_PATH, "utf-8"));
}

// After acquiring a token, persist the cache
const result = await pca.acquireTokenByDeviceCode({
  scopes: ["Notes.ReadWrite"],
  deviceCodeCallback: (response) => console.log(response.message),
});

fs.writeFileSync(CACHE_PATH, cache.serialize());
// Add .msal-token-cache.json to .gitignore immediately
```

### Step 8: Multi-Tenant vs Single-Tenant

| Configuration | Authority URL | When to use |
|---------------|--------------|-------------|
| Single tenant | `https://login.microsoftonline.com/{tenant-id}` | Internal enterprise tools |
| Multi-tenant | `https://login.microsoftonline.com/common` | SaaS apps serving multiple orgs |
| Personal accounts | `https://login.microsoftonline.com/consumers` | Consumer OneNote only |

For multi-tenant apps, replace `TENANT_ID` in the authority URL with `common` or `organizations`.

## Output

After completing these steps you will have:
- An Azure AD application registered with correct OneNote permissions
- Working authentication using delegated credentials (DeviceCodeCredential)
- Token caching for persistent sessions without re-authentication
- A verified Graph API connection that lists the user's notebooks

## Error Handling

| Error | Code | Root Cause | Solution |
|-------|------|------------|----------|
| `AADSTS7000218` | 403 | App configured for app-only auth | Reconfigure for delegated auth — app-only was deprecated March 2025 |
| `Insufficient privileges` | 403 | Missing or wrong permission scope | Add `Notes.ReadWrite` in Azure Portal, then re-consent |
| `AADSTS50011` | 400 | Redirect URI mismatch | Set redirect URI to `http://localhost` for device code flow |
| `Token expired` | 401 | Access token has expired (1 hour default) | Implement token refresh or use MSAL's built-in token cache |
| `AADSTS700016` | 400 | Application not found in tenant | Verify CLIENT_ID matches the registered app |
| `InteractionRequired` | — | Cached token invalid, need re-auth | Clear `.msal-token-cache.json` and re-authenticate |

**Diagnosing 403 errors:** If you get 403 after March 2025 on code that previously worked, check whether your credential uses `ClientSecretCredential`. This is the single most common cause — app-only auth for OneNote is permanently deprecated. Switch to `DeviceCodeCredential`.

## Examples

**Quick connectivity test (Python one-liner):**
```python
# Paste into Python REPL after setting AZURE_CLIENT_ID and AZURE_TENANT_ID
from azure.identity import DeviceCodeCredential; from msgraph import GraphServiceClient
c = GraphServiceClient(credentials=DeviceCodeCredential(client_id="YOUR_ID", tenant_id="YOUR_TENANT"), scopes=["Notes.Read"])
print(await c.me.onenote.notebooks.get())
```

**Switching from deprecated app-only auth:**
```typescript
// BEFORE (broken after March 2025):
// const credential = new ClientSecretCredential(tenantId, clientId, clientSecret);

// AFTER (correct):
const credential = new DeviceCodeCredential({ clientId, tenantId });
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Azure App Registration Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
- [MSAL Python Documentation](https://learn.microsoft.com/en-us/entra/msal/python/)
- [Graph API Reference](https://learn.microsoft.com/en-us/graph/api/overview)
- [OneNote Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [Graph Explorer (test queries interactively)](https://developer.microsoft.com/en-us/graph/graph-explorer)

## Next Steps

- Run `onenote-hello-world` to create your first notebook, section, and page
- See `onenote-common-errors` for a complete error decoder reference
- See `onenote-sdk-patterns` for production retry logic and rate limit handling
