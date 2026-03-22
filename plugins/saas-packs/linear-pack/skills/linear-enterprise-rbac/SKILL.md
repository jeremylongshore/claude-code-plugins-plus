---
name: linear-enterprise-rbac
description: |
  Implement enterprise role-based access control with Linear.
  Use when setting up team permissions, OAuth scopes,
  SAML SSO, SCIM provisioning, or audit logging.
  Trigger: "linear RBAC", "linear permissions", "linear SSO",
  "linear enterprise access", "linear role management", "linear SCIM".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, rbac]

---
# Linear Enterprise RBAC

## Overview
Implement role-based access control for Linear integrations. Linear provides built-in organization roles (Owner, Admin, Member, Guest), team-level access control, and fine-grained OAuth scopes. Enterprise plans add SAML 2.0 SSO and SCIM user provisioning.

## Prerequisites
- Linear Business or Enterprise plan (for SSO/SCIM)
- Organization admin access
- SSO provider (Okta, Azure AD, Google Workspace) for SAML
- Understanding of OAuth 2.0 scopes

## Instructions

### Step 1: Understand Linear's Built-In Roles

| Role | Capabilities |
|------|-------------|
| **Owner** | Full workspace control, billing, delete workspace |
| **Admin** | Manage members, teams, integrations, workspace settings |
| **Member** | Create/edit issues, access team-visible data |
| **Guest** | Read-only access to invited teams only |

These roles are fixed in Linear. Your application can layer additional permissions on top.

### Step 2: Map Application Roles to OAuth Scopes
```typescript
// src/auth/permissions.ts

// Available Linear OAuth scopes:
// read, write, issues:create, admin
// initiative:read, initiative:write
// customer:read, customer:write

const ROLE_SCOPES: Record<string, string[]> = {
  admin: ["read", "write", "issues:create", "admin"],
  manager: ["read", "write", "issues:create"],
  developer: ["read", "write", "issues:create"],
  viewer: ["read"],
};

const TEAM_ACCESS: Record<string, "member" | "guest" | "none"> = {
  admin: "member",
  manager: "member",
  developer: "member",
  viewer: "guest",
};
```

### Step 3: Permission Guard
```typescript
import { LinearClient } from "@linear/sdk";

interface UserContext {
  userId: string;
  role: string;
  linearClient: LinearClient;
  teamIds: string[];
}

class PermissionGuard {
  constructor(private ctx: UserContext) {}

  canAccessTeam(teamId: string): boolean {
    if (this.ctx.role === "admin") return true;
    return this.ctx.teamIds.includes(teamId);
  }

  async canModifyIssue(issueId: string): Promise<boolean> {
    if (this.ctx.role === "viewer") return false;

    const issue = await this.ctx.linearClient.issue(issueId);
    const team = await issue.team;
    return team ? this.canAccessTeam(team.id) : false;
  }

  canCreateIssue(): boolean {
    return ["admin", "manager", "developer"].includes(this.ctx.role);
  }

  canDeleteIssue(): boolean {
    return this.ctx.role === "admin";
  }

  canManageIntegration(): boolean {
    return this.ctx.role === "admin";
  }

  canAccessProject(projectTeamIds: string[]): boolean {
    if (this.ctx.role === "admin") return true;
    return projectTeamIds.some(id => this.ctx.teamIds.includes(id));
  }
}

// Express middleware
function requireRole(...allowedRoles: string[]) {
  return (req: any, res: any, next: any) => {
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: "Insufficient role" });
    }
    next();
  };
}

// Route protection
app.post("/api/issues", requireRole("admin", "manager", "developer"), createIssueHandler);
app.delete("/api/issues/:id", requireRole("admin"), deleteIssueHandler);
app.get("/api/issues", requireRole("admin", "manager", "developer", "viewer"), listIssuesHandler);
```

### Step 4: Scoped Client Factory
```typescript
// Create Linear clients with appropriate access per user
async function getClientForUser(userId: string): Promise<LinearClient> {
  const token = await getStoredOAuthToken(userId);
  if (!token) throw new Error("User not authenticated with Linear");
  return new LinearClient({ accessToken: token });
}

// Verify team membership via API
async function getUserTeamIds(client: LinearClient): Promise<string[]> {
  const viewer = await client.viewer;
  const memberships = await viewer.teamMemberships();

  const teamIds: string[] = [];
  for (const membership of memberships.nodes) {
    const team = await membership.team;
    if (team) teamIds.push(team.id);
  }
  return teamIds;
}
```

