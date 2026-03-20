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
---
# Apollo Enterprise RBAC

## Overview
Implement role-based access control for Apollo.io integrations with granular permissions, team-scoped API keys, permission middleware, and admin audit endpoints. Restricts who can search, enrich, export PII, and manage sequences.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Define Roles and Permissions
```typescript
// src/rbac/roles.ts
export type Role = 'viewer' | 'analyst' | 'sales_rep' | 'sales_manager' | 'admin';

export interface Permission {
  search: boolean;
  enrich: boolean;
  exportPII: boolean;
  manageSequences: boolean;
  createSequences: boolean;
  viewAnalytics: boolean;
  manageTeam: boolean;
  manageApiKeys: boolean;
}

export const ROLE_PERMISSIONS: Record<Role, Permission> = {
  viewer: {
    search: true, enrich: false, exportPII: false,
    manageSequences: false, createSequences: false,
    viewAnalytics: true, manageTeam: false, manageApiKeys: false,
  },
  analyst: {
    search: true, enrich: true, exportPII: false,
    manageSequences: false, createSequences: false,
    viewAnalytics: true, manageTeam: false, manageApiKeys: false,
  },
  sales_rep: {
    search: true, enrich: true, exportPII: false,
    manageSequences: true, createSequences: false,
    viewAnalytics: false, manageTeam: false, manageApiKeys: false,
  },
  sales_manager: {
    search: true, enrich: true, exportPII: true,
    manageSequences: true, createSequences: true,
    viewAnalytics: true, manageTeam: true, manageApiKeys: false,
  },
  admin: {
    search: true, enrich: true, exportPII: true,
    manageSequences: true, createSequences: true,
    viewAnalytics: true, manageTeam: true, manageApiKeys: true,
  },
};
```

### Step 2: Implement Team-Scoped API Keys
```typescript
// src/rbac/api-keys.ts
interface ScopedApiKey {
  key: string;
  teamId: string;
  role: Role;
  createdBy: string;
  createdAt: string;
  expiresAt?: string;
}

// In production, store in database. This is the schema.
const apiKeys: Map<string, ScopedApiKey> = new Map();

export function createScopedKey(teamId: string, role: Role, createdBy: string): ScopedApiKey {
  const key: ScopedApiKey = {
    key: `apollo_${teamId}_${Date.now()}_${Math.random().toString(36).slice(2)}`,
    teamId,
    role,
    createdBy,
    createdAt: new Date().toISOString(),
    expiresAt: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),  // 90 days
  };
  apiKeys.set(key.key, key);
  return key;
}

export function resolveKey(apiKey: string): ScopedApiKey | undefined {
  const key = apiKeys.get(apiKey);
  if (!key) return undefined;
  if (key.expiresAt && new Date(key.expiresAt) < new Date()) return undefined;
  return key;
}
```

### Step 3: Create Permission Middleware
```typescript
// src/rbac/middleware.ts
import { Request, Response, NextFunction } from 'express';
import { ROLE_PERMISSIONS, Permission, Role } from './roles';
import { resolveKey } from './api-keys';

export function requirePermission(action: keyof Permission) {
  return (req: Request, res: Response, next: NextFunction) => {
    const apiKey = req.headers['x-api-key'] as string;
    if (!apiKey) {
      return res.status(401).json({ error: 'API key required' });
    }

    const key = resolveKey(apiKey);
    if (!key) {
      return res.status(401).json({ error: 'Invalid or expired API key' });
    }

    const permissions = ROLE_PERMISSIONS[key.role];
    if (!permissions[action]) {
      return res.status(403).json({
        error: `Permission denied: ${action} requires role upgrade`,
        currentRole: key.role,
        requiredPermission: action,
      });
    }

    // Attach user context to request
    (req as any).apolloContext = { teamId: key.teamId, role: key.role, userId: key.createdBy };
    next();
  };
}

// Usage:
// app.post('/api/search', requirePermission('search'), searchHandler);
// app.post('/api/enrich', requirePermission('enrich'), enrichHandler);
// app.post('/api/export', requirePermission('exportPII'), exportHandler);
// app.post('/api/sequences', requirePermission('createSequences'), sequenceHandler);
```

