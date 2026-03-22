---
name: clickup-enterprise-rbac
description: |
  Implement ClickUp Enterprise SSO, OAuth 2.0 multi-workspace access,
  role-based permissions, and organization management via API v2.
  Trigger: "clickup SSO", "clickup RBAC", "clickup enterprise",
  "clickup roles", "clickup permissions", "clickup OAuth app", "clickup multi-workspace".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Enterprise RBAC

## Overview

Enterprise access patterns for ClickUp API v2. ClickUp's role system is built into the workspace, and the API surfaces roles via member objects. OAuth 2.0 enables multi-workspace apps where each user authorizes their own workspaces.

## ClickUp Role Model

ClickUp workspace members have role IDs in the API:

| Role ID | Role | Permissions |
|---------|------|-------------|
| 1 | Owner | Full control, billing, workspace settings |
| 2 | Admin | Manage members, spaces, integrations |
| 3 | Member | Create/edit tasks, spaces (per permission) |
| 4 | Guest | Limited access to shared items only |

```typescript
// Get workspace members with roles
async function getWorkspaceMembers(teamId: string) {
  const data = await clickupRequest(`/team/${teamId}`);

  return data.team.members.map((m: any) => ({
    userId: m.user.id,
    username: m.user.username,
    email: m.user.email,
    role: m.user.role,       // 1=owner, 2=admin, 3=member, 4=guest
    roleLabel: { 1: 'owner', 2: 'admin', 3: 'member', 4: 'guest' }[m.user.role],
  }));
}

// Check if user can perform admin operations
function canAdminister(member: { role: number }): boolean {
  return member.role <= 2; // Owner or Admin
}
```

## OAuth 2.0 Multi-Workspace App

Build apps that access multiple ClickUp workspaces on behalf of users.

```typescript
// Step 1: Redirect user to ClickUp authorization
function getOAuthUrl(state: string): string {
  return `https://app.clickup.com/api?client_id=${process.env.CLICKUP_CLIENT_ID}&redirect_uri=${encodeURIComponent(process.env.CLICKUP_REDIRECT_URI!)}&state=${state}`;
}

// Step 2: Exchange code for token
async function handleOAuthCallback(code: string) {
  const response = await fetch('https://api.clickup.com/api/v2/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_id: process.env.CLICKUP_CLIENT_ID,
      client_secret: process.env.CLICKUP_CLIENT_SECRET,
      code,
    }),
  });

  const { access_token } = await response.json();

  // Step 3: Discover which workspaces user authorized
  const teamsResponse = await fetch('https://api.clickup.com/api/v2/team', {
    headers: { 'Authorization': access_token },
  });
  const { teams } = await teamsResponse.json();

  return {
    token: access_token,   // Doesn't expire (but can be revoked)
    workspaces: teams.map((t: any) => ({ id: t.id, name: t.name })),
  };
}

// Step 4: Store per-user tokens
interface UserClickUpAuth {
  userId: string;
  clickupToken: string;      // Encrypt at rest
  authorizedWorkspaces: string[];
  connectedAt: Date;
}
```

## Permission Middleware

```typescript
// Express middleware that checks ClickUp workspace access
function requireClickUpAccess(requiredRole: number = 3) {
  return async (req: any, res: any, next: any) => {
    const userToken = req.user.clickupToken;
    const teamId = req.params.teamId || req.body.teamId;

    if (!userToken) {
      return res.status(401).json({ error: 'ClickUp not connected' });
    }

    // Verify user still has access to this workspace
    const teamsRes = await fetch('https://api.clickup.com/api/v2/team', {
      headers: { 'Authorization': userToken },
    });

    if (!teamsRes.ok) {
      return res.status(401).json({ error: 'ClickUp token expired or revoked' });
    }

    const { teams } = await teamsRes.json();
    const workspace = teams.find((t: any) => t.id === teamId);

    if (!workspace) {
      return res.status(403).json({ error: 'No access to this ClickUp workspace' });
    }

    // Check role level
    const userMember = workspace.members.find(
      (m: any) => m.user.id === req.user.clickupUserId
    );

    if (!userMember || userMember.user.role > requiredRole) {
      return res.status(403).json({
        error: `Requires role ${requiredRole} or higher`,
      });
    }

    req.clickupWorkspace = workspace;
    next();
  };
}

// Usage
app.delete('/api/clickup/:teamId/space/:spaceId',
  requireClickUpAccess(2), // Admin required
  async (req, res) => { /* ... */ }
);
```

## User Groups (API v2 "Teams")

```
GET    /api/v2/group                    Get User Groups
POST   /api/v2/team/{team_id}/group     Create User Group
PUT    /api/v2/group/{group_id}         Update User Group
DELETE /api/v2/group/{group_id}         Delete User Group
```

```typescript
// Create a user group for engineering team
await clickupRequest(`/team/${teamId}/group`, {
  method: 'POST',
  body: JSON.stringify({
    name: 'Engineering',
    member_ids: [183, 456, 789],
  }),
});
```

## Audit Trail

```typescript
interface ClickUpAuditEntry {
  timestamp: string;
  userId: number;
  workspaceId: string;
  action: string;
  resource: string;
  resourceId: string;
  success: boolean;
}

function logClickUpAction(entry: Omit<ClickUpAuditEntry, 'timestamp'>): void {
  const log: ClickUpAuditEntry = {
    ...entry,
    timestamp: new Date().toISOString(),
  };
  console.log(JSON.stringify({ level: 'audit', service: 'clickup', ...log }));
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| OAUTH_023/027 | Workspace not authorized | User must re-authorize via OAuth flow |
| Role check fails | User role changed in ClickUp | Re-fetch member data from API |
| Token revoked | User disconnected app | Handle 401, prompt re-auth |
| Guest access denied | Endpoint requires member+ | Check `role` field before API call |

## Resources

- [ClickUp Authentication](https://developer.clickup.com/docs/authentication)
- [ClickUp Get Access Token](https://developer.clickup.com/reference/getaccesstoken)
- [ClickUp API Terminology](https://developer.clickup.com/docs/general-v2-v3-api)

## Next Steps

For major migrations, see `clickup-migration-deep-dive`.
