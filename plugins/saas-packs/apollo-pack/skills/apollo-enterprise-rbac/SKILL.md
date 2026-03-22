---
name: apollo-enterprise-rbac
description: |
  Enterprise role-based access control for Apollo.io.
  Use when implementing team permissions, restricting data access,
  or setting up enterprise security controls.
  Trigger with phrases like "apollo rbac", "apollo permissions",
  "apollo roles", "apollo team access", "apollo enterprise security".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, security, rbac]

---
# Apollo Enterprise RBAC

## Overview
Role-based access control for Apollo.io API integrations. Apollo API keys are all-or-nothing (standard vs master), so RBAC must be implemented in your application layer as a proxy between users and the Apollo API. This skill builds a permission matrix, scoped API key system, Express middleware, and admin audit endpoints.

## Prerequisites
- Apollo master API key
- Node.js 18+ with Express

## Instructions

### Step 1: Define Roles and Permission Matrix
Map Apollo API operations to team roles. Apollo's API has two main categories:
- **Read-only**: search (free), enrichment (credits)
- **Write**: contacts CRUD, sequences, deals, tasks

```typescript
// src/rbac/roles.ts
export type Role = 'viewer' | 'analyst' | 'sales_rep' | 'sales_manager' | 'admin';

export interface Permission {
  searchPeople: boolean;       // /mixed_people/api_search (free)
  searchOrganizations: boolean; // /mixed_companies/search (free)
  enrichPerson: boolean;       // /people/match (1 credit)
  bulkEnrich: boolean;         // /people/bulk_match (credits)
  enrichOrg: boolean;          // /organizations/enrich (1 credit)
  manageContacts: boolean;     // /contacts CRUD (master key)
  manageSequences: boolean;    // /emailer_campaigns/* (master key)
  manageDeals: boolean;        // /opportunities/* (master key)
  exportPII: boolean;          // download contacts with email/phone
  viewAnalytics: boolean;      // sequence stats, usage
  manageTeam: boolean;         // create/revoke scoped keys
}

export const PERMISSIONS: Record<Role, Permission> = {
  viewer: {
    searchPeople: true, searchOrganizations: true, enrichPerson: false,
    bulkEnrich: false, enrichOrg: false, manageContacts: false,
    manageSequences: false, manageDeals: false, exportPII: false,
    viewAnalytics: true, manageTeam: false,
  },
  analyst: {
    searchPeople: true, searchOrganizations: true, enrichPerson: true,
    bulkEnrich: false, enrichOrg: true, manageContacts: false,
    manageSequences: false, manageDeals: false, exportPII: false,
    viewAnalytics: true, manageTeam: false,
  },
  sales_rep: {
    searchPeople: true, searchOrganizations: true, enrichPerson: true,
    bulkEnrich: false, enrichOrg: true, manageContacts: true,
    manageSequences: true, manageDeals: true, exportPII: false,
    viewAnalytics: false, manageTeam: false,
  },
  sales_manager: {
    searchPeople: true, searchOrganizations: true, enrichPerson: true,
    bulkEnrich: true, enrichOrg: true, manageContacts: true,
    manageSequences: true, manageDeals: true, exportPII: true,
    viewAnalytics: true, manageTeam: true,
  },
  admin: {
    searchPeople: true, searchOrganizations: true, enrichPerson: true,
    bulkEnrich: true, enrichOrg: true, manageContacts: true,
    manageSequences: true, manageDeals: true, exportPII: true,
    viewAnalytics: true, manageTeam: true,
  },
};
```

### Step 2: Scoped API Key System
```typescript
// src/rbac/api-keys.ts
import crypto from 'crypto';

interface ScopedKey {
  key: string;
  teamId: string;
  role: Role;
  createdBy: string;
  createdAt: string;
  expiresAt: string;
}

// In production: store in database
const keys = new Map<string, ScopedKey>();

export function createScopedKey(teamId: string, role: Role, createdBy: string, ttlDays: number = 90): ScopedKey {
  const entry: ScopedKey = {
    key: `ak_${teamId}_${crypto.randomBytes(16).toString('hex')}`,
    teamId, role, createdBy,
    createdAt: new Date().toISOString(),
    expiresAt: new Date(Date.now() + ttlDays * 86400000).toISOString(),
  };
  keys.set(entry.key, entry);
  return entry;
}

export function resolveKey(apiKey: string): ScopedKey | null {
  const entry = keys.get(apiKey);
  if (!entry) return null;
  if (new Date(entry.expiresAt) < new Date()) { keys.delete(apiKey); return null; }
  return entry;
}

export function revokeKey(apiKey: string) { keys.delete(apiKey); }
```

