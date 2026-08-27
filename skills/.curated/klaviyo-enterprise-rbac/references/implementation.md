# Klaviyo Enterprise RBAC — Full Implementation Walkthrough

This is the complete, copy-ready implementation referenced from `SKILL.md`. It
covers the full workflow: scoped API keys, application-level RBAC, permission
middleware, the OAuth app flow, and an audit trail, followed by the environment
variable layout.

## Step 1: Create Scoped API Keys

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

## Step 2: Application-Level RBAC

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

## Step 3: Permission Middleware

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

## Step 4: OAuth App Flow (for third-party integrations)

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

## Step 5: Audit Trail

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
