---
name: intercom-enterprise-rbac
description: |
  Configure Intercom enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Intercom.
  Trigger with phrases like "intercom SSO", "intercom RBAC",
  "intercom enterprise", "intercom roles", "intercom permissions", "intercom SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, intercom]
---

# Intercom Enterprise RBAC

## Overview
Configure enterprise-grade access control for Intercom integrations.

## Prerequisites
- Intercom Enterprise tier subscription
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
enum IntercomRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface IntercomPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<IntercomRole, IntercomPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: IntercomRole,
  action: keyof IntercomPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Intercom SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://intercom.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/intercom/callback',
};

// Map IdP groups to Intercom roles
const groupRoleMapping: Record<string, IntercomRole> = {
  'Engineering': IntercomRole.Developer,
  'Platform-Admins': IntercomRole.Admin,
  'Data-Team': IntercomRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@intercom/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.INTERCOM_OAUTH_CLIENT_ID!,
  clientSecret: process.env.INTERCOM_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/intercom/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface IntercomOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: IntercomRole;
}

async function createOrganization(
  config: IntercomOrganization
): Promise<void> {
  await intercomClient.organizations.create({
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
function requireIntercomPermission(
  requiredPermission: keyof IntercomPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { intercomRole: IntercomRole };

    if (!checkPermission(user.intercomRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/intercom/resource/:id',
  requireIntercomPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface IntercomAuditEntry {
  timestamp: Date;
  userId: string;
  role: IntercomRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logIntercomAccess(entry: IntercomAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Intercom permissions.

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
- [Intercom Enterprise Guide](https://docs.intercom.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `intercom-migration-deep-dive`.