---
name: intercom-enterprise-rbac
description: |
  Configure Intercom enterprise OAuth, admin roles, and app-level access control.
  Use when implementing OAuth integration, managing admin permissions,
  or setting up organization-level controls for Intercom.
  Trigger with phrases like "intercom OAuth", "intercom RBAC",
  "intercom enterprise", "intercom roles", "intercom permissions", "intercom admin access".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Enterprise RBAC

## Overview

Configure enterprise-grade access control for Intercom integrations using OAuth scopes, admin role management, and app-level permission enforcement.

## Prerequisites

- Intercom workspace with admin access
- Understanding of OAuth 2.0 flows
- For public apps: OAuth configured in Developer Hub

## Intercom Admin Roles

Intercom has built-in admin roles that control workspace access:

| Role | API Access | Capabilities |
|------|-----------|-------------|
| Owner | Full | All operations, billing, workspace settings |
| Admin | Full | Manage contacts, conversations, content |
| Agent | Limited | Reply to conversations, view contacts |
| Custom roles | Configurable | Enterprise plan feature |

### Step 1: List Admins and Roles

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

// List all admins in the workspace
const adminList = await client.admins.list();
for (const admin of adminList.admins) {
  console.log(`${admin.name} (${admin.email})`);
  console.log(`  ID: ${admin.id}`);
  console.log(`  Type: ${admin.type}`);      // "admin" or "team"
  console.log(`  Active: ${admin.awayModeEnabled ? "Away" : "Available"}`);
}

// Find a specific admin by ID
const admin = await client.admins.find({ adminId: "12345" });
console.log(`Admin: ${admin.name} - ${admin.email}`);
```

## Instructions

### Step 2: OAuth Scope-Based Access Control

For public apps (OAuth), scopes control what your app can access in a customer's workspace.

```typescript
// OAuth configuration
const OAUTH_CONFIG = {
  clientId: process.env.INTERCOM_CLIENT_ID!,
  clientSecret: process.env.INTERCOM_CLIENT_SECRET!,
  redirectUri: "https://your-app.com/auth/intercom/callback",
};

// Step 1: Build authorization URL with minimal scopes
function getAuthUrl(state: string): string {
  return `https://app.intercom.com/oauth?` +
    `client_id=${OAUTH_CONFIG.clientId}&` +
    `state=${state}&` +
    `redirect_uri=${encodeURIComponent(OAUTH_CONFIG.redirectUri)}`;
}

// Step 2: Exchange authorization code for token
async function exchangeCode(code: string): Promise<{
  token: string;
  tokenType: string;
}> {
  const response = await fetch("https://api.intercom.io/auth/eagle/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: OAUTH_CONFIG.clientId,
      client_secret: OAUTH_CONFIG.clientSecret,
      code,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`OAuth token exchange failed: ${error.message}`);
  }

  const data = await response.json();
  return { token: data.token, tokenType: data.token_type };
}

// Step 3: Store token per workspace for multi-tenant
interface WorkspaceAuth {
  workspaceId: string;
  token: string;
  installedAt: Date;
  installedBy: string; // admin email
}

// Usage
const authUrl = getAuthUrl(crypto.randomUUID());
// Redirect user to authUrl
// On callback, exchange code for token
```

### Step 3: App-Level Permission Enforcement

Enforce permissions at the application layer based on the current admin.

```typescript
// Define permission levels for your app's operations
type IntercomPermission =
  | "contacts:read"
  | "contacts:write"
  | "contacts:delete"
  | "conversations:read"
  | "conversations:reply"
  | "conversations:assign"
  | "conversations:close"
  | "articles:read"
  | "articles:write"
  | "settings:manage";

// Map admin types to permissions
const ROLE_PERMISSIONS: Record<string, Set<IntercomPermission>> = {
  owner: new Set([
    "contacts:read", "contacts:write", "contacts:delete",
    "conversations:read", "conversations:reply", "conversations:assign", "conversations:close",
    "articles:read", "articles:write", "settings:manage",
  ]),
  admin: new Set([
    "contacts:read", "contacts:write",
    "conversations:read", "conversations:reply", "conversations:assign", "conversations:close",
    "articles:read", "articles:write",
  ]),
  agent: new Set([
    "contacts:read",
    "conversations:read", "conversations:reply",
  ]),
};

