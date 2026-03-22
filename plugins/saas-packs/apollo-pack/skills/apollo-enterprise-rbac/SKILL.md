---
name: apollo-enterprise-rbac
description: |
  Configure Apollo enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Apollo.
  Trigger with phrases like "apollo SSO", "apollo RBAC",
  "apollo enterprise", "apollo roles", "apollo permissions", "apollo SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apollo]
---

# Apollo Enterprise RBAC

## Overview
Configure enterprise-grade access control for Apollo integrations.

## Prerequisites
- Apollo Enterprise tier subscription
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
enum ApolloRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface ApolloPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<ApolloRole, ApolloPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: ApolloRole,
  action: keyof ApolloPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Apollo SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://apollo.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/apollo/callback',
};

// Map IdP groups to Apollo roles
const groupRoleMapping: Record<string, ApolloRole> = {
  'Engineering': ApolloRole.Developer,
  'Platform-Admins': ApolloRole.Admin,
  'Data-Team': ApolloRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@apollo/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.APOLLO_OAUTH_CLIENT_ID!,
  clientSecret: process.env.APOLLO_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/apollo/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface ApolloOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: ApolloRole;
}

async function createOrganization(
  config: ApolloOrganization
): Promise<void> {
  await apolloClient.organizations.create({
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
function requireApolloPermission(
  requiredPermission: keyof ApolloPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { apolloRole: ApolloRole };

    if (!checkPermission(user.apolloRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/apollo/resource/:id',
  requireApolloPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface ApolloAuditEntry {
  timestamp: Date;
  userId: string;
  role: ApolloRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logApolloAccess(entry: ApolloAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Apollo permissions.

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
- [Apollo Enterprise Guide](https://docs.apollo.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `apollo-migration-deep-dive`.