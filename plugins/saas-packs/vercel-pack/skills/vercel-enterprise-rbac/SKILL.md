---
name: vercel-enterprise-rbac
description: |
  Configure Vercel enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Vercel.
  Trigger with phrases like "vercel SSO", "vercel RBAC",
  "vercel enterprise", "vercel roles", "vercel permissions", "vercel SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Enterprise RBAC

## Overview
Configure enterprise-grade access control for Vercel integrations.

## Prerequisites
- Vercel Enterprise tier subscription
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
enum VercelRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface VercelPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<VercelRole, VercelPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: VercelRole,
  action: keyof VercelPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Vercel SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://vercel.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/vercel/callback',
};

// Map IdP groups to Vercel roles
const groupRoleMapping: Record<string, VercelRole> = {
  'Engineering': VercelRole.Developer,
  'Platform-Admins': VercelRole.Admin,
  'Data-Team': VercelRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from 'vercel';

const oauthClient = new OAuth2Client({
  clientId: process.env.VERCEL_OAUTH_CLIENT_ID!,
  clientSecret: process.env.VERCEL_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/vercel/callback',
  scopes: read, write, deploy,
});
```

## Organization Management

```typescript
interface VercelOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: VercelRole;
}

async function createOrganization(
  config: VercelOrganization
): Promise<void> {
  await vercelClient.organizations.create({
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
function requireVercelPermission(
  requiredPermission: keyof VercelPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { vercelRole: VercelRole };

    if (!checkPermission(user.vercelRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/vercel/resource/:id',
  requireVercelPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface VercelAuditEntry {
  timestamp: Date;
  userId: string;
  role: VercelRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logVercelAccess(entry: VercelAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Vercel permissions.

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
- [Vercel Enterprise Guide](https://vercel.com/docs/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `vercel-migration-deep-dive`.