function checkPermission(adminRole: string, permission: IntercomPermission): boolean {
  return ROLE_PERMISSIONS[adminRole]?.has(permission) ?? false;
}

// Express middleware
function requirePermission(permission: IntercomPermission) {
  return (req: any, res: any, next: any) => {
    const adminRole = req.user?.intercomRole || "agent";
    if (!checkPermission(adminRole, permission)) {
      return res.status(403).json({
        error: "Forbidden",
        message: `Missing permission: ${permission}`,
        required: permission,
        currentRole: adminRole,
      });
    }
    next();
  };
}

// Usage
app.delete(
  "/api/contacts/:id",
  requirePermission("contacts:delete"),
  deleteContactHandler
);

app.post(
  "/api/conversations/:id/assign",
  requirePermission("conversations:assign"),
  assignConversationHandler
);
```

### Step 4: Team-Based Conversation Assignment

```typescript
// List teams in workspace
const admins = await client.admins.list();
const teams = admins.admins.filter(a => a.type === "team");
console.log("Teams:", teams.map(t => `${t.name} (${t.id})`));

// Assign conversation to team based on topic
async function routeConversation(
  conversationId: string,
  adminId: string,
  topic: string
): Promise<void> {
  const teamRouting: Record<string, string> = {
    billing: "team-billing-123",
    technical: "team-engineering-456",
    sales: "team-sales-789",
  };

  const teamId = teamRouting[topic];
  if (teamId) {
    await client.conversations.assign({
      conversationId,
      type: "team",
      adminId,
      assigneeId: teamId,
      body: `Routed to ${topic} team`,
    });
  }
}
```

### Step 5: Audit Logging for Admin Actions

```typescript
interface AdminAuditEntry {
  timestamp: string;
  adminId: string;
  adminEmail: string;
  action: string;
  resource: string;
  resourceId: string;
  success: boolean;
  ipAddress?: string;
}

async function auditAdminAction(entry: AdminAuditEntry): Promise<void> {
  // Log to your audit database
  await db.auditLog.insert(entry);

  // Track as Intercom data event for visibility
  await client.dataEvents.create({
    eventName: "admin-action-logged",
    createdAt: Math.floor(Date.now() / 1000),
    userId: entry.adminId,
    metadata: {
      action: entry.action,
      resource: entry.resource,
      resource_id: entry.resourceId,
      success: entry.success,
    },
  });

  // Alert on sensitive operations
  if (entry.action.includes("delete") || entry.action.includes("settings")) {
    console.warn(`[AUDIT] Sensitive action: ${entry.action} by ${entry.adminEmail}`);
  }
}
```

## OAuth Scope Reference

| Scope | Grants |
|-------|--------|
| Read admins | `GET /admins` |
| Read contacts | `GET /contacts`, `POST /contacts/search` |
| Write contacts | `POST /contacts`, `PUT /contacts/{id}`, `DELETE /contacts/{id}` |
| Read conversations | `GET /conversations`, `GET /conversations/{id}` |
| Write conversations | `POST /conversations`, reply, close, assign |
| Read messages | Read sent messages |
| Write messages | `POST /messages` |
| Read articles | `GET /articles`, `GET /help_center/collections` |
| Write articles | Create, update, delete articles and collections |
| Read tags | `GET /tags` |
| Write tags | Create, apply, remove tags |
| Read events | `GET /events` |
| Write events | `POST /events` |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| OAuth callback fails | Wrong redirect URI | Match exactly in Developer Hub |
| `forbidden` (403) | Missing OAuth scope | Add scope, user must re-authorize |
| Token revoked | User uninstalled app | Handle gracefully, notify admin |
| Admin not found | Admin left workspace | Remove from your system |
| Team assignment fails | Team ID invalid | List teams first with `admins.list()` |

## Resources

- [Authentication](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication)
- [Setting up OAuth](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/setting-up-oauth)
- [OAuth Scopes](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/oauth-scopes)
- [Admins API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/admins)

## Next Steps

For major migrations, see `intercom-migration-deep-dive`.
