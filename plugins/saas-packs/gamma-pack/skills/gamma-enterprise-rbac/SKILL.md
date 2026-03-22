---
name: gamma-enterprise-rbac
description: |
  Configure Gamma enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Gamma.
  Trigger with phrases like "gamma SSO", "gamma RBAC",
  "gamma enterprise", "gamma roles", "gamma permissions", "gamma SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, gamma]
---

# Gamma Enterprise RBAC

## Overview
Configure enterprise-grade access control for Gamma integrations.

## Prerequisites
- Gamma Enterprise tier subscription
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
enum GammaRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface GammaPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<GammaRole, GammaPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: GammaRole,
  action: keyof GammaPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Gamma SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://gamma.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/gamma/callback',
};

// Map IdP groups to Gamma roles
const groupRoleMapping: Record<string, GammaRole> = {
  'Engineering': GammaRole.Developer,
  'Platform-Admins': GammaRole.Admin,
  'Data-Team': GammaRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@gamma/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.GAMMA_OAUTH_CLIENT_ID!,
  clientSecret: process.env.GAMMA_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/gamma/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface GammaOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: GammaRole;
}

async function createOrganization(
  config: GammaOrganization
): Promise<void> {
  await gammaClient.organizations.create({
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
function requireGammaPermission(
  requiredPermission: keyof GammaPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { gammaRole: GammaRole };

    if (!checkPermission(user.gammaRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/gamma/resource/:id',
  requireGammaPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface GammaAuditEntry {
  timestamp: Date;
  userId: string;
  role: GammaRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logGammaAccess(entry: GammaAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Gamma permissions.

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
- [Gamma Enterprise Guide](https://docs.gamma.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `gamma-migration-deep-dive`.