---
name: klingai-enterprise-rbac
description: |
  Configure Kling AI enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Kling AI.
  Trigger with phrases like "klingai SSO", "klingai RBAC",
  "klingai enterprise", "klingai roles", "klingai permissions", "klingai SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klingai]
---

# Kling AI Enterprise RBAC

## Overview
Configure enterprise-grade access control for Kling AI integrations.

## Prerequisites
- Kling AI Enterprise tier subscription
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
enum Kling AIRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface Kling AIPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<Kling AIRole, Kling AIPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: Kling AIRole,
  action: keyof Kling AIPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Kling AI SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://klingai.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/klingai/callback',
};

// Map IdP groups to Kling AI roles
const groupRoleMapping: Record<string, Kling AIRole> = {
  'Engineering': Kling AIRole.Developer,
  'Platform-Admins': Kling AIRole.Admin,
  'Data-Team': Kling AIRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@klingai/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.KLINGAI_OAUTH_CLIENT_ID!,
  clientSecret: process.env.KLINGAI_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/klingai/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface Kling AIOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: Kling AIRole;
}

async function createOrganization(
  config: Kling AIOrganization
): Promise<void> {
  await klingaiClient.organizations.create({
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
function requireKling AIPermission(
  requiredPermission: keyof Kling AIPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { klingaiRole: Kling AIRole };

    if (!checkPermission(user.klingaiRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/klingai/resource/:id',
  requireKling AIPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface Kling AIAuditEntry {
  timestamp: Date;
  userId: string;
  role: Kling AIRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logKling AIAccess(entry: Kling AIAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Kling AI permissions.

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
- [Kling AI Enterprise Guide](https://docs.klingai.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `klingai-migration-deep-dive`.