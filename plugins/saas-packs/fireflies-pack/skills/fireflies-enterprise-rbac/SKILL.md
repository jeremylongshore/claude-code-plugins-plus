---
name: fireflies-enterprise-rbac
description: |
  Configure Fireflies.ai enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Fireflies.ai.
  Trigger with phrases like "fireflies SSO", "fireflies RBAC",
  "fireflies enterprise", "fireflies roles", "fireflies permissions", "fireflies SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fireflies]
---

# Fireflies.ai Enterprise RBAC

## Overview
Configure enterprise-grade access control for Fireflies.ai integrations.

## Prerequisites
- Fireflies.ai Enterprise tier subscription
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
enum Fireflies.aiRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface Fireflies.aiPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<Fireflies.aiRole, Fireflies.aiPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: Fireflies.aiRole,
  action: keyof Fireflies.aiPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Fireflies.ai SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://fireflies.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/fireflies/callback',
};

// Map IdP groups to Fireflies.ai roles
const groupRoleMapping: Record<string, Fireflies.aiRole> = {
  'Engineering': Fireflies.aiRole.Developer,
  'Platform-Admins': Fireflies.aiRole.Admin,
  'Data-Team': Fireflies.aiRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@fireflies/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.FIREFLIES_OAUTH_CLIENT_ID!,
  clientSecret: process.env.FIREFLIES_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/fireflies/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface Fireflies.aiOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: Fireflies.aiRole;
}

async function createOrganization(
  config: Fireflies.aiOrganization
): Promise<void> {
  await firefliesClient.organizations.create({
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
function requireFireflies.aiPermission(
  requiredPermission: keyof Fireflies.aiPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { firefliesRole: Fireflies.aiRole };

    if (!checkPermission(user.firefliesRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/fireflies/resource/:id',
  requireFireflies.aiPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface Fireflies.aiAuditEntry {
  timestamp: Date;
  userId: string;
  role: Fireflies.aiRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logFireflies.aiAccess(entry: Fireflies.aiAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Fireflies.ai permissions.

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
- [Fireflies.ai Enterprise Guide](https://docs.fireflies.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `fireflies-migration-deep-dive`.