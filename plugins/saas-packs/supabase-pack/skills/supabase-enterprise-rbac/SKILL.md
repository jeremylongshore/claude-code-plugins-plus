---
name: supabase-enterprise-rbac
description: |
  Supabase enterprise SSO, roles, and organization controls.
  Use when implementing enterprise access control for Supabase.
  Trigger with phrases like "supabase SSO", "supabase RBAC",
  "supabase enterprise", "supabase roles".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Enterprise RBAC

## Overview
Configure enterprise-grade access control for Supabase integrations.

## Prerequisites
- supabase-install-auth completed
- Enterprise Supabase plan active
- Identity provider (Okta, Azure AD, etc.) configured
- Organization structure defined

## Instructions

### Step 1: Role Definitions

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

### Step 2: Audit Trail

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

## Output
- Role-based access control implemented
- SSO integration configured
- Organization structure enforced
- Audit trail for all access attempts

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| SSO callback failed | Misconfigured callback URL | Verify callback URL in IdP settings |
| Role mapping failed | Unknown group | Add group to role mapping |
| Permission denied | Wrong role assigned | Review user's group membership in IdP |
| Token expired | Session timeout | Implement token refresh logic |

## Examples

### Azure AD Integration

```typescript
import { ConfidentialClientApplication } from '@azure/msal-node';

const msalConfig = {
  auth: {
    clientId: process.env.AZURE_CLIENT_ID!,
    authority: `https://login.microsoftonline.com/${process.env.AZURE_TENANT_ID}`,
    clientSecret: process.env.AZURE_CLIENT_SECRET!,
  },
};

const cca = new ConfidentialClientApplication(msalConfig);
```

## Resources
- [Supabase Enterprise Guide](https://supabase.com/docs/enterprise)
- [SSO Configuration](https://supabase.com/docs/sso)
- [RBAC Best Practices](https://supabase.com/docs/rbac)

## Next Steps
For major migrations, see `supabase-migration-deep-dive`.