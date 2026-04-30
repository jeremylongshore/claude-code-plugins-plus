---
name: onenote-security-basics
description: 'Implement secure authentication, token management, and permission scoping
  for OneNote Graph API.

  Use when hardening OneNote integrations, implementing least-privilege permissions,
  or managing token lifecycle.

  Trigger with "onenote security", "onenote permissions", "onenote token management",
  "onenote least privilege".

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
# OneNote Security Basics

## Overview

OneNote Graph API security changed fundamentally on March 31, 2025, when Microsoft deprecated app-only authentication for OneNote endpoints. Every integration must now use delegated authentication through MSAL, which means real users must sign in — no more background service accounts with client secrets. This skill covers the full security surface: permission scoping, token lifecycle management, MSAL cache serialization, credential storage, and multi-tenant hardening. Get any of these wrong and your integration either breaks silently (expired tokens returning 401s) or over-provisions access (Notes.ReadWrite.All when Notes.Read suffices).

## Prerequisites

- Azure AD app registration with redirect URI configured at https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps
- Microsoft 365 license (E3/E5/Business) with OneNote enabled
- Python: `pip install msgraph-sdk azure-identity msal` or Node: `npm install @microsoft/microsoft-graph-client @azure/identity @azure/msal-node`
- Understanding of OAuth 2.0 authorization code flow and delegated permissions

## Instructions

### Permission Scope Matrix

Choose the minimum scope required for your use case:

| Scope | Read notebooks | Read pages | Create pages | Create notebooks | Admin consent? |
|-------|:-:|:-:|:-:|:-:|:-:|
| `Notes.Read` | Yes | Yes | No | No | No |
| `Notes.ReadWrite` | Yes | Yes | Yes | Yes | No |
| `Notes.ReadWrite.All` | Yes | Yes | Yes | Yes | **Yes** |
| `Notes.Create` | No | No | Yes | Yes | No |

**Least-privilege recommendations:**
- Read-only dashboards: `Notes.Read` (user consent only)
- Personal note creation: `Notes.ReadWrite` (user consent only)
- Cross-user/organizational access: `Notes.ReadWrite.All` (requires tenant admin approval)
- Write-only ingestion: `Notes.Create` (cannot read back what was written)

### Delegated Authentication Setup (Post-2025 Mandatory)

**CRITICAL:** App-only authentication (ClientSecretCredential) was deprecated for OneNote endpoints on March 31, 2025. All code below uses delegated auth exclusively.

**Python — Device Code Flow (headless/CLI environments):**

```python
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient
import os

CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
TENANT_ID = os.environ["AZURE_TENANT_ID"]

# Minimal scopes — only request what you need
scopes = ["Notes.ReadWrite"]

credential = DeviceCodeCredential(
    client_id=CLIENT_ID,
    tenant_id=TENANT_ID,
    # cache_persistence_options enables silent token renewal
)
client = GraphServiceClient(credentials=credential, scopes=scopes)
```

**TypeScript — Interactive Browser Flow (web apps):**

```typescript
import { DeviceCodeCredential } from "@azure/identity";
import { Client } from "@microsoft/microsoft-graph-client";
import { TokenCredentialAuthenticationProvider }
  from "@microsoft/microsoft-graph-client/authProviders/azureTokenCredentials";

const credential = new DeviceCodeCredential({
  clientId: process.env.AZURE_CLIENT_ID!,
  tenantId: process.env.AZURE_TENANT_ID!,
});

const scopes = ["Notes.ReadWrite"];
const authProvider = new TokenCredentialAuthenticationProvider(credential, { scopes });
const client = Client.initWithMiddleware({ authProvider });
```

### Token Lifecycle Management

Access tokens expire after **1 hour**. Refresh tokens last **90 days** but can be revoked by admin policy. Your code must handle silent renewal:

```python
# Python: MSAL token cache serialization for persistent sessions
import msal
import json
import os

CACHE_FILE = os.path.expanduser("~/.onenote-token-cache.json")

def get_msal_app():
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        cache.deserialize(open(CACHE_FILE).read())

    app = msal.PublicClientApplication(
        client_id=os.environ["AZURE_CLIENT_ID"],
        authority=f"https://login.microsoftonline.com/{os.environ['AZURE_TENANT_ID']}",
        token_cache=cache,
    )
    return app, cache

def acquire_token(app, cache):
    accounts = app.get_accounts()
    if accounts:
        # Silent renewal — no user interaction needed if refresh token valid
        result = app.acquire_token_silent(
            scopes=["https://graph.microsoft.com/Notes.ReadWrite"],
            account=accounts[0],
        )
        if result and "access_token" in result:
            save_cache(cache)
            return result["access_token"]

    # Fallback: device code flow requires user interaction
    flow = app.initiate_device_flow(
        scopes=["https://graph.microsoft.com/Notes.ReadWrite"]
    )
    print(flow["message"])  # "Go to https://microsoft.com/devicelogin..."
    result = app.acquire_token_by_device_flow(flow)
    save_cache(cache)
    return result.get("access_token")

def save_cache(cache):
    if cache.has_state_changed:
        with open(CACHE_FILE, "w") as f:
            f.write(cache.serialize())
        os.chmod(CACHE_FILE, 0o600)  # Owner-only read/write
```

