---
name: vastai-enterprise-rbac
description: |
  Configure Vast.ai enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Vast.ai.
  Trigger with phrases like "vastai SSO", "vastai RBAC",
  "vastai enterprise", "vastai roles", "vastai permissions", "vastai SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, vastai]
---

# Vast.ai Enterprise RBAC

## Overview
Configure enterprise-grade access control for Vast.ai integrations.

## Prerequisites
- Vast.ai Enterprise tier subscription
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
enum Vast.aiRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface Vast.aiPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<Vast.aiRole, Vast.aiPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: Vast.aiRole,
  action: keyof Vast.aiPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Vast.ai SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://vastai.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/vastai/callback',
};

// Map IdP groups to Vast.ai roles
const groupRoleMapping: Record<string, Vast.aiRole> = {
  'Engineering': Vast.aiRole.Developer,
  'Platform-Admins': Vast.aiRole.Admin,
  'Data-Team': Vast.aiRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@vastai/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.VASTAI_OAUTH_CLIENT_ID!,
  clientSecret: process.env.VASTAI_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/vastai/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface Vast.aiOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: Vast.aiRole;
}

async function createOrganization(
  config: Vast.aiOrganization
): Promise<void> {
  await vastaiClient.organizations.create({
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
function requireVast.aiPermission(
  requiredPermission: keyof Vast.aiPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { vastaiRole: Vast.aiRole };

    if (!checkPermission(user.vastaiRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/vastai/resource/:id',
  requireVast.aiPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface Vast.aiAuditEntry {
  timestamp: Date;
  userId: string;
  role: Vast.aiRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logVast.aiAccess(entry: Vast.aiAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Vast.ai permissions.

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
- [Vast.ai Enterprise Guide](https://docs.vastai.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `vastai-migration-deep-dive`.