---
name: supabase-enterprise-rbac
description: |
  Configure Supabase enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Supabase.
  Trigger with phrases like "supabase SSO", "supabase RBAC",
  "supabase enterprise", "supabase roles", "supabase permissions", "supabase SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Enterprise RBAC

## Overview
Configure enterprise-grade access control for Supabase integrations.

## Prerequisites
- Supabase Enterprise tier subscription
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
enum SupabaseRole {
  Admin = 'admin',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface SupabasePermissions {
  read: boolean;
  write: boolean;
  delete: boolean;
  admin: boolean;
}

const ROLE_PERMISSIONS: Record<SupabaseRole, SupabasePermissions> = {
  admin: { read: true, write: true, delete: true, admin: true },
  developer: { read: true, write: true, delete: false, admin: false },
  viewer: { read: true, write: false, delete: false, admin: false },
  service: { read: true, write: true, delete: false, admin: false },
};

function checkPermission(
  role: SupabaseRole,
  action: keyof SupabasePermissions
): boolean {
  return ROLE_PERMISSIONS[role][action];
}
```

## SSO Integration

### SAML Configuration

```typescript
// Supabase SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://supabase.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/supabase/callback',
};

// Map IdP groups to Supabase roles
const groupRoleMapping: Record<string, SupabaseRole> = {
  'Engineering': SupabaseRole.Developer,
  'Platform-Admins': SupabaseRole.Admin,
  'Data-Team': SupabaseRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@supabase/supabase-js';

const oauthClient = new OAuth2Client({
  clientId: process.env.SUPABASE_OAUTH_CLIENT_ID!,
  clientSecret: process.env.SUPABASE_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/supabase/callback',
  scopes: read, write, realtime,
});
```

## Organization Management

```typescript
interface SupabaseOrganization {
  id: string;
  name: string;
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: SupabaseRole;
}

async function createOrganization(
  config: SupabaseOrganization
): Promise<void> {
  await supabaseClient.organizations.create({
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
function requireSupabasePermission(
  requiredPermission: keyof SupabasePermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { supabaseRole: SupabaseRole };

    if (!checkPermission(user.supabaseRole, requiredPermission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Usage
app.delete('/supabase/resource/:id',
  requireSupabasePermission('delete'),
  deleteResourceHandler
);
```

## Audit Trail

```typescript
interface SupabaseAuditEntry {
  timestamp: Date;
  userId: string;
  role: SupabaseRole;
  action: string;
  resource: string;
  success: boolean;
  ipAddress: string;
}

async function logSupabaseAccess(entry: SupabaseAuditEntry): Promise<void> {
  await auditDb.insert(entry);

  // Alert on suspicious activity
  if (entry.action === 'delete' && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }
}
```

## Instructions

### Step 1: Define Roles
Map organizational roles to Supabase permissions.

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
- [Supabase Enterprise Guide](https://supabase.com/docs/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `supabase-migration-deep-dive`.