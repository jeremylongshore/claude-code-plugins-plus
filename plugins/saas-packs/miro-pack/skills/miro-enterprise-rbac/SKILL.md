---
name: miro-enterprise-rbac
description: |
  Configure Miro Enterprise features: organization management, SCIM provisioning,
  board-level access control, audit logs, and SSO integration via REST API v2.
  Trigger with phrases like "miro SSO", "miro RBAC",
  "miro enterprise", "miro SCIM", "miro permissions", "miro organization".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, enterprise, rbac, scim]
compatible-with: claude-code
---

# Miro Enterprise RBAC

## Overview

Enterprise-grade access control for Miro REST API v2: organization and team management, SCIM user provisioning, board sharing with role-based permissions, and audit log access. Requires Miro Enterprise plan.

## Miro Access Hierarchy

```
Organization (Enterprise)
├── Team 1
│   ├── Board A (sharing: team only)
│   │   ├── Owner (full control)
│   │   ├── Co-owner (full control, can't delete board)
│   │   ├── Editor (can add/edit items)
│   │   ├── Commenter (can add comments only)
│   │   └── Viewer (read-only)
│   └── Board B
├── Team 2
│   └── Board C
└── Projects
    └── Project 1 (groups boards)
```

## Board Roles & Permissions

| Role | View | Comment | Edit Items | Share | Delete Board |
|------|------|---------|------------|-------|-------------|
| Viewer | Yes | No | No | No | No |
| Commenter | Yes | Yes | No | No | No |
| Editor | Yes | Yes | Yes | No | No |
| Co-owner | Yes | Yes | Yes | Yes | No |
| Owner | Yes | Yes | Yes | Yes | Yes |

## Board Member Management

```typescript
// List board members
// GET https://api.miro.com/v2/boards/{board_id}/members
const members = await miroFetch(`/v2/boards/${boardId}/members?limit=50`);
for (const member of members.data) {
  console.log(`${member.name} (${member.id}): role=${member.role}`);
}

// Share board with users
// POST https://api.miro.com/v2/boards/{board_id}/members
await miroFetch(`/v2/boards/${boardId}/members`, 'POST', {
  emails: ['dev@company.com', 'pm@company.com'],
  role: 'editor',        // 'viewer' | 'commenter' | 'editor' | 'coowner'
  message: 'You have been added to the sprint board',
});

// Update member role
// PATCH https://api.miro.com/v2/boards/{board_id}/members/{member_id}
await miroFetch(`/v2/boards/${boardId}/members/${memberId}`, 'PATCH', {
  role: 'commenter',
});

// Remove member from board
// DELETE https://api.miro.com/v2/boards/{board_id}/members/{member_id}
await miroFetch(`/v2/boards/${boardId}/members/${memberId}`, 'DELETE');
```

## Team Management (Enterprise)

```typescript
// List teams in organization
// GET https://api.miro.com/v2/orgs/{org_id}/teams (Enterprise)
const teams = await miroFetch(`/v2/orgs/${orgId}/teams?limit=50`);

// Get team details
// GET https://api.miro.com/v2/teams/{team_id}
const team = await miroFetch(`/v2/teams/${teamId}`);

// List team members
// GET https://api.miro.com/v2/teams/{team_id}/members
const teamMembers = await miroFetch(`/v2/teams/${teamId}/members?limit=100`);

// Invite user to team
// POST https://api.miro.com/v2/teams/{team_id}/members
await miroFetch(`/v2/teams/${teamId}/members`, 'POST', {
  emails: ['newdev@company.com'],
  role: 'member',         // 'member' | 'admin' | 'non_team'
});
```

## Organization Management (Enterprise)

```typescript
// Get organization info
// GET https://api.miro.com/v2/orgs/{org_id}
const org = await miroFetch(`/v2/orgs/${orgId}`);

// List organization members
// GET https://api.miro.com/v2/orgs/{org_id}/members
const orgMembers = await miroFetch(`/v2/orgs/${orgId}/members?limit=100`);
```

## SCIM User Provisioning (Enterprise)

Miro supports SCIM 2.0 for automated user lifecycle management from identity providers (Okta, Azure AD, OneLogin).

```typescript
// SCIM Base URL: https://miro.com/api/v1/scim/v2

// Create user via SCIM
// POST https://miro.com/api/v1/scim/v2/Users
const scimUser = await fetch('https://miro.com/api/v1/scim/v2/Users', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${scimToken}`,
    'Content-Type': 'application/scim+json',
  },
  body: JSON.stringify({
    schemas: ['urn:ietf:params:scim:schemas:core:2.0:User'],
    userName: 'newuser@company.com',
    name: { givenName: 'New', familyName: 'User' },
    emails: [{ value: 'newuser@company.com', type: 'work', primary: true }],
    active: true,
  }),
});

