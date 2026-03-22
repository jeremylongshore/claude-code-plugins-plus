---
name: databricks-enterprise-rbac
description: |
  Configure Databricks enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Databricks.
  Trigger with phrases like "databricks SSO", "databricks RBAC",
  "databricks enterprise", "databricks roles", "databricks permissions", "databricks SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, databricks]
---

# Databricks Enterprise RBAC

## Overview
Configure enterprise-grade access control for Databricks integrations.

## Prerequisites
- Databricks Enterprise tier subscription
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
enum DatabricksRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface DatabricksPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<DatabricksRole, DatabricksPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: DatabricksRole,
  action: keyof DatabricksPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Databricks SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://databricks.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/databricks/callback',
};

// Map IdP groups to Databricks roles
const groupRoleMapping: Record<string, DatabricksRole> = {
  'Engineering': DatabricksRole.Developer,
  'Platform-Admins': DatabricksRole.Admin,
  'Data-Team': DatabricksRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@databricks/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.DATABRICKS_OAUTH_CLIENT_ID!,
  clientSecret: process.env.DATABRICKS_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/databricks/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface DatabricksOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: DatabricksRole;
}

async function createOrganization(
  config: DatabricksOrganization
): Promise<void> {
  await databricksClient.organizations.create({
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
function requireDatabricksPermission(
  requiredPermission: keyof DatabricksPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { databricksRole: DatabricksRole };

    if (!checkPermission(user.databricksRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/databricks/resource/:id',
  requireDatabricksPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface DatabricksAuditEntry {
  timestamp: Date;
  userId: string;
  role: DatabricksRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logDatabricksAccess(entry: DatabricksAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Databricks permissions.

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
- [Databricks Enterprise Guide](https://docs.databricks.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `databricks-migration-deep-dive`.