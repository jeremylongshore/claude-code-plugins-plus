---
name: lindy-enterprise-rbac
description: |
  Configure Lindy enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Lindy.
  Trigger with phrases like "lindy SSO", "lindy RBAC",
  "lindy enterprise", "lindy roles", "lindy permissions", "lindy SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lindy]
---

# Lindy Enterprise RBAC

## Overview
Configure enterprise-grade access control for Lindy integrations.

## Prerequisites
- Lindy Enterprise tier subscription
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
enum LindyRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface LindyPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<LindyRole, LindyPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: LindyRole,
  action: keyof LindyPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Lindy SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://lindy.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/lindy/callback',
};

// Map IdP groups to Lindy roles
const groupRoleMapping: Record<string, LindyRole> = {
  'Engineering': LindyRole.Developer,
  'Platform-Admins': LindyRole.Admin,
  'Data-Team': LindyRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@lindy/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.LINDY_OAUTH_CLIENT_ID!,
  clientSecret: process.env.LINDY_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/lindy/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface LindyOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: LindyRole;
}

async function createOrganization(
  config: LindyOrganization
): Promise<void> {
  await lindyClient.organizations.create({
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
function requireLindyPermission(
  requiredPermission: keyof LindyPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { lindyRole: LindyRole };

    if (!checkPermission(user.lindyRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/lindy/resource/:id',
  requireLindyPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface LindyAuditEntry {
  timestamp: Date;
  userId: string;
  role: LindyRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logLindyAccess(entry: LindyAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Lindy permissions.

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
- [Lindy Enterprise Guide](https://docs.lindy.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `lindy-migration-deep-dive`.