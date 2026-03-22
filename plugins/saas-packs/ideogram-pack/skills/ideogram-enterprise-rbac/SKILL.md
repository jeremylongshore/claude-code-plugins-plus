---
name: ideogram-enterprise-rbac
description: |
  Configure Ideogram enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Ideogram.
  Trigger with phrases like "ideogram SSO", "ideogram RBAC",
  "ideogram enterprise", "ideogram roles", "ideogram permissions", "ideogram SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, ideogram]
---

# Ideogram Enterprise RBAC

## Overview
Configure enterprise-grade access control for Ideogram integrations.

## Prerequisites
- Ideogram Enterprise tier subscription
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
enum IdeogramRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface IdeogramPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<IdeogramRole, IdeogramPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: IdeogramRole,
  action: keyof IdeogramPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Ideogram SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://ideogram.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/ideogram/callback',
};

// Map IdP groups to Ideogram roles
const groupRoleMapping: Record<string, IdeogramRole> = {
  'Engineering': IdeogramRole.Developer,
  'Platform-Admins': IdeogramRole.Admin,
  'Data-Team': IdeogramRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@ideogram/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.IDEOGRAM_OAUTH_CLIENT_ID!,
  clientSecret: process.env.IDEOGRAM_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/ideogram/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface IdeogramOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: IdeogramRole;
}

async function createOrganization(
  config: IdeogramOrganization
): Promise<void> {
  await ideogramClient.organizations.create({
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
function requireIdeogramPermission(
  requiredPermission: keyof IdeogramPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { ideogramRole: IdeogramRole };

    if (!checkPermission(user.ideogramRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/ideogram/resource/:id',
  requireIdeogramPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface IdeogramAuditEntry {
  timestamp: Date;
  userId: string;
  role: IdeogramRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logIdeogramAccess(entry: IdeogramAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Ideogram permissions.

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
- [Ideogram Enterprise Guide](https://docs.ideogram.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `ideogram-migration-deep-dive`.