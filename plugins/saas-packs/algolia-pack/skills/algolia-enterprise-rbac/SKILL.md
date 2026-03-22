---
name: algolia-enterprise-rbac
description: |
  Configure Algolia enterprise access control: team-scoped API keys, Secured API Keys
  for multi-tenant RBAC, dashboard team management, and audit logging.
  Trigger: "algolia RBAC", "algolia enterprise", "algolia roles", "algolia permissions",
  "algolia team access", "algolia multi-tenant", "algolia SSO".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Enterprise RBAC

## Overview

Algolia's access control is built on **API keys with ACL (Access Control Lists)**. Each key has specific permissions, index restrictions, and rate limits. For multi-tenant apps, **Secured API Keys** provide per-user filtering without creating individual keys. For team management, Algolia's dashboard supports team members with role-based access.

## API Key ACL Permissions

| ACL | Operations Allowed | Use For |
|-----|-------------------|---------|
| `search` | Search queries | Frontend, search-only clients |
| `browse` | Browse/export all records | Data export, migration scripts |
| `addObject` | Add or replace records | Indexing pipelines |
| `deleteObject` | Delete records | Data cleanup, GDPR deletion |
| `editSettings` | Modify index settings | Deployment scripts |
| `listIndexes` | List all indices | Monitoring, health checks |
| `deleteIndex` | Delete entire indices | Admin operations only |
| `analytics` | Read analytics data | Dashboards, reporting |
| `recommendation` | Algolia Recommend API | Product recommendations |
| `usage` | Read usage data | Billing monitoring |
| `logs` | Read API logs | Debugging, audit |

## Instructions

### Step 1: Define Application Roles

```typescript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

// Role definitions with minimal permissions
const ROLES = {
  // Backend search service: search only, scoped to specific indices
  searchService: {
    acl: ['search'] as const,
    description: 'Search service — production read-only',
    indexes: ['products', 'articles'],
    maxQueriesPerIPPerHour: 100000,
  },

  // Indexing pipeline: write records, no search or delete
  indexingPipeline: {
    acl: ['addObject', 'editSettings', 'listIndexes'] as const,
    description: 'Indexing pipeline — write-only, no delete',
    indexes: ['products', 'articles'],
    maxQueriesPerIPPerHour: 10000,
  },

  // Analytics dashboard: read analytics, no data access
  analyticsDashboard: {
    acl: ['analytics', 'usage', 'listIndexes'] as const,
    description: 'Analytics reader — no record access',
    indexes: ['products', 'articles'],
    maxQueriesPerIPPerHour: 5000,
  },

  // Data admin: full CRUD, restricted to non-production
  dataAdmin: {
    acl: ['search', 'browse', 'addObject', 'deleteObject', 'editSettings', 'listIndexes', 'deleteIndex'] as const,
    description: 'Data admin — full access, staging only',
    indexes: ['staging_*'],
    maxQueriesPerIPPerHour: 50000,
  },
};

async function createRoleKey(roleName: keyof typeof ROLES) {
  const role = ROLES[roleName];
  const { key } = await client.addApiKey({
    apiKey: {
      acl: [...role.acl],
      description: role.description,
      indexes: role.indexes,
      maxQueriesPerIPPerHour: role.maxQueriesPerIPPerHour,
    },
  });
  console.log(`Created ${roleName} key: ...${key.slice(-8)}`);
  return key;
}
```

### Step 2: Multi-Tenant RBAC with Secured API Keys

```typescript
// Secured API Keys embed filters the client cannot bypass.
// Generate on YOUR server, send to the frontend.

interface UserContext {
  userId: string;
  tenantId: string;
  role: 'admin' | 'editor' | 'viewer';
}

function generateUserSearchKey(user: UserContext): string {
  // Base filter: tenant isolation
  let filters = `tenant_id:${user.tenantId}`;

  // Role-based visibility
  switch (user.role) {
    case 'admin':
      // Admins see everything in their tenant
      break;
    case 'editor':
      // Editors see published + their own drafts
      filters += ` AND (status:published OR author_id:${user.userId})`;
      break;
    case 'viewer':
      // Viewers see published only
      filters += ' AND status:published';
      break;
  }

  return client.generateSecuredApiKey({
    parentApiKey: process.env.ALGOLIA_SEARCH_KEY!,
    restrictions: {
      filters,
      validUntil: Math.floor(Date.now() / 1000) + 3600, // 1 hour
      restrictIndices: ['products', 'articles'],
    },
  });
}

// API endpoint: generate key for authenticated user
// GET /api/algolia/key
// Response: { appId: "...", searchKey: "secured_key_here" }
```

