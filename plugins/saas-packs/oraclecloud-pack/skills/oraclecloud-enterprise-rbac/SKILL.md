---
name: oraclecloud-enterprise-rbac
description: |
  Configure Oracle Cloud enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Oracle Cloud.
  Trigger with phrases like "oraclecloud SSO", "oraclecloud RBAC",
  "oraclecloud enterprise", "oraclecloud roles", "oraclecloud permissions", "oraclecloud SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, oraclecloud]
---

# Oracle Cloud Enterprise RBAC

## Overview
Configure enterprise-grade access control for Oracle Cloud integrations.

## Prerequisites
- Oracle Cloud Enterprise tier subscription
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
enum Oracle CloudRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface Oracle CloudPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<Oracle CloudRole, Oracle CloudPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: Oracle CloudRole,
  action: keyof Oracle CloudPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Oracle Cloud SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://oraclecloud.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/oraclecloud/callback',
};

// Map IdP groups to Oracle Cloud roles
const groupRoleMapping: Record<string, Oracle CloudRole> = {
  'Engineering': Oracle CloudRole.Developer,
  'Platform-Admins': Oracle CloudRole.Admin,
  'Data-Team': Oracle CloudRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@oraclecloud/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.ORACLECLOUD_OAUTH_CLIENT_ID!,
  clientSecret: process.env.ORACLECLOUD_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/oraclecloud/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface Oracle CloudOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: Oracle CloudRole;
}

async function createOrganization(
  config: Oracle CloudOrganization
): Promise<void> {
  await oraclecloudClient.organizations.create({
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
function requireOracle CloudPermission(
  requiredPermission: keyof Oracle CloudPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { oraclecloudRole: Oracle CloudRole };

    if (!checkPermission(user.oraclecloudRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/oraclecloud/resource/:id',
  requireOracle CloudPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface Oracle CloudAuditEntry {
  timestamp: Date;
  userId: string;
  role: Oracle CloudRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logOracle CloudAccess(entry: Oracle CloudAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Oracle Cloud permissions.

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
- [Oracle Cloud Enterprise Guide](https://docs.oraclecloud.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `oraclecloud-migration-deep-dive`.