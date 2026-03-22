---
name: flexport-enterprise-rbac
description: |
  Configure role-based access control for Flexport integrations with scoped API keys,
  multi-tenant patterns, and organization-level permission management.
  Trigger: "flexport RBAC", "flexport permissions", "flexport multi-tenant", "flexport access control".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Enterprise RBAC

## Overview

Implement role-based access control for Flexport integrations. Since Flexport API keys are scoped at the account level, RBAC is implemented in your application layer with per-role API key allocation and request filtering.

## Instructions

### Step 1: Define Roles

| Role | API Key Scope | Allowed Endpoints | Use Case |
|------|--------------|-------------------|----------|
| Viewer | Read-only | `GET /shipments`, `GET /products` | Dashboard users |
| Operator | Read-write | `GET/POST /bookings`, `GET/PATCH /purchase_orders` | Ops team |
| Finance | Read invoices | `GET /freight_invoices`, `GET /commercial_invoices` | Finance team |
| Admin | Full access | All endpoints | System administrators |

### Step 2: Application-Layer RBAC

```typescript
type Role = 'viewer' | 'operator' | 'finance' | 'admin';

const ROLE_PERMISSIONS: Record<Role, { methods: string[]; paths: RegExp[] }> = {
  viewer: {
    methods: ['GET'],
    paths: [/^\/shipments/, /^\/products/, /^\/purchase_orders/],
  },
  operator: {
    methods: ['GET', 'POST', 'PATCH'],
    paths: [/^\/shipments/, /^\/bookings/, /^\/purchase_orders/, /^\/products/],
  },
  finance: {
    methods: ['GET'],
    paths: [/^\/freight_invoices/, /^\/commercial_invoices/, /^\/shipments/],
  },
  admin: {
    methods: ['GET', 'POST', 'PATCH', 'DELETE'],
    paths: [/.*/],
  },
};

function checkPermission(role: Role, method: string, path: string): boolean {
  const perms = ROLE_PERMISSIONS[role];
  return perms.methods.includes(method) && perms.paths.some(p => p.test(path));
}

// Middleware
function rbacMiddleware(role: Role) {
  return (req: Request, res: Response, next: NextFunction) => {
    const flexportPath = req.params.flexportPath;
    if (!checkPermission(role, req.method, `/${flexportPath}`)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    next();
  };
}
```

### Step 3: Multi-Tenant API Key Management

```typescript
// Each tenant/team gets their own Flexport API key
interface TenantConfig {
  tenantId: string;
  flexportApiKey: string;
  role: Role;
  allowedShipmentPrefixes?: string[];  // Filter visible data
}

class MultiTenantFlexport {
  private configs: Map<string, TenantConfig>;

  async request(tenantId: string, path: string, options: RequestInit = {}) {
    const config = this.configs.get(tenantId);
    if (!config) throw new Error('Unknown tenant');
    if (!checkPermission(config.role, options.method || 'GET', path)) {
      throw new Error('Permission denied');
    }
    return fetch(`https://api.flexport.com${path}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${config.flexportApiKey}`,
        'Flexport-Version': '2',
        'Content-Type': 'application/json',
      },
    }).then(r => r.json());
  }
}
```

### Step 4: Audit Logging

```typescript
async function auditLog(entry: {
  userId: string;
  role: Role;
  action: string;
  resource: string;
  result: 'allowed' | 'denied';
}) {
  await db.auditLogs.create({
    data: { ...entry, timestamp: new Date(), ip: req.ip },
  });
  logger.info(entry, 'RBAC audit');
}
```

## Resources

- [Flexport Developer Portal](https://developers.flexport.com/)
- [Flexport API Credentials](https://developers.flexport.com/tutorials/using-api-credentials/)

## Next Steps

For migration strategies, see `flexport-migration-deep-dive`.
