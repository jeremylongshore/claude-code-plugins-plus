---
name: clay-enterprise-rbac
description: |
  Configure Clay enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Clay.
  Trigger with phrases like "clay SSO", "clay RBAC",
  "clay enterprise", "clay roles", "clay permissions", "clay SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clay]
---

# Clay Enterprise RBAC

## Overview
Configure enterprise-grade access control for Clay integrations.

## Prerequisites
- Clay Enterprise tier subscription
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
enum ClayRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface ClayPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<ClayRole, ClayPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: ClayRole,
  action: keyof ClayPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Clay SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://clay.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/clay/callback',
};

// Map IdP groups to Clay roles
const groupRoleMapping: Record<string, ClayRole> = {
  'Engineering': ClayRole.Developer,
  'Platform-Admins': ClayRole.Admin,
  'Data-Team': ClayRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@clay/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.CLAY_OAUTH_CLIENT_ID!,
  clientSecret: process.env.CLAY_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/clay/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface ClayOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: ClayRole;
}

async function createOrganization(
  config: ClayOrganization
): Promise<void> {
  await clayClient.organizations.create({
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
function requireClayPermission(
  requiredPermission: keyof ClayPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { clayRole: ClayRole };

    if (!checkPermission(user.clayRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/clay/resource/:id',
  requireClayPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface ClayAuditEntry {
  timestamp: Date;
  userId: string;
  role: ClayRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logClayAccess(entry: ClayAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Clay permissions.

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
- [Clay Enterprise Guide](https://docs.clay.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `clay-migration-deep-dive`.