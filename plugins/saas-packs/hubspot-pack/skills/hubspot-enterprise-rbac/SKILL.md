---
name: hubspot-enterprise-rbac
description: |
  Configure HubSpot enterprise access control with OAuth scopes and team permissions.
  Use when implementing role-based access, configuring per-team HubSpot scopes,
  or setting up multi-user access patterns for HubSpot integrations.
  Trigger with phrases like "hubspot RBAC", "hubspot roles",
  "hubspot enterprise", "hubspot permissions", "hubspot team access", "hubspot OAuth scopes".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Enterprise RBAC

## Overview

Implement role-based access control for HubSpot integrations using OAuth scopes, multiple private apps with different permissions, and application-level authorization.

## Prerequisites

- HubSpot Enterprise subscription (for team-level permissions)
- Understanding of HubSpot OAuth scopes
- Multiple private apps or OAuth app configured

## Instructions

### Step 1: Scope-Based Access Model

HubSpot's permission model is scope-based. Create separate private apps for different access levels:

| Role | Private App | Scopes | Use Case |
|------|-----------|--------|----------|
| Reader | `hubspot-readonly` | `crm.objects.contacts.read`, `crm.objects.deals.read`, `crm.objects.companies.read` | Dashboards, reports |
| Writer | `hubspot-readwrite` | Above + `.write` variants | CRM operations |
| Admin | `hubspot-admin` | All CRM scopes + `crm.schemas.*.read` | Schema management |
| Sync | `hubspot-sync` | `crm.objects.contacts.read`, `crm.objects.contacts.write`, `crm.import` | Data sync jobs |
| Webhook | `hubspot-webhook` | `automation` | Event handling only |

### Step 2: Multi-Token Client Factory

```typescript
import * as hubspot from '@hubspot/api-client';

type AccessLevel = 'reader' | 'writer' | 'admin' | 'sync';

const TOKEN_MAP: Record<AccessLevel, string> = {
  reader: process.env.HUBSPOT_READER_TOKEN!,
  writer: process.env.HUBSPOT_WRITER_TOKEN!,
  admin: process.env.HUBSPOT_ADMIN_TOKEN!,
  sync: process.env.HUBSPOT_SYNC_TOKEN!,
};

const clientCache = new Map<AccessLevel, hubspot.Client>();

export function getClientForRole(role: AccessLevel): hubspot.Client {
  if (!clientCache.has(role)) {
    const token = TOKEN_MAP[role];
    if (!token) {
      throw new Error(`No token configured for role: ${role}`);
    }
    clientCache.set(role, new hubspot.Client({
      accessToken: token,
      numberOfApiCallRetries: 3,
    }));
  }
  return clientCache.get(role)!;
}

// Usage
const readClient = getClientForRole('reader'); // can only read
const writeClient = getClientForRole('writer'); // can read and write
```

### Step 3: Application-Level Permission Middleware

```typescript
import { Request, Response, NextFunction } from 'express';

interface AppPermissions {
  contacts: { read: boolean; write: boolean; delete: boolean };
  deals: { read: boolean; write: boolean; delete: boolean };
  companies: { read: boolean; write: boolean; delete: boolean };
}

const ROLE_PERMISSIONS: Record<string, AppPermissions> = {
  sales_rep: {
    contacts: { read: true, write: true, delete: false },
    deals: { read: true, write: true, delete: false },
    companies: { read: true, write: false, delete: false },
  },
  marketing: {
    contacts: { read: true, write: true, delete: false },
    deals: { read: true, write: false, delete: false },
    companies: { read: true, write: false, delete: false },
  },
  admin: {
    contacts: { read: true, write: true, delete: true },
    deals: { read: true, write: true, delete: true },
    companies: { read: true, write: true, delete: true },
  },
  readonly: {
    contacts: { read: true, write: false, delete: false },
    deals: { read: true, write: false, delete: false },
    companies: { read: true, write: false, delete: false },
  },
};

function requirePermission(
  objectType: keyof AppPermissions,
  action: 'read' | 'write' | 'delete'
) {
  return (req: Request, res: Response, next: NextFunction) => {
    const userRole = req.user?.role || 'readonly';
    const permissions = ROLE_PERMISSIONS[userRole];

    if (!permissions || !permissions[objectType]?.[action]) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Role "${userRole}" lacks ${action} permission for ${objectType}`,
      });
    }
    next();
  };
}

