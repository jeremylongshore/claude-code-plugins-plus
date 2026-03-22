---
name: webflow-enterprise-rbac
description: |
  Configure Webflow enterprise access control — OAuth 2.0 app authorization,
  scope-based RBAC, per-site token isolation, workspace member management,
  and audit logging for compliance.
  Trigger with phrases like "webflow RBAC", "webflow enterprise",
  "webflow roles", "webflow permissions", "webflow OAuth scopes",
  "webflow access control", "webflow workspace members".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Enterprise RBAC

## Overview

Enterprise-grade access control for Webflow Data API v2 integrations. Uses Webflow's
OAuth 2.0 scope system, per-site token isolation, and application-level RBAC to
enforce least privilege across teams and environments.

## Prerequisites

- Webflow workspace (Core plan or higher for multiple members)
- OAuth 2.0 Data Client App (for user-authorized access)
- Understanding of Webflow scopes

## Webflow's Native Access Model

Webflow provides three levels of access control:

| Level | Mechanism | Granularity |
|-------|-----------|-------------|
| **Workspace tokens** | API token | All sites in workspace |
| **Site tokens** | API token | Single site |
| **OAuth tokens** | OAuth 2.0 authorization | User-authorized scopes per site |

## Scope-Based Permission Model

Webflow scopes map directly to API access:

| Scope | Read Access | Write Access |
|-------|-------------|--------------|
| `sites:read` | List/get sites | — |
| `sites:write` | — | Publish sites |
| `cms:read` | List collections, read items | — |
| `cms:write` | — | Create/update/delete CMS items |
| `pages:read` | List/get pages | — |
| `pages:write` | — | Update page settings |
| `forms:read` | List forms, read submissions | — |
| `ecommerce:read` | List products, orders, inventory | — |
| `ecommerce:write` | — | Create products, fulfill orders |
| `custom_code:read` | List registered scripts | — |
| `custom_code:write` | — | Register/apply custom code |

## Instructions

### Step 1: Define Application Roles

Map your application roles to Webflow scope sets:

```typescript
enum AppRole {
  ContentViewer = "content_viewer",
  ContentEditor = "content_editor",
  SiteAdmin = "site_admin",
  EcommerceManager = "ecommerce_manager",
  FormProcessor = "form_processor",
}

// Map roles to required Webflow OAuth scopes
const ROLE_SCOPES: Record<AppRole, string[]> = {
  [AppRole.ContentViewer]: ["sites:read", "cms:read", "pages:read"],
  [AppRole.ContentEditor]: ["sites:read", "cms:read", "cms:write", "pages:read"],
  [AppRole.SiteAdmin]: [
    "sites:read", "sites:write",
    "cms:read", "cms:write",
    "pages:read", "pages:write",
    "custom_code:read", "custom_code:write",
  ],
  [AppRole.EcommerceManager]: [
    "sites:read",
    "ecommerce:read", "ecommerce:write",
    "cms:read", // Products are CMS collections
  ],
  [AppRole.FormProcessor]: ["sites:read", "forms:read"],
};
```

### Step 2: OAuth App with Role-Based Scopes

Request only the scopes needed for the user's role:

```typescript
function getAuthorizationUrl(role: AppRole, state: string): string {
  const scopes = ROLE_SCOPES[role];
  const scopeString = scopes.join(" ");

  return (
    `https://webflow.com/oauth/authorize` +
    `?client_id=${process.env.WEBFLOW_CLIENT_ID}` +
    `&response_type=code` +
    `&redirect_uri=${encodeURIComponent(process.env.REDIRECT_URI!)}` +
    `&scope=${encodeURIComponent(scopeString)}` +
    `&state=${state}` // CSRF protection
  );
}

// Initiate OAuth flow with role-appropriate scopes
app.get("/auth/webflow", (req, res) => {
  const role = req.user.appRole as AppRole;
  const state = generateCsrfToken(req.session.id);

  res.redirect(getAuthorizationUrl(role, state));
});
```

### Step 3: Token Storage with Role Metadata

```typescript
interface StoredToken {
  accessToken: string;
  userId: string;
  role: AppRole;
  scopes: string[];
  siteIds: string[]; // Which sites this token can access
  createdAt: Date;
  lastUsed: Date;
}

async function storeToken(token: StoredToken): Promise<void> {
  // Encrypt token before storing
  const encrypted = encrypt(token.accessToken);

  await db.webflowTokens.upsert({
    where: { userId: token.userId },
    create: {
      ...token,
      accessToken: encrypted,
    },
    update: {
      accessToken: encrypted,
      lastUsed: new Date(),
    },
  });
}
```

### Step 4: Per-Site Token Isolation

Use site-scoped tokens to limit blast radius:

```typescript
class SiteIsolatedClient {
  private clients = new Map<string, WebflowClient>();

