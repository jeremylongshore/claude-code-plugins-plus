---
name: linear-enterprise-rbac
description: |
  Implement enterprise role-based access control with Linear.
  Use when setting up team permissions, implementing SSO,
  or managing access control for Linear integrations.
  Trigger with phrases like "linear RBAC", "linear permissions",
  "linear enterprise access", "linear SSO", "linear role management".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Enterprise RBAC

## Overview
Implement role-based access control for Linear integrations. Linear provides organization roles (Owner, Admin, Member, Guest), team-level access control, and OAuth scopes for API integrations. Enterprise plans add SAML SSO and SCIM provisioning.

## Prerequisites
- Linear Business or Enterprise plan
- Organization admin access
- SSO provider (Okta, Azure AD, Google Workspace) for SAML
- Understanding of OAuth 2.0 scopes

## Instructions

### Step 1: Define Application Roles
Map your application's permission model to Linear's built-in roles and API scopes.

```typescript
// roles/linear-permissions.ts

// Linear organization roles (built-in, cannot be customized)
// Owner  — full workspace control, billing, delete workspace
// Admin  — manage members, teams, integrations, workspace settings
// Member — create/edit issues, access team-visible data
// Guest  — read-only access to invited teams

// Map application roles to required Linear OAuth scopes
const ROLE_SCOPES: Record<string, string[]> = {
  admin: ["read", "write", "issues:create", "admin"],
  manager: ["read", "write", "issues:create"],
  developer: ["read", "write", "issues:create"],
  viewer: ["read"],
};

// Map roles to team access levels
const TEAM_ACCESS: Record<string, "member" | "guest" | "none"> = {
  admin: "member",
  manager: "member",
  developer: "member",
  viewer: "guest",
};
```

### Step 2: Permission Guard Implementation
```typescript
import { LinearClient } from "@linear/sdk";

interface UserContext {
  linearClient: LinearClient;
  role: string;
  teamIds: string[];
}

class PermissionGuard {
  constructor(private ctx: UserContext) {}

  async canAccessTeam(teamId: string): Promise<boolean> {
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

  canManageIntegration(): boolean {
    return this.ctx.role === "admin";
  }
}

// Usage in API route
async function updateIssueHandler(req: Request, ctx: UserContext) {
  const guard = new PermissionGuard(ctx);
  if (!(await guard.canModifyIssue(req.body.issueId))) {
    throw new Error("Forbidden: insufficient permissions to modify this issue");
  }
  await ctx.linearClient.updateIssue(req.body.issueId, req.body.updates);
}
```

### Step 3: Secure Linear Client Factory
```typescript
// Create scoped Linear clients per user role
function createScopedClient(apiKey: string, role: string): LinearClient {
  // Validate the API key has correct scopes for the role
  const requiredScopes = ROLE_SCOPES[role];
  if (!requiredScopes) {
    throw new Error(`Unknown role: ${role}`);
  }

  // The Linear SDK doesn't enforce scopes client-side,
  // but the API will reject operations outside the token's scope
  return new LinearClient({ apiKey });
}

// For multi-user OAuth apps, store per-user tokens
async function getClientForUser(userId: string): Promise<LinearClient> {
  const token = await getStoredToken(userId);
  if (!token) throw new Error("User not authenticated with Linear");
  return new LinearClient({ accessToken: token });
}
```

### Step 4: SAML SSO Integration (Enterprise)
```typescript
// Linear Enterprise supports SAML 2.0 SSO
// Configuration is done in Linear Settings > Security > SAML

// After SSO is configured, verify team membership via API
async function verifyTeamAccess(client: LinearClient): Promise<string[]> {
  const viewer = await client.viewer;
  const teamMemberships = await viewer.teamMemberships();
  return teamMemberships.nodes.map(async (m) => {
    const team = await m.team;
    return team!.id;
  });
}

// SCIM provisioning auto-syncs users and groups
// from your IdP to Linear. Configure in:
// Linear Settings > Security > SCIM provisioning
// Endpoint: https://api.linear.app/scim/v2
// Bearer token: generated in Linear admin settings
```

### Step 5: Audit Logging
```typescript
// Track all Linear API operations for compliance
interface AuditEntry {
  timestamp: string;
  userId: string;
  action: string;
  resource: string;
  resourceId: string;
  details: Record<string, unknown>;
}

function logAuditEvent(entry: AuditEntry): void {
  // Send to your audit log system (e.g., database, SIEM)
  console.log(JSON.stringify(entry));
}

// Wrap client operations with audit logging
async function auditedUpdateIssue(
  client: LinearClient,
  userId: string,
  issueId: string,
  updates: Record<string, unknown>
) {
  logAuditEvent({
    timestamp: new Date().toISOString(),
    userId,
    action: "issue.update",
    resource: "Issue",
    resourceId: issueId,
    details: updates,
  });
  return client.updateIssue(issueId, updates);
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Forbidden` | Token lacks required scope | Request OAuth scopes matching the role: `ROLE_SCOPES[role]` |
| `Authentication required` | SSO session expired | Redirect to SAML IdP for re-authentication |
| SCIM sync fails | Invalid bearer token | Regenerate SCIM token in Linear admin settings |
| Guest cannot create issue | Guest role is read-only | Upgrade user to Member role or assign to team |

## Examples

### API Middleware with Role Check
```typescript
// Express middleware
function requireRole(...allowedRoles: string[]) {
  return (req: any, res: any, next: any) => {
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: "Insufficient role" });
    }
    next();
  };
}

app.post("/api/issues", requireRole("admin", "manager", "developer"), createIssueHandler);
app.delete("/api/issues/:id", requireRole("admin"), deleteIssueHandler);
app.get("/api/issues", requireRole("admin", "manager", "developer", "viewer"), listIssuesHandler);
```

### List Organization Members by Role
```typescript
const org = await client.organization;
const members = await org.users();
for (const user of members.nodes) {
  console.log(`${user.name} (${user.email}): admin=${user.admin}, guest=${user.guest}`);
}
```

## Output
- Role-to-scope mapping for Linear OAuth applications
- Permission guard class with team-level access checks
- Scoped client factory creating role-appropriate Linear clients
- SAML SSO configuration guide with SCIM provisioning
- Audit logging wrapper for compliance tracking

## Resources
- [Linear OAuth Documentation](https://developers.linear.app/docs/oauth)
- [Linear SSO Guide](https://linear.app/docs/sso)
- [SCIM Provisioning](https://linear.app/docs/scim)
- [RBAC Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)

## Next Steps
Complete your Linear knowledge with `linear-migration-deep-dive`.