### Step 5: SAML SSO Configuration (Enterprise)
```typescript
// Linear Enterprise supports SAML 2.0 SSO
// Configuration: Linear Settings > Security > SAML

// After SSO login, verify user's Linear access
async function onSSOLogin(email: string): Promise<UserContext> {
  // Look up user's stored OAuth token
  const user = await db.users.findByEmail(email);
  if (!user?.linearAccessToken) {
    throw new Error("User must complete Linear OAuth after SSO login");
  }

  const client = new LinearClient({ accessToken: user.linearAccessToken });
  const viewer = await client.viewer;
  const teamIds = await getUserTeamIds(client);

  return {
    userId: user.id,
    role: mapLinearRoleToAppRole(viewer),
    linearClient: client,
    teamIds,
  };
}

function mapLinearRoleToAppRole(viewer: any): string {
  if (viewer.admin) return "admin";
  if (viewer.guest) return "viewer";
  return "developer";
}
```

### Step 6: SCIM Provisioning (Enterprise)
```typescript
// SCIM auto-syncs users and groups from your IdP to Linear
// Configuration: Linear Settings > Security > SCIM provisioning
// Endpoint: https://api.linear.app/scim/v2
// Bearer token: generated in Linear admin settings

// After SCIM syncs users, verify in your app
async function syncSCIMUsers(client: LinearClient) {
  const org = await client.organization;
  const members = await org.users();

  for (const user of members.nodes) {
    console.log(`${user.name} (${user.email}): admin=${user.admin}, guest=${user.guest}, active=${user.active}`);

    // Sync to your app's user database
    await db.users.upsert({
      email: user.email,
      name: user.name,
      linearId: user.id,
      role: user.admin ? "admin" : user.guest ? "viewer" : "developer",
      active: user.active,
    });
  }
}
```

### Step 7: Audit Logging
```typescript
interface AuditEntry {
  timestamp: string;
  userId: string;
  action: string;
  resource: string;
  resourceId: string;
  details: Record<string, unknown>;
}

function logAudit(entry: AuditEntry): void {
  // Write to audit log (database, SIEM, CloudWatch, etc.)
  console.log(JSON.stringify(entry));
}

// Wrap Linear operations with audit logging
async function auditedCreateIssue(
  ctx: UserContext,
  input: { teamId: string; title: string; [key: string]: any }
) {
  const guard = new PermissionGuard(ctx);
  if (!guard.canCreateIssue()) throw new Error("Forbidden");
  if (!guard.canAccessTeam(input.teamId)) throw new Error("No team access");

  const result = await ctx.linearClient.createIssue(input);

  logAudit({
    timestamp: new Date().toISOString(),
    userId: ctx.userId,
    action: "issue.create",
    resource: "Issue",
    resourceId: (await result.issue)?.id ?? "",
    details: { teamId: input.teamId, title: input.title },
  });

  return result;
}

async function auditedUpdateIssue(
  ctx: UserContext,
  issueId: string,
  updates: Record<string, unknown>
) {
  const guard = new PermissionGuard(ctx);
  if (!(await guard.canModifyIssue(issueId))) throw new Error("Forbidden");

  logAudit({
    timestamp: new Date().toISOString(),
    userId: ctx.userId,
    action: "issue.update",
    resource: "Issue",
    resourceId: issueId,
    details: updates,
  });

  return ctx.linearClient.updateIssue(issueId, updates);
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Forbidden` | Token lacks required scope | Request OAuth with correct `ROLE_SCOPES` |
| `Authentication required` | SSO session expired | Redirect to SAML IdP |
| SCIM sync fails | Invalid bearer token | Regenerate SCIM token in Linear admin |
| Guest can't create issue | Guest role is read-only | Upgrade to Member role in Linear |
| Team not accessible | User not added to team | Add user to team in Linear Settings |

## Examples

### List Organization Members by Role
```typescript
const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
const org = await client.organization;
const members = await org.users();

for (const user of members.nodes) {
  const role = user.admin ? "admin" : user.guest ? "guest" : "member";
  console.log(`${user.name} (${user.email}): ${role}`);
}
```

## Resources
- [Linear OAuth Scopes](https://linear.app/developers/oauth-2-0-authentication)
- [Linear SSO Guide](https://linear.app/docs/sso)
- [SCIM Provisioning](https://linear.app/docs/scim)
- [OAuth Actor Authorization](https://linear.app/developers/oauth-actor-authorization)
