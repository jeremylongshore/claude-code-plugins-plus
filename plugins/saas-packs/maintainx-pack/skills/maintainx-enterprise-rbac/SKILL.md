---
name: maintainx-enterprise-rbac
description: |
  Configure enterprise role-based access control for MaintainX integrations.
  Use when implementing SSO, managing organization-level permissions,
  or setting up enterprise access controls with MaintainX.
  Trigger with phrases like "maintainx rbac", "maintainx sso",
  "maintainx enterprise", "maintainx permissions", "maintainx roles".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Enterprise RBAC

## Overview
Configure enterprise role-based access control for MaintainX integrations with role definitions, location-scoped permissions, and audit logging.

## Prerequisites
- MaintainX Enterprise plan
- Understanding of RBAC concepts
- Node.js 18+

## MaintainX Role Hierarchy

```
Organization Admin
├── can manage all locations, users, teams, and settings
├── Full API access
│
Location Manager
├── can manage work orders, assets at assigned locations
├── API: filtered by locationId
│
Technician
├── can view/update assigned work orders
├── API: filtered by assigneeId
│
Viewer (Read-Only)
└── can view work orders, assets, locations
    └── API: GET endpoints only
```

## Instructions

### Step 1: Role Definitions

```typescript
// src/rbac/roles.ts

export type Role = 'admin' | 'manager' | 'technician' | 'viewer';

interface Permission {
  resource: string;
  actions: Array<'create' | 'read' | 'update' | 'delete'>;
  scope?: 'all' | 'location' | 'assigned';
}

export const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  admin: [
    { resource: 'workorders', actions: ['create', 'read', 'update', 'delete'], scope: 'all' },
    { resource: 'assets', actions: ['create', 'read', 'update', 'delete'], scope: 'all' },
    { resource: 'locations', actions: ['create', 'read', 'update', 'delete'], scope: 'all' },
    { resource: 'users', actions: ['create', 'read', 'update', 'delete'], scope: 'all' },
    { resource: 'teams', actions: ['create', 'read', 'update', 'delete'], scope: 'all' },
  ],
  manager: [
    { resource: 'workorders', actions: ['create', 'read', 'update'], scope: 'location' },
    { resource: 'assets', actions: ['create', 'read', 'update'], scope: 'location' },
    { resource: 'locations', actions: ['read'], scope: 'location' },
    { resource: 'users', actions: ['read'], scope: 'all' },
    { resource: 'teams', actions: ['read'], scope: 'all' },
  ],
  technician: [
    { resource: 'workorders', actions: ['read', 'update'], scope: 'assigned' },
    { resource: 'assets', actions: ['read'], scope: 'location' },
    { resource: 'locations', actions: ['read'], scope: 'location' },
  ],
  viewer: [
    { resource: 'workorders', actions: ['read'], scope: 'all' },
    { resource: 'assets', actions: ['read'], scope: 'all' },
    { resource: 'locations', actions: ['read'], scope: 'all' },
  ],
};
```

### Step 2: Permission Middleware

```typescript
// src/rbac/middleware.ts
import express from 'express';

interface AuthContext {
  userId: number;
  role: Role;
  locationIds: number[];  // Locations this user can access
}

function authorize(resource: string, action: 'create' | 'read' | 'update' | 'delete') {
  return (req: express.Request, res: express.Response, next: express.NextFunction) => {
    const auth = req.user as AuthContext;
    if (!auth) return res.status(401).json({ error: 'Not authenticated' });

    const perms = ROLE_PERMISSIONS[auth.role];
    const match = perms.find(
      (p) => p.resource === resource && p.actions.includes(action),
    );

    if (!match) {
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: { resource, action },
        role: auth.role,
      });
    }

    // Apply scope filtering
    if (match.scope === 'location') {
      req.query.locationId = auth.locationIds.join(',');
    } else if (match.scope === 'assigned') {
      req.query.assigneeId = String(auth.userId);
    }

    next();
  };
}

// Usage in routes
const router = express.Router();

router.get('/api/workorders', authorize('workorders', 'read'), async (req, res) => {
  const client = new MaintainXClient();
  const { data } = await client.getWorkOrders(req.query as any);
  res.json(data);
});

router.post('/api/workorders', authorize('workorders', 'create'), async (req, res) => {
  const client = new MaintainXClient();
  const { data } = await client.createWorkOrder(req.body);
  res.json(data);
});
```

