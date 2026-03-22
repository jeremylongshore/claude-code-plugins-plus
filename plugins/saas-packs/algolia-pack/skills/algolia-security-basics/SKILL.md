---
name: algolia-security-basics
description: |
  Apply Algolia security best practices: API key scoping, secured API keys,
  frontend vs backend key separation, and key rotation.
  Trigger: "algolia security", "algolia API key security", "secure algolia",
  "algolia secrets", "algolia key rotation", "algolia secured key".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Security Basics

## Overview

Algolia's security model is built around **scoped API keys**. Every Algolia app has three default keys (Admin, Search-Only, Monitoring). For production, create custom keys with minimal permissions and use Secured API Keys for per-user/per-tenant restrictions.

## Key Types and Where to Use Them

| Key Type | ACL | Expose to Frontend? | Use Case |
|----------|-----|---------------------|----------|
| Admin | All operations | **NEVER** | Backend indexing, settings, key management |
| Search-Only | `search` only | Yes (safe) | Frontend search widgets |
| Monitoring | Read monitoring data | No | Health checks, dashboards |
| Custom | You define ACL | Depends on ACL | Scoped backend services |
| Secured | Derived from parent key | Yes | Per-user filtered search |

## Instructions

### Step 1: Environment Variable Setup

```bash
# .env (NEVER commit — add to .gitignore)
ALGOLIA_APP_ID=YourApplicationID
ALGOLIA_ADMIN_KEY=admin_api_key_here        # Backend only
ALGOLIA_SEARCH_KEY=search_only_key_here     # OK for frontend

# .gitignore — MUST include:
.env
.env.local
.env.*.local
```

### Step 2: Create Scoped API Keys

```typescript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

// Create a write-only key for a specific microservice
const { key: indexingKey } = await client.addApiKey({
  apiKey: {
    acl: ['addObject', 'deleteObject', 'editSettings'],
    description: 'Product sync service — write only',
    indexes: ['products', 'products_staging'],  // Restrict to specific indices
    maxQueriesPerIPPerHour: 5000,
    referers: [],  // Empty = no referer restriction (backend use)
  },
});

// Create a search key restricted to specific referers (frontend)
const { key: frontendKey } = await client.addApiKey({
  apiKey: {
    acl: ['search'],
    description: 'Frontend search — domain-restricted',
    indexes: ['products'],
    referers: ['https://mystore.com/*', 'https://*.mystore.com/*'],
    maxQueriesPerIPPerHour: 1000,
    maxHitsPerQuery: 50,
  },
});
```

### Step 3: Generate Secured API Keys (Per-User Filtering)

```typescript
// Secured API keys are generated on YOUR server, not via Algolia API.
// They embed restrictions that the client can't bypass.

function generateUserSearchKey(userId: string, tenantId: string): string {
  const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

  return client.generateSecuredApiKey({
    parentApiKey: process.env.ALGOLIA_SEARCH_KEY!,
    restrictions: {
      // User can only see their tenant's data
      filters: `tenant_id:${tenantId}`,
      // Key expires in 1 hour
      validUntil: Math.floor(Date.now() / 1000) + 3600,
      // Restrict to specific indices
      restrictIndices: ['products'],
      // Optional: restrict sources (IPs)
      restrictSources: '',
    },
  });
}

// Usage in your API endpoint:
// const userKey = generateUserSearchKey(req.user.id, req.user.tenantId);
// return { appId: process.env.ALGOLIA_APP_ID, searchKey: userKey };
```

### Step 4: Key Rotation Procedure

```typescript
async function rotateApiKey(oldKeyDescription: string) {
  const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

  // 1. List keys to find the old one
  const { keys } = await client.listApiKeys();
  const oldKey = keys.find(k => k.description === oldKeyDescription);
  if (!oldKey) throw new Error(`Key not found: ${oldKeyDescription}`);

  // 2. Create new key with same ACL
  const { key: newKey } = await client.addApiKey({
    apiKey: {
      acl: oldKey.acl,
      description: `${oldKeyDescription} (rotated ${new Date().toISOString().split('T')[0]})`,
      indexes: oldKey.indexes || [],
      maxQueriesPerIPPerHour: oldKey.maxQueriesPerIPPerHour || 0,
      referers: oldKey.referers || [],
    },
  });

  console.log(`New key created: ...${newKey.slice(-8)}`);
  console.log('Update your env vars, then delete the old key:');
  console.log(`  client.deleteApiKey({ key: '${oldKey.value}' })`);

  return newKey;
}
```

## Security Checklist

- [ ] Admin key in env vars, never in frontend code or git
- [ ] `.env` files in `.gitignore`
- [ ] Frontend uses Search-Only or Secured API key
- [ ] Custom keys have minimal ACL (least privilege)
- [ ] `referers` set on frontend keys to prevent abuse
- [ ] `maxQueriesPerIPPerHour` set on all public keys
- [ ] Secured API keys have `validUntil` (expiration)
- [ ] Key rotation scheduled quarterly
- [ ] Git history scanned for accidentally committed keys

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Admin key exposed in frontend | Code review, git scanning | Rotate immediately, restrict referers |
| Key in git history | `git log -S 'ALGOLIA'` | Rotate key, use git-secrets or gitleaks |
| Excessive ACL on key | Audit key permissions | Create scoped replacement key |
| Expired secured key | `validUntil` in the past | Generate fresh secured key |

## Resources

- [API Keys Guide](https://www.algolia.com/doc/guides/security/api-keys/)
- [Secured API Keys](https://www.algolia.com/doc/guides/security/api-keys/in-depth/secured-api-keys/)
- [API Key Restrictions](https://www.algolia.com/doc/guides/security/api-keys/in-depth/api-key-restrictions/)

## Next Steps

For production deployment, see `algolia-prod-checklist`.
