---
name: notion-enterprise-rbac
description: |
  Configure Notion enterprise access control with OAuth, workspace permissions, and audit logging.
  Use when implementing OAuth public integrations, managing multi-workspace access,
  or building permission-aware Notion applications.
  Trigger with phrases like "notion SSO", "notion RBAC",
  "notion enterprise", "notion OAuth", "notion permissions", "notion multi-workspace".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Enterprise RBAC

## Overview
Implement enterprise-grade access control for Notion integrations: OAuth 2.0 for multi-workspace access, token management per workspace, permission-aware API calls, and audit logging.

## Prerequisites
- Notion public integration (for OAuth) or enterprise workspace
- Understanding of OAuth 2.0 flow
- Database for storing per-workspace tokens

## Instructions

### Step 1: Notion OAuth 2.0 Flow
Public integrations use OAuth to access other workspaces:

```typescript
import { Client } from '@notionhq/client';

// Step 1: Build authorization URL
function getAuthorizationUrl(state: string): string {
  const params = new URLSearchParams({
    client_id: process.env.NOTION_OAUTH_CLIENT_ID!,
    response_type: 'code',
    owner: 'user', // 'user' for user-level, 'workspace' for workspace-level
    redirect_uri: process.env.NOTION_REDIRECT_URI!,
    state, // CSRF protection
  });
  return `https://api.notion.com/v1/oauth/authorize?${params}`;
}

// Step 2: Exchange code for access token
async function exchangeCodeForToken(code: string) {
  const credentials = Buffer.from(
    `${process.env.NOTION_OAUTH_CLIENT_ID}:${process.env.NOTION_OAUTH_CLIENT_SECRET}`
  ).toString('base64');

  const response = await fetch('https://api.notion.com/v1/oauth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${credentials}`,
    },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      code,
      redirect_uri: process.env.NOTION_REDIRECT_URI,
    }),
  });

  const data = await response.json();
  // data contains:
  // access_token — use for API calls
  // bot_id — unique ID for this installation (use as primary key)
  // workspace_id — which workspace authorized
  // workspace_name — display name
  // workspace_icon — icon URL
  // owner — user or workspace that authorized
  // duplicated_template_id — if template was duplicated

  return data;
}

// Step 3: Create client for specific workspace
function getClientForWorkspace(accessToken: string): Client {
  return new Client({ auth: accessToken });
}
```

### Step 2: Token Storage and Management
```typescript
// Store tokens per workspace (use bot_id as primary key)
interface WorkspaceToken {
  botId: string;
  workspaceId: string;
  workspaceName: string;
  accessToken: string; // Encrypt at rest!
  ownerId: string;
  createdAt: Date;
}

// Example with a simple Map (use a database in production)
const tokenStore = new Map<string, WorkspaceToken>();

async function handleOAuthCallback(code: string) {
  const tokenData = await exchangeCodeForToken(code);

  tokenStore.set(tokenData.bot_id, {
    botId: tokenData.bot_id,
    workspaceId: tokenData.workspace_id,
    workspaceName: tokenData.workspace_name,
    accessToken: tokenData.access_token, // Encrypt this!
    ownerId: tokenData.owner?.user?.id ?? tokenData.owner?.workspace ?? '',
    createdAt: new Date(),
  });

  return tokenData;
}

function getNotionForWorkspace(botId: string): Client {
  const token = tokenStore.get(botId);
  if (!token) throw new Error(`No token for bot ${botId}`);
  return new Client({ auth: token.accessToken });
}
```

### Step 3: Permission-Aware API Calls
Notion's permission model is page-level: your integration can only access pages explicitly shared with it.

```typescript
import { isNotionClientError, APIErrorCode } from '@notionhq/client';

async function safePageAccess(notion: Client, pageId: string) {
  try {
    return await notion.pages.retrieve({ page_id: pageId });
  } catch (error) {
    if (isNotionClientError(error)) {
      switch (error.code) {
        case APIErrorCode.ObjectNotFound:
          // Page not shared with integration — NOT necessarily missing
          console.log('Page not accessible. User needs to share it with the integration.');
          return null;
        case APIErrorCode.RestrictedResource:
          // Integration doesn't have required capability
          console.log('Integration lacks required capability (read/write/insert).');
          return null;
        case APIErrorCode.Unauthorized:
          // Token revoked or expired
          console.log('Token expired. User needs to re-authorize.');
          return null;
      }
    }
    throw error;
  }
}
```

### Step 4: Application-Level Role Control
```typescript
// Your application's role system on top of Notion's permissions
enum AppRole {
  Admin = 'admin',
  Editor = 'editor',
  Viewer = 'viewer',
}