// List users via SCIM
// GET https://miro.com/api/v1/scim/v2/Users
const users = await fetch('https://miro.com/api/v1/scim/v2/Users?filter=active eq true', {
  headers: { 'Authorization': `Bearer ${scimToken}` },
});

// Deactivate user (deprovision)
// PATCH https://miro.com/api/v1/scim/v2/Users/{user_id}
await fetch(`https://miro.com/api/v1/scim/v2/Users/${scimUserId}`, {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${scimToken}`,
    'Content-Type': 'application/scim+json',
  },
  body: JSON.stringify({
    schemas: ['urn:ietf:params:scim:api:messages:2.0:PatchOp'],
    Operations: [{ op: 'replace', path: 'active', value: false }],
  }),
});

// Manage team membership via SCIM Groups
// GET https://miro.com/api/v1/scim/v2/Groups
// POST/PATCH Groups to add/remove team members
```

## Board Sharing Policies

Control how boards can be shared at creation time:

```typescript
// Create board with restrictive sharing
await miroFetch('/v2/boards', 'POST', {
  name: 'Confidential Strategy Board',
  policy: {
    sharingPolicy: {
      access: 'private',                        // Only invited members
      inviteToAccountAndBoardLinkAccess: 'no_access',
      organizationAccess: 'private',             // Not visible to org
      teamAccess: 'private',                     // Not visible to team
    },
    permissionsPolicy: {
      collaborationToolsStartAccess: 'all_editors',
      copyAccess: 'team_members',                // Only team can copy
      sharingAccess: 'owners_and_coowners',       // Only owners can share
    },
  },
});

// Create board with open team access
await miroFetch('/v2/boards', 'POST', {
  name: 'Team Brainstorming',
  teamId: teamId,
  policy: {
    sharingPolicy: {
      access: 'edit',                            // Team can edit by default
      teamAccess: 'edit',
    },
    permissionsPolicy: {
      sharingAccess: 'team_members_and_collaborators',
    },
  },
});
```

## Audit Logs (Enterprise)

```typescript
// Get audit logs — requires 'auditlogs:read' scope
// GET https://api.miro.com/v2/orgs/{org_id}/audit-logs
const logs = await miroFetch(
  `/v2/orgs/${orgId}/audit-logs?limit=100&createdAfter=${startDate}`
);

// Log entries include:
// - User actions (board created, item modified, member added)
// - Admin actions (team created, user deactivated, settings changed)
// - API actions (OAuth token issued, SCIM provisioning)

for (const entry of logs.data) {
  console.log({
    action: entry.action,
    actor: entry.actor?.email,
    target: entry.context?.boardId ?? entry.context?.teamId,
    timestamp: entry.createdAt,
  });
}
```

## Access Control Middleware

Enforce board-level permissions in your application:

```typescript
type BoardRole = 'viewer' | 'commenter' | 'editor' | 'coowner' | 'owner';

const ROLE_HIERARCHY: Record<BoardRole, number> = {
  viewer: 0,
  commenter: 1,
  editor: 2,
  coowner: 3,
  owner: 4,
};

function hasMinimumRole(userRole: BoardRole, requiredRole: BoardRole): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
}

async function requireBoardRole(boardId: string, userId: string, minRole: BoardRole) {
  const members = await miroFetch(`/v2/boards/${boardId}/members?limit=100`);
  const user = members.data.find((m: any) => m.id === userId);

  if (!user) {
    throw new Error('User is not a board member');
  }

  if (!hasMinimumRole(user.role, minRole)) {
    throw new Error(`Requires ${minRole} role, user has ${user.role}`);
  }
}

// Usage
await requireBoardRole(boardId, userId, 'editor');
// Throws if user doesn't have editor or higher role
```

## Required OAuth Scopes

| Feature | Required Scope |
|---------|---------------|
| Board members | `boards:read` (list) / `boards:write` (manage) |
| Team management | `team:read` / `team:write` |
| Organization | `organizations:read` |
| Audit logs | `auditlogs:read` |
| SCIM provisioning | SCIM token (separate from OAuth) |

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `insufficientPermissions` | 403 | Missing scope | Add required scope in app settings |
| `memberNotFound` | 404 | User not on board | Invite user first |
| `teamNotFound` | 404 | Wrong team ID or no access | Verify org/team hierarchy |
| `orgNotFound` | 404 | Not Enterprise plan | Upgrade to Enterprise |
| `scimTokenInvalid` | 401 | Wrong SCIM token | Generate new token in admin console |

## Resources

- [Miro Board Members](https://developers.miro.com/docs/rest-api-reference-guide)
- [Permission Scopes](https://developers.miro.com/reference/scopes)
- [SCIM API Introduction](https://developers.miro.com/reference/scim-introduction)
- [Teams API Guide](https://developers.miro.com/docs/teams-api-securely-manage-boards-teams-at-scale)
- [SCIM Groups (Teams)](https://developers.miro.com/docs/groups)

## Next Steps

For major migrations, see `miro-migration-deep-dive`.
