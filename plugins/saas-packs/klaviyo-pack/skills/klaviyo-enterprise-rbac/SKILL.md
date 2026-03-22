---
name: klaviyo-enterprise-rbac
description: |
  Configure Klaviyo enterprise access control with API key scopes and OAuth.
  Use when implementing per-key scoping, configuring OAuth app authorization,
  or setting up organization-level access controls for Klaviyo.
  Trigger with phrases like "klaviyo scopes", "klaviyo RBAC",
  "klaviyo enterprise", "klaviyo permissions", "klaviyo OAuth", "klaviyo access control".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Enterprise RBAC

## Overview

Enterprise access control for Klaviyo: API key scoping with granular read/write permissions, OAuth app authorization flows, and application-level RBAC built on top of Klaviyo's scope system.

## Prerequisites

- Klaviyo account with API key management access
- Understanding of OAuth 2.0 (for OAuth apps)
- Application requiring per-user or per-role Klaviyo access

## Klaviyo Access Control Model

Klaviyo uses **scoped API keys** and **OAuth** for access control. There are no built-in "roles" in Klaviyo's API -- you implement RBAC by creating multiple API keys with different scopes.

### API Key Scopes

| Scope | Read | Write | What It Controls |
|-------|------|-------|-----------------|
| `accounts` | Account info | N/A | Organization name, timezone |
| `campaigns` | List campaigns | Create/send campaigns | Email, SMS, push campaigns |
| `catalogs` | Browse items | CRUD catalog items | Product catalog management |
| `coupons` | List coupons | Create coupons | Coupon/discount codes |
| `data-privacy` | N/A | Delete profiles | GDPR/CCPA deletion requests |
| `events` | Query events | Track events | Server-side event tracking |
| `flows` | List flows | Create/update flows | Flow automation |
| `images` | List images | Upload images | Email template images |
| `lists` | List lists | CRUD lists/members | List management |
| `metrics` | Query metrics | N/A | Metric aggregations |
| `profiles` | Read profiles | Create/update profiles | Profile management |
| `segments` | Read segments | N/A | Segment queries |
| `tags` | Read tags | CRUD tags | Resource tagging |
| `templates` | Read templates | Create/update templates | Email templates |
| `webhooks` | List webhooks | CRUD webhooks | Webhook subscriptions |

## Instructions

### Step 1: Create Scoped API Keys

Create separate API keys per service/role in Klaviyo dashboard (**Settings > API Keys**):

```typescript
// Example: different keys for different services

// Profile Sync Service -- only needs profiles + lists
// Key scopes: profiles:read, profiles:write, lists:read, lists:write
const profileSyncSession = new ApiKeySession(process.env.KLAVIYO_KEY_PROFILE_SYNC!);

// Event Tracking Service -- only needs events + profiles
// Key scopes: events:write, profiles:read, profiles:write
const eventTrackingSession = new ApiKeySession(process.env.KLAVIYO_KEY_EVENT_TRACKER!);

// Reporting Dashboard -- read-only
// Key scopes: campaigns:read, metrics:read, segments:read, profiles:read
const reportingSession = new ApiKeySession(process.env.KLAVIYO_KEY_REPORTING!);

// Admin Service -- full access (use sparingly)
// Key scopes: all scopes
const adminSession = new ApiKeySession(process.env.KLAVIYO_KEY_ADMIN!);
```

### Step 2: Application-Level RBAC

```typescript
// src/klaviyo/rbac.ts

enum AppRole {
  Admin = 'admin',
  Marketer = 'marketer',
  Developer = 'developer',
  Viewer = 'viewer',
  Service = 'service',
}

interface KlaviyoPermissions {
  canReadProfiles: boolean;
  canWriteProfiles: boolean;
  canDeleteProfiles: boolean;
  canSendCampaigns: boolean;
  canManageLists: boolean;
  canTrackEvents: boolean;
  canViewReports: boolean;
  canManageWebhooks: boolean;
}

const ROLE_PERMISSIONS: Record<AppRole, KlaviyoPermissions> = {
  admin: {
    canReadProfiles: true, canWriteProfiles: true, canDeleteProfiles: true,
    canSendCampaigns: true, canManageLists: true, canTrackEvents: true,
    canViewReports: true, canManageWebhooks: true,
  },
  marketer: {
    canReadProfiles: true, canWriteProfiles: false, canDeleteProfiles: false,
    canSendCampaigns: true, canManageLists: true, canTrackEvents: false,
    canViewReports: true, canManageWebhooks: false,
  },
  developer: {
    canReadProfiles: true, canWriteProfiles: true, canDeleteProfiles: false,
    canSendCampaigns: false, canManageLists: true, canTrackEvents: true,
    canViewReports: true, canManageWebhooks: true,
  },
  viewer: {
    canReadProfiles: true, canWriteProfiles: false, canDeleteProfiles: false,
    canSendCampaigns: false, canManageLists: false, canTrackEvents: false,
    canViewReports: true, canManageWebhooks: false,
  },
  service: {
    canReadProfiles: true, canWriteProfiles: true, canDeleteProfiles: false,
    canSendCampaigns: false, canManageLists: false, canTrackEvents: true,
    canViewReports: false, canManageWebhooks: false,
  },
};

export function checkPermission(role: AppRole, permission: keyof KlaviyoPermissions): boolean {
  return ROLE_PERMISSIONS[role][permission];
}

// Map roles to API keys with appropriate scopes
const ROLE_API_KEYS: Record<AppRole, string> = {
  admin: process.env.KLAVIYO_KEY_ADMIN!,
  marketer: process.env.KLAVIYO_KEY_MARKETER!,
  developer: process.env.KLAVIYO_KEY_DEVELOPER!,
  viewer: process.env.KLAVIYO_KEY_VIEWER!,
  service: process.env.KLAVIYO_KEY_SERVICE!,
};

export function getSessionForRole(role: AppRole): ApiKeySession {
  const key = ROLE_API_KEYS[role];
  if (!key) throw new Error(`No API key configured for role: ${role}`);
  return new ApiKeySession(key);
}
```

