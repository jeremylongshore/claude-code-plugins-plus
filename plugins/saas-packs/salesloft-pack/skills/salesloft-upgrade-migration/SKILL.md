---
name: salesloft-upgrade-migration
description: |
  Migrate between SalesLoft API versions and handle breaking changes.
  Use when SalesLoft announces API deprecations, upgrading OAuth flows,
  or transitioning from legacy endpoints.
  Trigger: "upgrade salesloft", "salesloft migration", "salesloft API version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Upgrade & Migration

## Overview

SalesLoft REST API is versioned at v2 with no official SDK -- migrations involve endpoint changes, auth flow updates, and response schema changes. The Cadence Import/Export API was a major addition. Key migration: SalesLoft rebranded some endpoints and added OAuth client credentials flow.

## Migration Scenarios

### Legacy API Key to OAuth 2.0

```typescript
// BEFORE: Static API key (being deprecated for partner apps)
const api = axios.create({
  headers: { Authorization: `Bearer ${process.env.SALESLOFT_API_KEY}` },
});

// AFTER: OAuth 2.0 with token refresh
class SalesloftOAuthClient {
  private tokenStore: { access: string; refresh: string; expiresAt: number };

  async getClient() {
    if (Date.now() > this.tokenStore.expiresAt * 1000 - 300_000) {
      await this.refreshToken();
    }
    return axios.create({
      baseURL: 'https://api.salesloft.com/v2',
      headers: { Authorization: `Bearer ${this.tokenStore.access}` },
    });
  }

  private async refreshToken() {
    const { data } = await axios.post('https://accounts.salesloft.com/oauth/token', {
      grant_type: 'refresh_token',
      refresh_token: this.tokenStore.refresh,
      client_id: process.env.SALESLOFT_CLIENT_ID,
      client_secret: process.env.SALESLOFT_CLIENT_SECRET,
    });
    this.tokenStore = {
      access: data.access_token,
      refresh: data.refresh_token,
      expiresAt: Math.floor(Date.now() / 1000) + data.expires_in,
    };
  }
}
```

### Adding Client Credentials Flow

```typescript
// Client credentials: server-to-server, no user interaction
// Recommended for background sync jobs
async function getServiceToken(): Promise<string> {
  const { data } = await axios.post('https://accounts.salesloft.com/oauth/token', {
    grant_type: 'client_credentials',
    client_id: process.env.SALESLOFT_CLIENT_ID,
    client_secret: process.env.SALESLOFT_CLIENT_SECRET,
  });
  return data.access_token; // No refresh token -- request new when expired
}
```

### Cadence Import/Export API Adoption

```typescript
// Export cadence (portable format -- can import into any SalesLoft instance)
const { data: exported } = await api.get(`/cadence_exports/${cadenceId}.json`);
// Returns agnostic content: steps, email templates, timing

// Import cadence into another instance
const { data: imported } = await api.post('/cadence_imports.json', {
  cadence_content: exported.data,
  settings: {
    name: 'Imported: Q1 Outbound',
    shared: false,
  },
});
```

## Migration Checklist

- [ ] Audit all endpoints used (search codebase for `/v2/`)
- [ ] Check response fields consumed (SalesLoft may add/remove fields)
- [ ] Test with staging OAuth app first
- [ ] Update error handling for any new error codes
- [ ] Verify rate limit costs haven't changed
- [ ] Update webhook signature verification if format changed
- [ ] Run integration tests against new version

## Rollback

```bash
# Pin to previous behavior
git checkout -b rollback/salesloft-migration
git revert <migration-commit>
git push origin rollback/salesloft-migration
```

## Error Handling

| Change | Impact | Migration |
|--------|--------|-----------|
| API key deprecation | Auth stops working | Switch to OAuth 2.0 |
| New required fields | 422 on create | Add new fields to payloads |
| Endpoint rename | 404 on old path | Update URL in client |
| Rate limit cost change | Unexpected 429s | Recalculate pagination budgets |

## Resources

- [SalesLoft API Basics](https://developers.salesloft.com/docs/platform/api-basics/)
- [Cadence Imports](https://developers.salesloft.com/docs/platform/cadence-imports/introduction/)
- [OAuth Client Credentials](https://developers.salesloft.com/docs/platform/api-basics/client-creds/)

## Next Steps

For CI integration during upgrades, see `salesloft-ci-integration`.
