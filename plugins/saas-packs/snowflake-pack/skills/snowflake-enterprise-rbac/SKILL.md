---
name: snowflake-enterprise-rbac
description: |
  Configure Snowflake enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Snowflake.
  Trigger with phrases like "snowflake SSO", "snowflake RBAC",
  "snowflake enterprise", "snowflake roles", "snowflake permissions", "snowflake SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, snowflake]
---

# Snowflake Enterprise RBAC

## Overview
Configure enterprise-grade access control for Snowflake integrations.

## Prerequisites
- Snowflake Enterprise tier subscription
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
enum SnowflakeRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface SnowflakePermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<SnowflakeRole, SnowflakePermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: SnowflakeRole,
  action: keyof SnowflakePermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Snowflake SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://snowflake.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/snowflake/callback',
};

// Map IdP groups to Snowflake roles
const groupRoleMapping: Record<string, SnowflakeRole> = {
  'Engineering': SnowflakeRole.Developer,
  'Platform-Admins': SnowflakeRole.Admin,
  'Data-Team': SnowflakeRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@snowflake/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.SNOWFLAKE_OAUTH_CLIENT_ID!,
  clientSecret: process.env.SNOWFLAKE_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/snowflake/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface SnowflakeOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: SnowflakeRole;
}

async function createOrganization(
  config: SnowflakeOrganization
): Promise<void> {
  await snowflakeClient.organizations.create({
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
function requireSnowflakePermission(
  requiredPermission: keyof SnowflakePermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { snowflakeRole: SnowflakeRole };

    if (!checkPermission(user.snowflakeRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/snowflake/resource/:id',
  requireSnowflakePermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface SnowflakeAuditEntry {
  timestamp: Date;
  userId: string;
  role: SnowflakeRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logSnowflakeAccess(entry: SnowflakeAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Snowflake permissions.

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
- [Snowflake Enterprise Guide](https://docs.snowflake.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `snowflake-migration-deep-dive`.