### Secure Credential Storage

Never store client IDs or tenant IDs in source code. Use environment variables at minimum, Azure Key Vault for production:

```bash
# Development: .env file (add to .gitignore FIRST)
echo ".env" >> .gitignore
cat > .env << 'EOF'
AZURE_CLIENT_ID=your-app-registration-client-id
AZURE_TENANT_ID=your-directory-tenant-id
EOF
chmod 600 .env
```

```python
# Production: Azure Key Vault integration
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

vault_url = "https://your-vault.vault.azure.net"
kv_client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())

client_id = kv_client.get_secret("onenote-client-id").value
tenant_id = kv_client.get_secret("onenote-tenant-id").value
```

### Multi-Tenant Security Considerations

For apps serving multiple organizations:
- Register as a multi-tenant app (set `supportedAccountTypes` to `AzureADMultipleOrgs`)
- Validate the `tid` (tenant ID) claim in every token — reject tokens from unexpected tenants
- Store per-tenant token caches separately (never mix tenant tokens)
- Handle Conditional Access policies: catch `claims` challenge in 401 responses and re-authenticate with the required claims

### Security Checklist for Production

- [ ] Using delegated auth (NOT app-only/ClientSecretCredential — deprecated March 2025)
- [ ] Minimum required scopes (Notes.Read unless writes needed)
- [ ] Token cache file has 0600 permissions (owner-only)
- [ ] MSAL cache serialized to disk for silent renewal
- [ ] Client ID and tenant ID sourced from environment or Key Vault
- [ ] .env file in .gitignore
- [ ] Token claims validated (aud, tid, exp)
- [ ] Refresh token rotation monitored (90-day expiry alert)
- [ ] Admin consent obtained for Notes.ReadWrite.All (if needed)
- [ ] Conditional Access error handling implemented

## Output

After applying this skill, your OneNote integration will have: least-privilege permission scoping matched to actual usage, persistent MSAL token cache with silent renewal, secure credential storage using environment variables or Key Vault, and a verified security checklist. Authentication failures will produce actionable error messages instead of silent 401 loops.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `AADSTS65001: user needs to consent` | Scope not yet granted by user | Redirect to consent URL or use admin consent endpoint |
| `AADSTS700016: app not found` | Wrong client ID or wrong tenant | Verify AZURE_CLIENT_ID matches portal registration |
| `AADSTS50076: MFA required` | Conditional Access policy | Use InteractiveBrowserCredential (device code cannot handle MFA prompts) |
| `403 Forbidden` on OneNote calls | Missing Notes.* permission or using app-only auth | Check scope in token; switch to delegated auth |
| `401 Unauthorized` after working | Access token expired, silent renewal failed | Check refresh token validity; re-serialize cache |
| Token cache file empty after restart | Cache not serialized on shutdown | Call `save_cache()` in atexit handler |

## Examples

**Verify your current token scopes:**

```python
import requests

def check_token_scopes(access_token: str) -> list[str]:
    """Decode token to inspect granted scopes (without validation)."""
    import base64, json
    payload = access_token.split(".")[1]
    payload += "=" * (4 - len(payload) % 4)  # pad base64
    claims = json.loads(base64.urlsafe_b64decode(payload))
    return claims.get("scp", "").split(" ")

# Usage
scopes = check_token_scopes(token)
if "Notes.ReadWrite" not in scopes:
    raise PermissionError(f"Token only has: {scopes}. Need Notes.ReadWrite.")
```

**Rotate to new credentials without downtime:**

```bash
# 1. Register new app in Azure portal
# 2. Update Key Vault with new credentials
az keyvault secret set --vault-name your-vault --name onenote-client-id --value NEW_CLIENT_ID
# 3. Clear MSAL cache to force re-auth with new app
rm ~/.onenote-token-cache.json
# 4. First request will trigger device code flow with new app
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [MSAL Python Documentation](https://learn.microsoft.com/en-us/entra/msal/python/)
- [Azure App Registration](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
- [OneNote Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [Graph API Reference](https://learn.microsoft.com/en-us/graph/api/overview)
- [Known Issues](https://learn.microsoft.com/en-us/graph/known-issues)

## Next Steps

- Apply `onenote-prod-checklist` for full production readiness review
- Use `onenote-reference-architecture` to understand API path differences across notebook locations
- See `onenote-rate-limits` for throttling and Retry-After handling
