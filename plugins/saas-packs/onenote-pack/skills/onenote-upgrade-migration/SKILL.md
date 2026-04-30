---
name: onenote-upgrade-migration
description: 'Migrate OneNote integrations across Graph SDK versions, auth deprecations,
  and API changes.

  Use when upgrading Graph SDK, migrating from app-only to delegated auth, or handling
  deprecated endpoints.

  Trigger with "onenote upgrade", "onenote migration", "graph sdk upgrade", "onenote
  breaking changes".

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
# OneNote Upgrade & Migration

## Overview

Microsoft shipped three breaking changes to OneNote integrations in under two years: webhook decommissioning (June 2023), search endpoint deprecation (April 2024), and app-only auth deprecation (March 2025). The Graph SDK itself had breaking changes between v5 and v6. This skill provides exact migration diffs, verification steps, and rollback strategies for each breaking change.

## Prerequisites

- Existing OneNote integration using Graph API
- Node.js 18+ (TypeScript SDK) or Python 3.10+ (Python SDK)
- Git for branch-based migration with rollback capability
- Azure portal access for app registration changes (auth migration)

## Instructions

### Breaking Changes Timeline

| Date | Change | Impact |
|------|--------|--------|
| June 16, 2023 | Webhooks decommissioned | Subscription notifications stop |
| April 2024 | Search endpoint deprecated | `/pages?search=` returns 404 |
| March 31, 2025 | App-only auth deprecated | `ClientSecretCredential` returns 403 |

### Migration 1: App-Only to Delegated Auth

**Before (broken after March 2025):**

```typescript
// OLD — ClientSecretCredential (DEPRECATED for OneNote)
import { ClientSecretCredential } from "@azure/identity";
const credential = new ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET);
const authProvider = new TokenCredentialAuthenticationProvider(credential, {
  scopes: ["https://graph.microsoft.com/.default"],
});
```

**After:**

```typescript
// NEW — DeviceCodeCredential (required)
import { DeviceCodeCredential } from "@azure/identity";
const credential = new DeviceCodeCredential({
  clientId: CLIENT_ID, tenantId: TENANT_ID,
  userPromptCallback: (info) =>
    console.log(`Open ${info.verificationUri} and enter code: ${info.userCode}`),
});
const authProvider = new TokenCredentialAuthenticationProvider(credential, {
  scopes: ["Notes.Read", "Notes.ReadWrite"],  // Explicit, not .default
});
const client = Client.initWithMiddleware({ authProvider });
```

**Python equivalent:**

```python
# OLD: credential = ClientSecretCredential(tenant_id, client_id, client_secret)
# NEW:
from azure.identity import DeviceCodeCredential
credential = DeviceCodeCredential(client_id=CLIENT_ID, tenant_id=TENANT_ID)
```

**Required Azure portal changes:** Add "Mobile and desktop applications" platform with `http://localhost` redirect URI to your app registration.

### Migration 2: Webhooks to Polling

```typescript
// OLD — Webhook subscription (DECOMMISSIONED June 2023)
// await client.api("/subscriptions").post({ resource: "/me/onenote/pages", ... });

// NEW — Polling with delta link tracking
async function pollForChanges(client: any, deltaLink: string | null) {
  const endpoint = deltaLink || "/me/onenote/notebooks";
  const response = await client.api(endpoint)
    .header("Prefer", "odata.track-changes").get();

  for (const item of response.value || []) {
    await processChange(item);
  }
  return response["@odata.deltaLink"] || deltaLink;
}

// Poll every 60s (stays under 600 req/60s per-user rate limit)
let deltaLink: string | null = null;
setInterval(async () => {
  try { deltaLink = await pollForChanges(client, deltaLink); }
  catch (err: any) {
    if (err?.statusCode === 429) {
      console.warn(`Rate limited. Retry after ${err.headers?.["retry-after"] ?? 30}s`);
    }
  }
}, 60_000);
```

### Migration 3: Search Endpoint to OData Filters