### Step 3: Permission Checking Middleware

```typescript
// Validate that the calling service has required Algolia permissions
async function validateKeyPermissions(
  apiKey: string,
  requiredAcl: string[]
): Promise<boolean> {
  try {
    const keyInfo = await client.getApiKey({ key: apiKey });
    const hasAll = requiredAcl.every(perm => keyInfo.acl.includes(perm));

    if (!hasAll) {
      const missing = requiredAcl.filter(p => !keyInfo.acl.includes(p));
      console.warn(`Key missing permissions: ${missing.join(', ')}`);
    }

    return hasAll;
  } catch (e) {
    console.error('Failed to validate API key:', e);
    return false;
  }
}

// Express middleware
function requireAlgoliaPermission(requiredAcl: string[]) {
  return async (req: any, res: any, next: any) => {
    const key = req.headers['x-algolia-api-key'];
    if (!key || !(await validateKeyPermissions(key, requiredAcl))) {
      return res.status(403).json({ error: 'Insufficient Algolia permissions' });
    }
    next();
  };
}
```

### Step 4: API Key Audit and Rotation

```typescript
// List all API keys and audit their permissions
async function auditApiKeys() {
  const { keys } = await client.listApiKeys();

  console.log(`Total API keys: ${keys.length}\n`);

  for (const key of keys) {
    const ageMs = Date.now() - new Date(key.createdAt * 1000).getTime();
    const ageDays = Math.floor(ageMs / (1000 * 60 * 60 * 24));

    console.log(`Key: ...${key.value.slice(-8)}`);
    console.log(`  Description: ${key.description || '(none)'}`);
    console.log(`  ACL: ${key.acl.join(', ')}`);
    console.log(`  Indices: ${key.indexes?.join(', ') || 'ALL'}`);
    console.log(`  Rate limit: ${key.maxQueriesPerIPPerHour || 'unlimited'}/hr`);
    console.log(`  Age: ${ageDays} days`);

    // Flag old keys
    if (ageDays > 90) {
      console.log(`  WARNING: Key is ${ageDays} days old — consider rotation`);
    }
    // Flag overly permissive keys
    if (key.acl.includes('deleteIndex') && !key.description?.includes('admin')) {
      console.log(`  WARNING: Has deleteIndex permission — verify this is intentional`);
    }
    console.log('');
  }
}
```

### Step 5: Dashboard Team Management

```
Algolia Dashboard Team Roles (configured in dashboard.algolia.com > Team):

| Dashboard Role | Can Do                                    | Can't Do              |
|----------------|-------------------------------------------|-----------------------|
| Owner          | Everything + billing + team management    | N/A                   |
| Admin          | All index operations + API key management | Billing               |
| Editor         | Search, index data, edit settings         | API key management    |
| Viewer         | Search, view analytics                    | Modify anything       |

Configure at: dashboard.algolia.com > Settings > Team
Enterprise plans support SSO (SAML 2.0) for team authentication.
```

## Security Checklist

- [ ] Each microservice has its own scoped API key (not shared admin key)
- [ ] Frontend keys are search-only with `referers` restriction
- [ ] Multi-tenant apps use Secured API Keys with `filters`
- [ ] `maxQueriesPerIPPerHour` set on all non-admin keys
- [ ] Keys restricted to specific `indexes` (not all)
- [ ] Key rotation scheduled (every 90 days)
- [ ] Dashboard team members have appropriate roles
- [ ] API key audit runs monthly

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 on search | Key missing `search` ACL | Check key permissions with `getApiKey` |
| Secured key invalid | Parent key deleted/rotated | Regenerate secured keys from new parent |
| Filter bypass | Client-side filter manipulation | Secured API Keys enforce filters server-side |
| Audit shows unknown keys | Leaked or forgotten keys | Delete unrecognized keys, rotate known ones |

## Resources

- [API Keys Guide](https://www.algolia.com/doc/guides/security/api-keys/)
- [Secured API Keys](https://www.algolia.com/doc/guides/security/api-keys/in-depth/secured-api-keys/)
- [Team Management](https://www.algolia.com/doc/guides/security/api-keys/in-depth/api-key-restrictions/)
- [Enterprise SSO](https://www.algolia.com/enterprise/)

## Next Steps

For major platform migrations, see `algolia-migration-deep-dive`.