### Step 4: Build Admin Audit Endpoints
```typescript
// src/rbac/admin.ts
import express from 'express';
import { requirePermission } from './middleware';

const adminRouter = express.Router();

// All admin routes require manageTeam permission
adminRouter.use(requirePermission('manageTeam'));

// List team members and their roles
adminRouter.get('/team', (req, res) => {
  const { teamId } = (req as any).apolloContext;
  // In production, query database
  res.json({ teamId, members: [] });
});

// View API key usage
adminRouter.get('/usage', (req, res) => {
  const { teamId } = (req as any).apolloContext;
  res.json({
    teamId,
    period: 'current_month',
    searches: 450,
    enrichments: 120,
    sequences: 5,
    creditsRemaining: 880,
  });
});

// Audit log
adminRouter.get('/audit', (req, res) => {
  const { teamId } = (req as any).apolloContext;
  res.json({
    teamId,
    entries: [
      { timestamp: '2025-01-15T10:00:00Z', user: 'jane@co.com', action: 'search', detail: 'Searched 50 contacts' },
      { timestamp: '2025-01-15T10:05:00Z', user: 'john@co.com', action: 'enrich', detail: 'Enriched 10 contacts' },
    ],
  });
});

export { adminRouter };
```

### Step 5: Apply RBAC to Apollo API Proxy
```typescript
// src/rbac/proxy.ts
import express from 'express';
import axios from 'axios';
import { requirePermission } from './middleware';

const app = express();
app.use(express.json());

const APOLLO_ENDPOINT_PERMISSIONS: Record<string, keyof Permission> = {
  '/people/search': 'search',
  '/organizations/search': 'search',
  '/people/match': 'enrich',
  '/organizations/enrich': 'enrich',
  '/emailer_campaigns': 'manageSequences',
  '/contacts': 'search',
};

// Proxy all Apollo API calls through RBAC
app.all('/apollo/*', (req, res, next) => {
  const apolloPath = req.path.replace('/apollo', '');
  const permission = APOLLO_ENDPOINT_PERMISSIONS[apolloPath];
  if (!permission) return res.status(404).json({ error: 'Unknown endpoint' });
  requirePermission(permission)(req, res, next);
}, async (req, res) => {
  const apolloPath = req.path.replace('/apollo', '');
  try {
    const response = await axios({
      method: req.method as any,
      url: `https://api.apollo.io/v1${apolloPath}`,
      data: req.body,
      params: { api_key: process.env.APOLLO_API_KEY },
      headers: { 'Content-Type': 'application/json' },
    });
    res.status(response.status).json(response.data);
  } catch (err: any) {
    res.status(err.response?.status ?? 500).json(err.response?.data ?? { error: err.message });
  }
});
```

## Output
- Five-tier role system (viewer, analyst, sales_rep, sales_manager, admin)
- Team-scoped API key creation with 90-day expiration
- Express middleware enforcing permissions per endpoint
- Admin audit endpoints for team management and usage reporting
- Apollo API proxy routing all requests through RBAC layer

## Error Handling
| Issue | Resolution |
|-------|------------|
| Missing permissions | Check role matrix; request role upgrade from admin |
| API key expired | Generate new key via admin endpoint |
| Team access denied | Verify team membership in admin panel |
| Role conflict | Higher role takes precedence; admin overrides all |

## Examples

### Set Up RBAC for a Sales Team
```typescript
import { createScopedKey } from './rbac/api-keys';

// Admin creates keys for team members
const repKey = createScopedKey('team-west', 'sales_rep', 'admin@company.com');
const mgrKey = createScopedKey('team-west', 'sales_manager', 'admin@company.com');

console.log(`Sales rep key: ${repKey.key}`);     // Can search + enrich
console.log(`Manager key: ${mgrKey.key}`);        // Can also export PII + manage sequences
```

## Resources
- [RBAC Best Practices (Auth0)](https://auth0.com/docs/manage-users/access-control/rbac)
- [OWASP Access Control](https://owasp.org/www-community/Access_Control)
- [Apollo Team Permissions](https://knowledge.apollo.io/)

## Next Steps
Proceed to `apollo-migration-deep-dive` for migration strategies.
