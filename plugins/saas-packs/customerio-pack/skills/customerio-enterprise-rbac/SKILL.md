---
name: customerio-enterprise-rbac
description: |
  Configure Customer.io enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Customer.io.
  Trigger with phrases like "customerio SSO", "customerio RBAC",
  "customerio enterprise", "customerio roles", "customerio permissions", "customerio SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, customerio]
---

# Customer.io Enterprise RBAC

## Overview
Configure enterprise-grade access control for Customer.io integrations.

## Prerequisites
- Customer.io Enterprise tier subscription
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
enum Customer.ioRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface Customer.ioPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<Customer.ioRole, Customer.ioPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: Customer.ioRole,
  action: keyof Customer.ioPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Customer.io SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://customerio.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/customerio/callback',
};

// Map IdP groups to Customer.io roles
const groupRoleMapping: Record<string, Customer.ioRole> = {
  'Engineering': Customer.ioRole.Developer,
  'Platform-Admins': Customer.ioRole.Admin,
  'Data-Team': Customer.ioRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@customerio/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.CUSTOMERIO_OAUTH_CLIENT_ID!,
  clientSecret: process.env.CUSTOMERIO_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/customerio/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface Customer.ioOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: Customer.ioRole;
}

async function createOrganization(
  config: Customer.ioOrganization
): Promise<void> {
  await customerioClient.organizations.create({
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
function requireCustomer.ioPermission(
  requiredPermission: keyof Customer.ioPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { customerioRole: Customer.ioRole };

    if (!checkPermission(user.customerioRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/customerio/resource/:id',
  requireCustomer.ioPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface Customer.ioAuditEntry {
  timestamp: Date;
  userId: string;
  role: Customer.ioRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logCustomer.ioAccess(entry: Customer.ioAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Customer.io permissions.

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
- [Customer.io Enterprise Guide](https://docs.customerio.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `customerio-migration-deep-dive`.