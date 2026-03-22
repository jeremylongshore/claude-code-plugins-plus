---
name: retellai-enterprise-rbac
description: |
  Configure Retell AI enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Retell AI.
  Trigger with phrases like "retellai SSO", "retellai RBAC",
  "retellai enterprise", "retellai roles", "retellai permissions", "retellai SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, retellai]
---

# Retell AI Enterprise RBAC

## Overview
Configure enterprise-grade access control for Retell AI integrations.

## Prerequisites
- Retell AI Enterprise tier subscription
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
enum Retell AIRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface Retell AIPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<Retell AIRole, Retell AIPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: Retell AIRole,
  action: keyof Retell AIPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Retell AI SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://retellai.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/retellai/callback',
};

// Map IdP groups to Retell AI roles
const groupRoleMapping: Record<string, Retell AIRole> = {
  'Engineering': Retell AIRole.Developer,
  'Platform-Admins': Retell AIRole.Admin,
  'Data-Team': Retell AIRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@retellai/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.RETELLAI_OAUTH_CLIENT_ID!,
  clientSecret: process.env.RETELLAI_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/retellai/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface Retell AIOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: Retell AIRole;
}

async function createOrganization(
  config: Retell AIOrganization
): Promise<void> {
  await retellaiClient.organizations.create({
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
function requireRetell AIPermission(
  requiredPermission: keyof Retell AIPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { retellaiRole: Retell AIRole };

    if (!checkPermission(user.retellaiRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/retellai/resource/:id',
  requireRetell AIPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface Retell AIAuditEntry {
  timestamp: Date;
  userId: string;
  role: Retell AIRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logRetell AIAccess(entry: Retell AIAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Retell AI permissions.

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
- [Retell AI Enterprise Guide](https://docs.retellai.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `retellai-migration-deep-dive`.