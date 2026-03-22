---
name: palantir-enterprise-rbac
description: |
  Configure Palantir enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Palantir.
  Trigger with phrases like "palantir SSO", "palantir RBAC",
  "palantir enterprise", "palantir roles", "palantir permissions", "palantir SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, palantir]
---

# Palantir Enterprise RBAC

## Overview
Configure enterprise-grade access control for Palantir integrations.

## Prerequisites
- Palantir Enterprise tier subscription
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
enum PalantirRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface PalantirPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<PalantirRole, PalantirPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: PalantirRole,
  action: keyof PalantirPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Palantir SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://palantir.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/palantir/callback',
};

// Map IdP groups to Palantir roles
const groupRoleMapping: Record<string, PalantirRole> = {
  'Engineering': PalantirRole.Developer,
  'Platform-Admins': PalantirRole.Admin,
  'Data-Team': PalantirRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@palantir/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.PALANTIR_OAUTH_CLIENT_ID!,
  clientSecret: process.env.PALANTIR_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/palantir/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface PalantirOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: PalantirRole;
}

async function createOrganization(
  config: PalantirOrganization
): Promise<void> {
  await palantirClient.organizations.create({
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
function requirePalantirPermission(
  requiredPermission: keyof PalantirPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { palantirRole: PalantirRole };

    if (!checkPermission(user.palantirRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/palantir/resource/:id',
  requirePalantirPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface PalantirAuditEntry {
  timestamp: Date;
  userId: string;
  role: PalantirRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logPalantirAccess(entry: PalantirAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Palantir permissions.

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
- [Palantir Enterprise Guide](https://docs.palantir.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `palantir-migration-deep-dive`.