### Step 3: Permission Middleware
```typescript
// src/rbac/middleware.ts
import { Request, Response, NextFunction } from 'express';
import { PERMISSIONS, Permission } from './roles';
import { resolveKey } from './api-keys';

// Map Apollo API paths to required permissions
const ENDPOINT_PERMISSIONS: Record<string, keyof Permission> = {
  '/mixed_people/api_search': 'searchPeople',
  '/mixed_companies/search': 'searchOrganizations',
  '/people/match': 'enrichPerson',
  '/people/bulk_match': 'bulkEnrich',
  '/organizations/enrich': 'enrichOrg',
  '/contacts': 'manageContacts',
  '/emailer_campaigns': 'manageSequences',
  '/opportunities': 'manageDeals',
};

export function requirePermission(action: keyof Permission) {
  return (req: Request, res: Response, next: NextFunction) => {
    const apiKey = req.headers['x-api-key'] as string;
    if (!apiKey) return res.status(401).json({ error: 'x-api-key header required' });

    const key = resolveKey(apiKey);
    if (!key) return res.status(401).json({ error: 'Invalid or expired API key' });

    if (!PERMISSIONS[key.role][action]) {
      return res.status(403).json({
        error: `Permission denied: ${action} requires role upgrade`,
        currentRole: key.role,
      });
    }

    (req as any).apolloCtx = { teamId: key.teamId, role: key.role, user: key.createdBy };
    next();
  };
}
```

### Step 4: Apollo API Proxy with RBAC
```typescript
// src/rbac/proxy.ts
import express from 'express';
import axios from 'axios';

const app = express();
app.use(express.json());

// Proxy all /apollo/* requests through RBAC
app.all('/apollo/*', (req, res, next) => {
  const apolloPath = req.path.replace('/apollo', '');
  const matchedKey = Object.keys(ENDPOINT_PERMISSIONS).find((p) => apolloPath.startsWith(p));
  if (!matchedKey) return res.status(404).json({ error: 'Unknown Apollo endpoint' });

  requirePermission(ENDPOINT_PERMISSIONS[matchedKey])(req, res, next);
}, async (req, res) => {
  const apolloPath = req.path.replace('/apollo', '');
  try {
    const response = await axios({
      method: req.method as any,
      url: `https://api.apollo.io/api/v1${apolloPath}`,
      data: req.body,
      params: req.query,
      headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! },
    });
    res.status(response.status).json(response.data);
  } catch (err: any) {
    res.status(err.response?.status ?? 500).json(err.response?.data ?? { error: err.message });
  }
});
```

### Step 5: Admin Endpoints
```typescript
// src/rbac/admin.ts
import { Router } from 'express';
import { requirePermission } from './middleware';
import { createScopedKey, revokeKey } from './api-keys';

const admin = Router();
admin.use(requirePermission('manageTeam'));

admin.post('/keys', (req, res) => {
  const { teamId, role, ttlDays } = req.body;
  const ctx = (req as any).apolloCtx;
  const key = createScopedKey(teamId, role, ctx.user, ttlDays);
  res.json({ key: key.key, role: key.role, expiresAt: key.expiresAt });
});

admin.delete('/keys/:key', (req, res) => {
  revokeKey(req.params.key);
  res.json({ revoked: true });
});

admin.get('/usage', async (req, res) => {
  // Check Apollo's usage stats
  const { data } = await axios.get('https://api.apollo.io/api/v1/usage', {
    headers: { 'x-api-key': process.env.APOLLO_API_KEY! },
  });
  res.json(data);
});

export { admin };
```

## Output
- Five-tier role system mapping to Apollo API operations
- Scoped API key creation with configurable TTL and revocation
- Express middleware enforcing per-endpoint permissions
- Apollo API proxy routing all requests through RBAC
- Admin endpoints for key management and usage stats

## Error Handling
| Issue | Resolution |
|-------|------------|
| 403 Permission denied | Check role matrix; request upgrade from admin |
| Key expired | Admin creates new key via `POST /keys` |
| Wrong role for bulk enrichment | Only `sales_manager` and `admin` have `bulkEnrich` |
| Proxy timeout | Increase timeout, check Apollo API latency |

## Resources
- [Apollo API Overview](https://docs.apollo.io/docs/api-overview)
- [Create API Keys](https://docs.apollo.io/docs/create-api-key)
- [RBAC Best Practices (Auth0)](https://auth0.com/docs/manage-users/access-control/rbac)
- [View API Usage Stats](https://docs.apollo.io/reference/view-api-usage-stats)

## Next Steps
Proceed to `apollo-migration-deep-dive` for migration strategies.