### Step 3: Permission Middleware

```typescript
// src/middleware/klaviyo-auth.ts
import { checkPermission, AppRole, KlaviyoPermissions } from '../klaviyo/rbac';

export function requireKlaviyoPermission(permission: keyof KlaviyoPermissions) {
  return (req: any, res: any, next: any) => {
    const userRole = req.user?.klaviyoRole as AppRole;
    if (!userRole) return res.status(401).json({ error: 'No Klaviyo role assigned' });

    if (!checkPermission(userRole, permission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Role '${userRole}' does not have permission: ${permission}`,
      });
    }

    next();
  };
}

// Usage in routes
app.get('/api/klaviyo/profiles',
  requireKlaviyoPermission('canReadProfiles'),
  profilesHandler
);

app.post('/api/klaviyo/campaigns/send',
  requireKlaviyoPermission('canSendCampaigns'),
  campaignSendHandler
);

app.delete('/api/klaviyo/profiles/:id',
  requireKlaviyoPermission('canDeleteProfiles'),
  profileDeleteHandler
);
```

### Step 4: OAuth App Flow (for third-party integrations)

```typescript
// OAuth flow for Klaviyo apps (marketplace integrations)
// Reference: https://developers.klaviyo.com/en/docs/set_up_oauth

const OAUTH_CONFIG = {
  clientId: process.env.KLAVIYO_OAUTH_CLIENT_ID!,
  clientSecret: process.env.KLAVIYO_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://your-app.com/auth/klaviyo/callback',
  authorizationUrl: 'https://www.klaviyo.com/oauth/authorize',
  tokenUrl: 'https://a.klaviyo.com/oauth/token',
  // Only request scopes your app needs
  scopes: ['profiles:read', 'profiles:write', 'events:write', 'lists:read'],
};

// Step 1: Redirect user to Klaviyo authorization
function getAuthorizationUrl(state: string): string {
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: OAUTH_CONFIG.clientId,
    redirect_uri: OAUTH_CONFIG.redirectUri,
    scope: OAUTH_CONFIG.scopes.join(' '),
    state,
  });
  return `${OAUTH_CONFIG.authorizationUrl}?${params}`;
}

// Step 2: Exchange code for access token
async function exchangeCodeForToken(code: string): Promise<{
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}> {
  const response = await fetch(OAUTH_CONFIG.tokenUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      client_id: OAUTH_CONFIG.clientId,
      client_secret: OAUTH_CONFIG.clientSecret,
      redirect_uri: OAUTH_CONFIG.redirectUri,
    }),
  });

  const data = await response.json();
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresIn: data.expires_in,
  };
}
```

### Step 5: Audit Trail

```typescript
// src/klaviyo/audit.ts

interface KlaviyoAuditEntry {
  timestamp: Date;
  userId: string;
  role: AppRole;
  action: string;
  resource: string;
  success: boolean;
  klaviyoEndpoint: string;
  ipAddress?: string;
}

async function logKlaviyoAccess(entry: KlaviyoAuditEntry): Promise<void> {
  // Store in audit database
  await db.auditLog.create({ data: entry });

  // Alert on suspicious activity
  if (entry.action === 'DELETE' && entry.resource.includes('profile')) {
    await alertSecurityTeam(`Profile deletion by ${entry.userId} (${entry.role})`);
  }
}
```

## Environment Variable Layout

```bash
# Per-role API keys (create in Klaviyo dashboard with specific scopes)
KLAVIYO_KEY_ADMIN=pk_admin_***         # All scopes
KLAVIYO_KEY_MARKETER=pk_marketer_***   # campaigns:*, lists:*, profiles:read, segments:read
KLAVIYO_KEY_DEVELOPER=pk_dev_***       # profiles:*, events:*, lists:*, webhooks:*, templates:*
KLAVIYO_KEY_VIEWER=pk_viewer_***       # *:read only
KLAVIYO_KEY_SERVICE=pk_service_***     # events:write, profiles:read/write

# OAuth (for marketplace apps)
KLAVIYO_OAUTH_CLIENT_ID=your_client_id
KLAVIYO_OAUTH_CLIENT_SECRET=your_client_secret
```

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `permission_denied` | 403 | API key missing required scope | Create new key with correct scopes |
| OAuth code expired | 400 | User took too long to authorize | Retry authorization flow |
| Token refresh failed | 401 | Refresh token revoked | Re-authorize the app |
| Role not assigned | 401 | User missing `klaviyoRole` | Assign role in your user management |

## Resources

- [Klaviyo API Scopes](https://developers.klaviyo.com/en/docs/authenticate_)
- [OAuth Setup Guide](https://developers.klaviyo.com/en/docs/set_up_oauth)
- [Update OAuth Scopes](https://developers.klaviyo.com/en/docs/update_your_oauth_scopes)

## Next Steps

For major migrations, see `klaviyo-migration-deep-dive`.
