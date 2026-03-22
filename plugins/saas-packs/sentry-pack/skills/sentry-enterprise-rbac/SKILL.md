---
name: sentry-enterprise-rbac
description: |
  Configure Sentry enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Sentry.
  Trigger with phrases like "sentry SSO", "sentry RBAC",
  "sentry enterprise", "sentry roles", "sentry permissions", "sentry SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, sentry]
---

# Sentry Enterprise RBAC

## Overview
Configure enterprise-grade access control for Sentry integrations.

## Prerequisites
- Sentry Enterprise tier subscription
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
enum SentryRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface SentryPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<SentryRole, SentryPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: SentryRole,
  action: keyof SentryPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Sentry SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://sentry.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/sentry/callback',
};

// Map IdP groups to Sentry roles
const groupRoleMapping: Record<string, SentryRole> = {
  'Engineering': SentryRole.Developer,
  'Platform-Admins': SentryRole.Admin,
  'Data-Team': SentryRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@sentry/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.SENTRY_OAUTH_CLIENT_ID!,
  clientSecret: process.env.SENTRY_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/sentry/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface SentryOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: SentryRole;
}

async function createOrganization(
  config: SentryOrganization
): Promise<void> {
  await sentryClient.organizations.create({
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
function requireSentryPermission(
  requiredPermission: keyof SentryPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { sentryRole: SentryRole };

    if (!checkPermission(user.sentryRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/sentry/resource/:id',
  requireSentryPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface SentryAuditEntry {
  timestamp: Date;
  userId: string;
  role: SentryRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logSentryAccess(entry: SentryAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Sentry permissions.

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
- [Sentry Enterprise Guide](https://docs.sentry.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `sentry-migration-deep-dive`.