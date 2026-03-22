---
name: apple-notes-enterprise-rbac
description: |
  Configure Apple Notes enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Apple Notes.
  Trigger with phrases like "apple-notes SSO", "apple-notes RBAC",
  "apple-notes enterprise", "apple-notes roles", "apple-notes permissions", "apple-notes SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apple-notes]
---

# Apple Notes Enterprise RBAC

## Overview
Configure enterprise-grade access control for Apple Notes integrations.

## Prerequisites
- Apple Notes Enterprise tier subscription
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
enum Apple NotesRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface Apple NotesPermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<Apple NotesRole, Apple NotesPermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: Apple NotesRole,
  action: keyof Apple NotesPermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Apple Notes SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://apple-notes.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/apple-notes/callback',
};

// Map IdP groups to Apple Notes roles
const groupRoleMapping: Record<string, Apple NotesRole> = {
  'Engineering': Apple NotesRole.Developer,
  'Platform-Admins': Apple NotesRole.Admin,
  'Data-Team': Apple NotesRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@apple-notes/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.APPLE-NOTES_OAUTH_CLIENT_ID!,
  clientSecret: process.env.APPLE-NOTES_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/apple-notes/callback',
  scopes: ['read', 'write'],
});
```

## Organization Management

```typescript
interface Apple NotesOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: Apple NotesRole;
}

async function createOrganization(
  config: Apple NotesOrganization
): Promise<void> {
  await apple-notesClient.organizations.create({
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
function requireApple NotesPermission(
  requiredPermission: keyof Apple NotesPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { apple-notesRole: Apple NotesRole };

    if (!checkPermission(user.apple-notesRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/apple-notes/resource/:id',
  requireApple NotesPermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface Apple NotesAuditEntry {
  timestamp: Date;
  userId: string;
  role: Apple NotesRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logApple NotesAccess(entry: Apple NotesAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Apple Notes permissions.

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
- [Apple Notes Enterprise Guide](https://docs.apple-notes.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `apple-notes-migration-deep-dive`.