// Usage
app.get('/api/contacts', requirePermission('contacts', 'read'), listContacts);
app.post('/api/contacts', requirePermission('contacts', 'write'), createContact);
app.delete('/api/contacts/:id', requirePermission('contacts', 'delete'), deleteContact);
```

### Step 4: OAuth 2.0 for Multi-Portal Access

```typescript
// For public apps accessing multiple HubSpot portals
interface PortalCredentials {
  portalId: string;
  accessToken: string;
  refreshToken: string;
  expiresAt: Date;
}

class MultiPortalManager {
  private credentials = new Map<string, PortalCredentials>();

  async getClient(portalId: string): Promise<hubspot.Client> {
    let creds = this.credentials.get(portalId);

    if (!creds) {
      throw new Error(`No credentials for portal ${portalId}. User must authorize.`);
    }

    // Refresh token if expired
    if (new Date() >= creds.expiresAt) {
      creds = await this.refreshToken(creds);
      this.credentials.set(portalId, creds);
    }

    return new hubspot.Client({ accessToken: creds.accessToken });
  }

  private async refreshToken(creds: PortalCredentials): Promise<PortalCredentials> {
    const tempClient = new hubspot.Client();
    const response = await tempClient.oauth.tokensApi.create(
      'refresh_token',
      undefined, undefined,
      process.env.HUBSPOT_CLIENT_ID!,
      process.env.HUBSPOT_CLIENT_SECRET!,
      creds.refreshToken
    );

    return {
      ...creds,
      accessToken: response.accessToken,
      refreshToken: response.refreshToken,
      expiresAt: new Date(Date.now() + response.expiresIn * 1000),
    };
  }
}
```

### Step 5: Audit Trail

```typescript
interface HubSpotAuditEntry {
  timestamp: string;
  userId: string;
  role: string;
  action: string;
  objectType: string;
  objectId: string;
  success: boolean;
  hubspotCorrelationId?: string;
}

async function auditHubSpotAction(
  userId: string, role: string, action: string,
  objectType: string, objectId: string, success: boolean,
  correlationId?: string
): Promise<void> {
  const entry: HubSpotAuditEntry = {
    timestamp: new Date().toISOString(),
    userId, role, action, objectType, objectId, success,
    hubspotCorrelationId: correlationId,
  };

  // Store in your audit database
  await db.auditLog.insert(entry);

  // Alert on suspicious activity
  if (!success && action === 'delete') {
    console.warn('Failed delete attempt:', { userId, role, objectType, objectId });
  }
}
```

## Output

- Scope-based access model with separate private apps per role
- Multi-token client factory for role-based HubSpot access
- Application-level permission middleware
- Multi-portal OAuth management for public apps
- Audit trail for all HubSpot operations

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `403 MISSING_SCOPES` | Token lacks required scope | Use the correct role's token |
| Permission denied in app | User role too restrictive | Check ROLE_PERMISSIONS mapping |
| Token refresh fails | Client secret changed | Update client secret in env |
| Audit gaps | Async logging failed | Add retry to audit log writes |

## Resources

- [HubSpot OAuth Scopes](https://developers.hubspot.com/docs/guides/apps/authentication/scopes)
- [Private Apps Guide](https://developers.hubspot.com/docs/guides/apps/private-apps/overview)
- [HubSpot Teams & Permissions](https://knowledge.hubspot.com/account/hubspot-user-permissions-guide)

## Next Steps

For major migrations, see `hubspot-migration-deep-dive`.
