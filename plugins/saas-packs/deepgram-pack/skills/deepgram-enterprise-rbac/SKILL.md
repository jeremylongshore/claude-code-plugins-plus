---
name: deepgram-enterprise-rbac
description: |
  Configure Deepgram enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Deepgram.
  Trigger with phrases like "deepgram SSO", "deepgram RBAC",
  "deepgram enterprise", "deepgram roles", "deepgram permissions", "deepgram SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, deepgram]
---

# Deepgram Enterprise RBAC

## Overview
Configure enterprise-grade access control for Deepgram integrations.

## Prerequisites
- Deepgram Enterprise tier subscription
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
enum DeepgramRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface DeepgramPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<DeepgramRole, DeepgramPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: DeepgramRole,
  action: keyof DeepgramPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Deepgram SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://deepgram.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/deepgram/callback',
};

// Map IdP groups to Deepgram roles
const groupRoleMapping: Record<string, DeepgramRole> = {
  'Engineering': DeepgramRole.Developer,
  'Platform-Admins': DeepgramRole.Admin,
  'Data-Team': DeepgramRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@deepgram/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.DEEPGRAM_OAUTH_CLIENT_ID!,
  clientSecret: process.env.DEEPGRAM_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/deepgram/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface DeepgramOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: DeepgramRole;
}

async function createOrganization(
  config: DeepgramOrganization
): Promise<void> {
  await deepgramClient.organizations.create({
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
function requireDeepgramPermission(
  requiredPermission: keyof DeepgramPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { deepgramRole: DeepgramRole };

    if (!checkPermission(user.deepgramRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/deepgram/resource/:id',
  requireDeepgramPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface DeepgramAuditEntry {
  timestamp: Date;
  userId: string;
  role: DeepgramRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logDeepgramAccess(entry: DeepgramAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Deepgram permissions.

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
- [Deepgram Enterprise Guide](https://docs.deepgram.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `deepgram-migration-deep-dive`.