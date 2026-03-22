---
name: clickhouse-enterprise-rbac
description: |
  Configure ClickHouse enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for ClickHouse.
  Trigger with phrases like "clickhouse SSO", "clickhouse RBAC",
  "clickhouse enterprise", "clickhouse roles", "clickhouse permissions", "clickhouse SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickhouse]
---

# ClickHouse Enterprise RBAC

## Overview
Configure enterprise-grade access control for ClickHouse integrations.

## Prerequisites
- ClickHouse Enterprise tier subscription
- Identity Provider (IdP) with SAML/OIDC support
- Understanding of role-based access patterns
- Audit logging infrastructure

## Role Definitions

| Role | Permissions | Use Case |
|------|-------------|----------|
| Admin | Full access | Platform administrators |
| Developer | Read/write, no delete | Active development |
| Viewer | Read-only | Stakeholders, auditors |
| Service | API access only | Automated systems |

## Role Implementation

```typescript
enum ClickHouseRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface ClickHousePermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<ClickHouseRole, ClickHousePermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: ClickHouseRole,
  action: keyof ClickHousePermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// ClickHouse SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://clickhouse.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/clickhouse/callback',
};

// Map IdP groups to ClickHouse roles
const groupRoleMapping: Record<string, ClickHouseRole> = {
  'Engineering': ClickHouseRole.Developer,
  'Platform-Admins': ClickHouseRole.Admin,
  'Data-Team': ClickHouseRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@clickhouse/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.CLICKHOUSE_OAUTH_CLIENT_ID!,
  clientSecret: process.env.CLICKHOUSE_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/clickhouse/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface ClickHouseOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: ClickHouseRole;
}

async function createOrganization(
  config: ClickHouseOrganization
): Promise<void> {
  await clickhouseClient.organizations.create({
    ...config,
    settings: {
      sso: {
        enabled: config.ssoEnabled,
        enforced: config.enforceSso,
        domains: config.allowedDomains,
      },
    },
  });
}
```

## Access Control Middleware

```typescript
function requireClickHousePermission(
  requiredPermission: keyof ClickHousePermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { clickhouseRole: ClickHouseRole };

    if (!checkPermission(user.clickhouseRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/clickhouse/resource/:id',
  requireClickHousePermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface ClickHouseAuditEntry {
  timestamp: Date;
  userId: string;
  role: ClickHouseRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logClickHouseAccess(entry: ClickHouseAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to ClickHouse permissions.

### Step 2: Configure SSO
Set up SAML or OIDC integration with your IdP.

### Step 3: Implement Middleware
Add permission checks to API endpoints.

### Step 4: Enable Audit Logging
Track all access for compliance.

## Output
- Role definitions implemented
- SSO integration configured
- Permission middleware active
- Audit trail enabled

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| SSO login fails | Wrong callback URL | Verify IdP config |
| Permission denied | Missing role mapping | Update group mappings |
| Token expired | Short TTL | Refresh token logic |
| Audit gaps | Async logging failed | Check log pipeline |

## Examples

### Quick Permission Check
```typescript
if (!checkPermission(user.role, 'write')) {
  throw new ForbiddenError('Write permission required');
}
```

## Resources
- [ClickHouse Enterprise Guide](https://docs.clickhouse.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `clickhouse-migration-deep-dive`.