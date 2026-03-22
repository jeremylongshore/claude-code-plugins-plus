---
name: salesforce-enterprise-rbac
description: |
  Configure Salesforce enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Salesforce.
  Trigger with phrases like "salesforce SSO", "salesforce RBAC",
  "salesforce enterprise", "salesforce roles", "salesforce permissions", "salesforce SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesforce]
---

# Salesforce Enterprise RBAC

## Overview
Configure enterprise-grade access control for Salesforce integrations.

## Prerequisites
- Salesforce Enterprise tier subscription
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
enum SalesforceRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface SalesforcePermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<SalesforceRole, SalesforcePermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: SalesforceRole,
  action: keyof SalesforcePermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Salesforce SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://salesforce.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/salesforce/callback',
};

// Map IdP groups to Salesforce roles
const groupRoleMapping: Record<string, SalesforceRole> = {
  'Engineering': SalesforceRole.Developer,
  'Platform-Admins': SalesforceRole.Admin,
  'Data-Team': SalesforceRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@salesforce/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.SALESFORCE_OAUTH_CLIENT_ID!,
  clientSecret: process.env.SALESFORCE_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/salesforce/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface SalesforceOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: SalesforceRole;
}

async function createOrganization(
  config: SalesforceOrganization
): Promise<void> {
  await salesforceClient.organizations.create({
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
function requireSalesforcePermission(
  requiredPermission: keyof SalesforcePermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { salesforceRole: SalesforceRole };

    if (!checkPermission(user.salesforceRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/salesforce/resource/:id',
  requireSalesforcePermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface SalesforceAuditEntry {
  timestamp: Date;
  userId: string;
  role: SalesforceRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logSalesforceAccess(entry: SalesforceAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Salesforce permissions.

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
- [Salesforce Enterprise Guide](https://docs.salesforce.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `salesforce-migration-deep-dive`.