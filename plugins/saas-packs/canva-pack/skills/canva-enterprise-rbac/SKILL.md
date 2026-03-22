---
name: canva-enterprise-rbac
description: |
  Configure Canva Enterprise organization access control and scope management.
  Use when implementing per-user scope control, managing Canva Enterprise features,
  or setting up organization-level Canva integration governance.
  Trigger with phrases like "canva enterprise", "canva RBAC",
  "canva roles", "canva permissions", "canva organization", "canva team".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Enterprise RBAC

## Overview

Manage access control for Canva Connect API integrations at the organization level. The Canva API uses OAuth scopes (not roles) — your application layer implements RBAC on top of Canva's scope system.

## Canva Enterprise Requirements

| Feature | Canva Free/Pro | Canva Enterprise |
|---------|----------------|------------------|
| Design Create/Read | Yes | Yes |
| Export Designs | Yes | Yes |
| Asset Upload | Yes | Yes |
| Brand Templates | No | Yes |
| Autofill API | No | Yes |
| Folders (advanced) | Limited | Yes |
| Comments API | Yes | Yes |

**Key:** Autofill and brand template APIs require the user to be a member of a Canva Enterprise organization.

## Application-Level RBAC

```typescript
// Your application controls what each user role can do with Canva

interface CanvaRole {
  name: string;
  scopes: string[];          // OAuth scopes to request
  allowedOperations: string[]; // Application-level operations
}

const CANVA_ROLES: Record<string, CanvaRole> = {
  viewer: {
    name: 'Viewer',
    scopes: ['design:meta:read'],
    allowedOperations: ['listDesigns', 'getDesign'],
  },
  creator: {
    name: 'Creator',
    scopes: ['design:meta:read', 'design:content:write', 'design:content:read', 'asset:write', 'asset:read'],
    allowedOperations: ['listDesigns', 'getDesign', 'createDesign', 'exportDesign', 'uploadAsset'],
  },
  admin: {
    name: 'Admin',
    scopes: [
      'design:meta:read', 'design:content:write', 'design:content:read',
      'asset:write', 'asset:read',
      'brandtemplate:meta:read', 'brandtemplate:content:read',
      'folder:read', 'folder:write',
      'comment:read', 'comment:write',
      'collaboration:event',
    ],
    allowedOperations: ['*'],
  },
};

// Request only the scopes needed for the user's role
function getScopesForRole(role: string): string[] {
  return CANVA_ROLES[role]?.scopes || CANVA_ROLES.viewer.scopes;
}
```

## Permission Middleware

```typescript
function requireCanvaOperation(operation: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userRole = req.user?.canvaRole || 'viewer';
    const role = CANVA_ROLES[userRole];

    if (!role) {
      return res.status(403).json({ error: 'Unknown role' });
    }

    if (!role.allowedOperations.includes('*') && !role.allowedOperations.includes(operation)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Role '${userRole}' cannot perform '${operation}'`,
        requiredRole: Object.entries(CANVA_ROLES)
          .find(([, r]) => r.allowedOperations.includes(operation) || r.allowedOperations.includes('*'))
          ?.[0],
      });
    }

    next();
  };
}

// Usage
app.post('/api/designs',
  requireCanvaOperation('createDesign'),
  async (req, res) => {
    const result = await req.canva.createDesign(req.body);
    res.json(result);
  }
);

app.post('/api/autofill',
  requireCanvaOperation('autofillTemplate'),
  async (req, res) => {
    // Only admins can autofill — requires Enterprise + admin role
    const result = await req.canva.createAutofill(req.body);
    res.json(result);
  }
);
```

## User Capabilities Check

```typescript
// GET https://api.canva.com/rest/v1/users/me/capabilities
// Check what the authenticated user can do

async function checkUserCapabilities(token: string): Promise<{
  canAutofill: boolean;
  isEnterprise: boolean;
}> {
  try {
    const data = await canvaAPI('/users/me/capabilities', token);
    return {
      canAutofill: data.capabilities?.includes('autofill') || false,
      isEnterprise: data.capabilities?.includes('brand_template') || false,
    };
  } catch {
    return { canAutofill: false, isEnterprise: false };
  }
}
```

## Scope-Based Access Control

```typescript
// Track which scopes each user authorized
interface UserCanvaAuth {
  userId: string;
  grantedScopes: string[];   // Scopes the user consented to
  role: string;              // Application-assigned role
  connectedAt: Date;
}

// Check if a specific API call is authorized
function canPerformAction(
  userAuth: UserCanvaAuth,
  requiredScope: string
): boolean {
  // 1. Check application role allows the operation
  const role = CANVA_ROLES[userAuth.role];
  if (!role) return false;

  // 2. Check the required OAuth scope was granted by the user
  if (!userAuth.grantedScopes.includes(requiredScope)) {
    console.warn(`User ${userAuth.userId} missing scope: ${requiredScope}`);
    return false;
  }

  return true;
}

// If user needs additional scopes, redirect to re-authorize
function buildReAuthUrl(userId: string, additionalScopes: string[]): string {
  const existingScopes = userAuth.grantedScopes;
  const allScopes = [...new Set([...existingScopes, ...additionalScopes])];

  return getAuthorizationUrl({
    clientId: process.env.CANVA_CLIENT_ID!,
    redirectUri: process.env.CANVA_REDIRECT_URI!,
    scopes: allScopes,
    codeChallenge: generatePKCE().challenge,
    state: `reauth:${userId}`,
  });
}
```

## Audit Logging

```typescript
async function auditCanvaAction(entry: {
  userId: string;
  role: string;
  action: string;
  endpoint: string;
  success: boolean;
  designId?: string;
}): Promise<void> {
  await db.auditLog.insert({
    ...entry,
    service: 'canva-connect-api',
    timestamp: new Date(),
  });

  // Alert on permission escalation attempts
  if (!entry.success && entry.action === 'autofillTemplate') {
    console.warn(`Permission denied: user ${entry.userId} (role: ${entry.role}) attempted ${entry.action}`);
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 on autofill | Not Enterprise user | Check user capabilities first |
| Scope not granted | User rejected consent | Show scope explanation, re-auth |
| Role mismatch | Wrong role assigned | Update user role in your DB |
| New scope needed | Feature added | Trigger re-authorization flow |

## Resources

- [Canva Scopes](https://www.canva.dev/docs/connect/appendix/scopes/)
- [User Capabilities API](https://www.canva.dev/docs/connect/api-reference/users/get-user-capabilities/)
- [Canva Enterprise](https://www.canva.com/enterprise/)

## Next Steps

For major migrations, see `canva-migration-deep-dive`.
