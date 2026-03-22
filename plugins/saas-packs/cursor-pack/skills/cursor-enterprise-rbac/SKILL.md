---
name: cursor-enterprise-rbac
description: |
  Configure Cursor enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Cursor.
  Trigger with phrases like "cursor SSO", "cursor RBAC",
  "cursor enterprise", "cursor roles", "cursor permissions", "cursor SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cursor]
---

# Cursor Enterprise RBAC

## Overview
Configure enterprise-grade access control for Cursor integrations.

## Prerequisites
- Cursor Enterprise tier subscription
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
enum CursorRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface CursorPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<CursorRole, CursorPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: CursorRole,
  action: keyof CursorPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Cursor SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://cursor.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/cursor/callback',
};

// Map IdP groups to Cursor roles
const groupRoleMapping: Record<string, CursorRole> = {
  'Engineering': CursorRole.Developer,
  'Platform-Admins': CursorRole.Admin,
  'Data-Team': CursorRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@cursor/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.CURSOR_OAUTH_CLIENT_ID!,
  clientSecret: process.env.CURSOR_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/cursor/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface CursorOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: CursorRole;
}

async function createOrganization(
  config: CursorOrganization
): Promise<void> {
  await cursorClient.organizations.create({
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
function requireCursorPermission(
  requiredPermission: keyof CursorPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { cursorRole: CursorRole };

    if (!checkPermission(user.cursorRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/cursor/resource/:id',
  requireCursorPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface CursorAuditEntry {
  timestamp: Date;
  userId: string;
  role: CursorRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logCursorAccess(entry: CursorAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Cursor permissions.

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
- [Cursor Enterprise Guide](https://docs.cursor.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `cursor-migration-deep-dive`.