  // Each site gets its own token — compromise of one doesn't affect others
  registerSite(siteId: string, siteToken: string): void {
    this.clients.set(siteId, new WebflowClient({ accessToken: siteToken }));
  }

  getClient(siteId: string): WebflowClient {
    const client = this.clients.get(siteId);
    if (!client) {
      throw new Error(`No token registered for site ${siteId}`);
    }
    return client;
  }

  // Rotate a single site's token without affecting others
  rotateToken(siteId: string, newToken: string): void {
    this.clients.set(siteId, new WebflowClient({ accessToken: newToken }));
    console.log(`Token rotated for site ${siteId}`);
  }
}

const siteClients = new SiteIsolatedClient();
siteClients.registerSite("site-prod", process.env.WEBFLOW_TOKEN_PROD!);
siteClients.registerSite("site-staging", process.env.WEBFLOW_TOKEN_STAGING!);
```

### Step 5: Permission Check Middleware

```typescript
import { Request, Response, NextFunction } from "express";

function requireWebflowScope(requiredScopes: string[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userToken = await db.webflowTokens.findByUserId(req.user.id);

    if (!userToken) {
      return res.status(401).json({ error: "No Webflow authorization" });
    }

    // Check if user's token has the required scopes
    const missingScopes = requiredScopes.filter(
      s => !userToken.scopes.includes(s)
    );

    if (missingScopes.length > 0) {
      return res.status(403).json({
        error: "Insufficient Webflow permissions",
        missing: missingScopes,
        userRole: userToken.role,
        hint: `Role "${userToken.role}" does not include: ${missingScopes.join(", ")}`,
      });
    }

    next();
  };
}

// Usage
app.post(
  "/api/cms/items",
  requireWebflowScope(["cms:write"]),
  createItemHandler
);

app.get(
  "/api/forms/submissions",
  requireWebflowScope(["forms:read"]),
  listSubmissionsHandler
);

app.post(
  "/api/site/publish",
  requireWebflowScope(["sites:write"]),
  publishSiteHandler
);
```

### Step 6: Audit Logging

```typescript
interface WebflowAuditEntry {
  timestamp: Date;
  userId: string;
  role: AppRole;
  operation: string;
  siteId: string;
  resourceType: string;
  resourceId?: string;
  result: "success" | "denied" | "error";
  scopes: string[];
  ipAddress: string;
}

async function auditWebflowAccess(entry: WebflowAuditEntry): Promise<void> {
  // Write to audit log (never delete audit entries)
  await db.auditLog.create({
    data: {
      ...entry,
      timestamp: entry.timestamp.toISOString(),
    },
  });

  // Alert on suspicious patterns
  if (entry.result === "denied") {
    console.warn(`ACCESS DENIED: ${entry.userId} attempted ${entry.operation} on ${entry.resourceType}`);
  }

  // Alert on admin operations
  if (entry.role === AppRole.SiteAdmin && entry.operation.includes("publish")) {
    console.log(`ADMIN ACTION: ${entry.userId} published site ${entry.siteId}`);
  }
}

// Wrap API calls with audit logging
async function auditedCall<T>(
  entry: Omit<WebflowAuditEntry, "timestamp" | "result">,
  operation: () => Promise<T>
): Promise<T> {
  try {
    const result = await operation();
    await auditWebflowAccess({ ...entry, timestamp: new Date(), result: "success" });
    return result;
  } catch (error) {
    await auditWebflowAccess({ ...entry, timestamp: new Date(), result: "error" });
    throw error;
  }
}
```

### Step 7: Token Rotation Schedule

```typescript
async function checkTokenAge(): Promise<void> {
  const tokens = await db.webflowTokens.findMany();

  for (const token of tokens) {
    const ageInDays = (Date.now() - token.createdAt.getTime()) / (1000 * 60 * 60 * 24);

    if (ageInDays > 90) {
      console.warn(
        `Token for user ${token.userId} (${token.role}) is ${Math.floor(ageInDays)} days old. ` +
        `Rotation recommended.`
      );
      // Send notification to user/admin
    }
  }
}

// Run weekly
// cron: "0 9 * * 1"
```

## Output

- Role-to-scope mapping for Webflow OAuth
- OAuth authorization with role-appropriate scopes
- Per-site token isolation
- Permission check middleware for API endpoints
- Comprehensive audit logging
- Token age monitoring and rotation alerts

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| OAuth scope mismatch | App requests more scopes than configured | Match app settings in Webflow dashboard |
| 403 on API call | Token missing required scope | Re-authorize with correct role |
| Token not found | User never completed OAuth flow | Redirect to authorization |
| Audit gap | Error in async logging | Add fallback logging to console |

## Resources

- [Webflow OAuth Reference](https://developers.webflow.com/data/reference/oauth-app)
- [Webflow Scopes](https://developers.webflow.com/data/reference/scopes)
- [Webflow Authentication](https://developers.webflow.com/data/reference/authentication)

## Next Steps

For major migrations, see `webflow-migration-deep-dive`.
