---
name: guidewire-enterprise-rbac
description: |
  Configure Guidewire enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Guidewire.
  Trigger with phrases like "guidewire SSO", "guidewire RBAC",
  "guidewire enterprise", "guidewire roles", "guidewire permissions", "guidewire SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, guidewire]
---

# Guidewire Enterprise RBAC

## Overview
Configure enterprise-grade access control for Guidewire integrations.

## Prerequisites
- Guidewire Enterprise tier subscription
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
enum GuidewireRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface GuidewirePermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<GuidewireRole, GuidewirePermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: GuidewireRole,
  action: keyof GuidewirePermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Guidewire SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://guidewire.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/guidewire/callback',
};

// Map IdP groups to Guidewire roles
const groupRoleMapping: Record<string, GuidewireRole> = {
  'Engineering': GuidewireRole.Developer,
  'Platform-Admins': GuidewireRole.Admin,
  'Data-Team': GuidewireRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@guidewire/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.GUIDEWIRE_OAUTH_CLIENT_ID!,
  clientSecret: process.env.GUIDEWIRE_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/guidewire/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface GuidewireOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: GuidewireRole;
}

async function createOrganization(
  config: GuidewireOrganization
): Promise<void> {
  await guidewireClient.organizations.create({
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
function requireGuidewirePermission(
  requiredPermission: keyof GuidewirePermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { guidewireRole: GuidewireRole };

    if (!checkPermission(user.guidewireRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/guidewire/resource/:id',
  requireGuidewirePermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface GuidewireAuditEntry {
  timestamp: Date;
  userId: string;
  role: GuidewireRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logGuidewireAccess(entry: GuidewireAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Guidewire permissions.

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
- [Guidewire Enterprise Guide](https://docs.guidewire.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `guidewire-migration-deep-dive`.