### Step 3: Scoped API Keys

Create separate API keys per role to enforce server-side access control:

```typescript
// src/rbac/scoped-clients.ts

const scopedClients: Record<Role, MaintainXClient> = {
  admin: new MaintainXClient(process.env.MAINTAINX_API_KEY_ADMIN),
  manager: new MaintainXClient(process.env.MAINTAINX_API_KEY_MANAGER),
  technician: new MaintainXClient(process.env.MAINTAINX_API_KEY_TECH),
  viewer: new MaintainXClient(process.env.MAINTAINX_API_KEY_VIEWER),
};

function getClientForRole(role: Role): MaintainXClient {
  const client = scopedClients[role];
  if (!client) throw new Error(`No client configured for role: ${role}`);
  return client;
}
```

### Step 4: User and Team Management

```typescript
// Fetch all users and their roles
async function listUsersWithRoles(client: MaintainXClient) {
  const { data } = await client.getUsers({ limit: 100 });
  const { data: teams } = await client.request('GET', '/teams');

  const userTeams = new Map<number, string[]>();
  for (const team of teams.teams) {
    for (const member of team.members || []) {
      const existing = userTeams.get(member.id) || [];
      existing.push(team.name);
      userTeams.set(member.id, existing);
    }
  }

  for (const user of data.users) {
    const teamList = userTeams.get(user.id) || [];
    console.log(`  ${user.firstName} ${user.lastName} (${user.email})`);
    console.log(`    Role: ${user.role || 'N/A'} | Teams: ${teamList.join(', ') || 'None'}`);
  }
}
```

### Step 5: Audit Logging

```typescript
// src/rbac/audit.ts
function logAccess(auth: AuthContext, resource: string, action: string, result: 'allow' | 'deny') {
  const entry = {
    timestamp: new Date().toISOString(),
    type: 'access_control',
    userId: auth.userId,
    role: auth.role,
    resource,
    action,
    result,
    locationScope: auth.locationIds,
  };
  // Send to your log aggregation (CloudWatch, Datadog, etc.)
  console.log(JSON.stringify(entry));
}
```

## Output
- Role definitions mapping roles to resource permissions and scopes
- Express middleware enforcing RBAC on all API proxy routes
- Location-scoped and assignee-scoped query filtering
- Scoped API keys per role for defense in depth
- Audit logging for all access control decisions

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 403 on valid user | Missing permission for action | Check `ROLE_PERMISSIONS` mapping |
| Empty results for manager | Location scope filter too narrow | Verify `locationIds` in auth context |
| Scoped key missing | Environment variable not set | Add `MAINTAINX_API_KEY_{ROLE}` to env |
| Audit log gaps | Middleware not applied to route | Ensure `authorize()` is on all routes |

## Resources
- [MaintainX Enterprise](https://www.getmaintainx.com/enterprise)
- [OWASP Access Control Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html)
- [MaintainX API Reference](https://developer.maintainx.com/reference)

## Next Steps
For complete platform migration, see `maintainx-migration-deep-dive`.

## Examples

**Check if a user can perform an action**:

```typescript
function canPerform(role: Role, resource: string, action: string): boolean {
  const perms = ROLE_PERMISSIONS[role];
  return perms.some((p) => p.resource === resource && p.actions.includes(action as any));
}

console.log(canPerform('technician', 'workorders', 'update'));  // true
console.log(canPerform('technician', 'workorders', 'delete'));  // false
console.log(canPerform('viewer', 'workorders', 'read'));        // true
```