interface AppUser {
  id: string;
  role: AppRole;
  notionBotId: string; // Links to workspace token
}

const roleCapabilities: Record<AppRole, { canRead: boolean; canWrite: boolean; canDelete: boolean }> = {
  admin: { canRead: true, canWrite: true, canDelete: true },
  editor: { canRead: true, canWrite: true, canDelete: false },
  viewer: { canRead: true, canWrite: false, canDelete: false },
};

function checkAppPermission(user: AppUser, action: 'read' | 'write' | 'delete'): boolean {
  const caps = roleCapabilities[user.role];
  switch (action) {
    case 'read': return caps.canRead;
    case 'write': return caps.canWrite;
    case 'delete': return caps.canDelete;
  }
}

// Middleware
function requirePermission(action: 'read' | 'write' | 'delete') {
  return (req: any, res: any, next: any) => {
    if (!checkAppPermission(req.user, action)) {
      return res.status(403).json({ error: `Requires ${action} permission` });
    }
    next();
  };
}
```

### Step 5: Audit Logging
```typescript
interface AuditEntry {
  timestamp: string;
  userId: string;
  workspaceId: string;
  action: string;
  resource: { type: string; id: string };
  result: 'success' | 'denied' | 'error';
  metadata?: Record<string, any>;
}

async function auditLog(entry: Omit<AuditEntry, 'timestamp'>) {
  const full: AuditEntry = {
    ...entry,
    timestamp: new Date().toISOString(),
  };

  // Log to structured logging
  console.log(JSON.stringify({ level: 'audit', ...full }));

  // Optionally write to a Notion database for audit trail
  // (only if you need the audit log IN Notion)
  if (process.env.NOTION_AUDIT_DB_ID) {
    const notion = getNotionForWorkspace(entry.workspaceId);
    await notion.pages.create({
      parent: { database_id: process.env.NOTION_AUDIT_DB_ID },
      properties: {
        Action: { title: [{ text: { content: entry.action } }] },
        User: { rich_text: [{ text: { content: entry.userId } }] },
        Result: { select: { name: entry.result } },
        Resource: { rich_text: [{ text: { content: `${entry.resource.type}:${entry.resource.id}` } }] },
      },
    });
  }
}
```

### Step 6: Workspace Deauthorization
```typescript
// Handle when a user removes your integration
// Notion will stop sending webhook events
// Clean up stored tokens

async function handleDeauthorization(botId: string) {
  const token = tokenStore.get(botId);
  if (token) {
    await auditLog({
      userId: token.ownerId,
      workspaceId: token.workspaceId,
      action: 'deauthorize',
      resource: { type: 'workspace', id: token.workspaceId },
      result: 'success',
    });
    tokenStore.delete(botId);
  }
}
```

## Output
- OAuth 2.0 flow for multi-workspace access
- Per-workspace token storage and management
- Permission-aware API calls with graceful error handling
- Application-level role system
- Audit logging for compliance

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| OAuth callback fails | Wrong redirect URI | Match URI exactly in integration settings |
| Token expired | Notion doesn't use refresh tokens for internal | Re-authorize |
| Permission denied | Page not shared | User must add integration via Connections |
| Missing capability | Integration config | Edit capabilities in dashboard |

## Examples

### Express OAuth Route
```typescript
app.get('/auth/notion', (req, res) => {
  const state = crypto.randomUUID();
  req.session.oauthState = state;
  res.redirect(getAuthorizationUrl(state));
});

app.get('/auth/notion/callback', async (req, res) => {
  if (req.query.state !== req.session.oauthState) {
    return res.status(403).send('Invalid state');
  }
  const token = await handleOAuthCallback(req.query.code as string);
  res.redirect(`/dashboard?workspace=${token.workspace_name}`);
});
```

## Resources
- [Notion OAuth Authorization](https://developers.notion.com/docs/authorization)
- [Create a Token (OAuth)](https://developers.notion.com/reference/create-a-token)
- [Authentication Reference](https://developers.notion.com/reference/authentication)

## Next Steps
For major migrations, see `notion-migration-deep-dive`.
