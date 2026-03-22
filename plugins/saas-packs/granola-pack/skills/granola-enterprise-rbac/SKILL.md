---
name: granola-enterprise-rbac
description: |
  Configure Granola enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Granola.
  Trigger with phrases like "granola SSO", "granola RBAC",
  "granola enterprise", "granola roles", "granola permissions", "granola SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, granola]
---

# Granola Enterprise RBAC

## Overview
Configure enterprise-grade access control for Granola integrations.

## Prerequisites
- Granola Enterprise tier subscription
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
enum GranolaRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface GranolaPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<GranolaRole, GranolaPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: GranolaRole,
  action: keyof GranolaPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Granola SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://granola.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/granola/callback',
};

// Map IdP groups to Granola roles
const groupRoleMapping: Record<string, GranolaRole> = {
  'Engineering': GranolaRole.Developer,
  'Platform-Admins': GranolaRole.Admin,
  'Data-Team': GranolaRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@granola/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.GRANOLA_OAUTH_CLIENT_ID!,
  clientSecret: process.env.GRANOLA_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/granola/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface GranolaOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: GranolaRole;
}

async function createOrganization(
  config: GranolaOrganization
): Promise<void> {
  await granolaClient.organizations.create({
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
function requireGranolaPermission(
  requiredPermission: keyof GranolaPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { granolaRole: GranolaRole };

    if (!checkPermission(user.granolaRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/granola/resource/:id',
  requireGranolaPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface GranolaAuditEntry {
  timestamp: Date;
  userId: string;
  role: GranolaRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logGranolaAccess(entry: GranolaAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Granola permissions.

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
- [Granola Enterprise Guide](https://docs.granola.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `granola-migration-deep-dive`.