```typescript
// OLD — Search endpoint (DEPRECATED April 2024)
// const results = await client.api("/me/onenote/pages").query({ search: "term" }).get();

// NEW — OData filter for title, client-side for content
async function searchPages(client: any, query: string) {
  // Server-side title filter
  const titleMatches = await client.api("/me/onenote/pages")
    .filter(`contains(title,'${query.replace(/'/g, "''")}')`)
    .top(50).orderby("lastModifiedDateTime desc").get();

  // Client-side content search (Graph no longer supports full-text)
  const contentMatches: any[] = [];
  const pages = await client.api("/me/onenote/pages").top(100)
    .orderby("lastModifiedDateTime desc").get();
  for (const page of pages.value) {
    const html = await client.api(`/me/onenote/pages/${page.id}/content`).get();
    if (html.replace(/<[^>]+>/g, "").toLowerCase().includes(query.toLowerCase())) {
      contentMatches.push(page);
    }
  }

  // Deduplicate
  const seen = new Set(titleMatches.value.map((p: any) => p.id));
  return [...titleMatches.value, ...contentMatches.filter((m) => !seen.has(m.id))];
}
```

### Migration 4: Graph SDK v5 to v6 (TypeScript)

```typescript
// SDK v5 — callback-based auth (REMOVED in v6)
const client = Client.init({
  authProvider: (done) => done(null, accessToken),
});

// SDK v6 — middleware-based auth (REQUIRED)
import { TokenCredentialAuthenticationProvider } from
  "@microsoft/microsoft-graph-client/authProviders/azureTokenCredentials";
const authProvider = new TokenCredentialAuthenticationProvider(credential, {
  scopes: ["Notes.Read", "Notes.ReadWrite"],
});
const client = Client.initWithMiddleware({ authProvider });
```

### Migration Checklists

**Auth migration:** Remove `AZURE_CLIENT_SECRET` from env/secrets. Add redirect URI in Azure portal. Replace `.default` with explicit scopes. Verify `GET /me/onenote/notebooks` returns 200.

**SDK upgrade:** Update `@microsoft/microsoft-graph-client` to v6+. Replace `Client.init()` with `Client.initWithMiddleware()`. Remove callback auth providers. Run full test suite.

**Search migration:** Replace `/pages?search=` with OData `$filter`. Add client-side content search fallback. Performance test: client-side search under 2s for 100 pages.

### Feature Detection at Runtime

```typescript
export function requiresDelegatedAuth(): boolean { return true; } // Since March 2025
export function isSearchEndpointAvailable(): boolean { return false; } // Since April 2024
export function isWebhookAvailable(): boolean { return false; } // Since June 2023
```

### Rollback Strategy

Use a feature flag for gradual auth migration:

```typescript
const useDelegated = process.env.ONENOTE_AUTH_MODE !== "legacy";
const credential = useDelegated
  ? new DeviceCodeCredential({ clientId, tenantId })
  : new ClientSecretCredential(tenantId, clientId, clientSecret); // Legacy fallback
```

## Output

- Auth migration: `ClientSecretCredential` to `DeviceCodeCredential` with code diff
- Webhook migration: subscription API to polling with delta queries
- Search migration: deprecated endpoint to OData filters + client-side search
- SDK v5 to v6: `Client.init()` to `Client.initWithMiddleware()`
- Migration checklists and feature detection module
- Rollback strategy with feature flag pattern

## Error Handling

| Migration Error | Cause | Fix |
|----------------|-------|-----|
| `403 Forbidden` after auth migration | Missing redirect URI | Add `http://localhost` to "Mobile and desktop" platform in Azure portal |
| `InvalidScope` on token request | Using `.default` with delegated auth | Use explicit scopes: `Notes.Read`, `Notes.ReadWrite` |
| `TypeError: Client.init is not a function` | SDK v6 removed `Client.init` | Use `Client.initWithMiddleware` |
| `404` on search endpoint | Removed April 2024 | Use OData `$filter` + client-side content search |
| `400` on subscription create | Webhooks decommissioned June 2023 | Switch to polling with delta queries |

## Examples

```bash
# Check which migrations your codebase needs
grep -r "ClientSecretCredential" src/ --include="*.ts" --include="*.py"
grep -r "search=" src/ --include="*.ts" --include="*.py"
grep -r "/subscriptions" src/ --include="*.ts" --include="*.py"
grep -r "Client.init(" src/ --include="*.ts"
```

```typescript
// Smoke test after auth migration
const client = getGraphClient();
const nb = await client.api("/me/onenote/notebooks").top(1).get();
console.log("Auth migration OK:", nb.value.length, "notebooks");
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Graph API Known Issues](https://learn.microsoft.com/en-us/graph/known-issues)
- [Azure App Registration](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
- [MSAL Python](https://learn.microsoft.com/en-us/entra/msal/python/)
- [OneNote Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)

## Next Steps

- Set up CI for migrated code with `onenote-ci-integration`
- Debug migration issues with `onenote-debug-bundle`
- Review security after migration with `onenote-security-basics`
