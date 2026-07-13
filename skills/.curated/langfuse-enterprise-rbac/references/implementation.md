# Langfuse Enterprise RBAC - Implementation Details

## Role-Based Access Implementation

```typescript
enum LangfuseRole { Owner = "owner", Admin = "admin", Member = "member", Viewer = "viewer", ApiOnly = "api_only" }

const ROLE_PERMISSIONS: Record<LangfuseRole, LangfusePermissions> = {
  [LangfuseRole.Owner]: { canViewDashboard: true, canReadTraces: true, canWriteTraces: true, canManageSettings: true, canManageMembers: true, canManageBilling: true, canCreateApiKeys: true, canDeleteData: true },
  [LangfuseRole.Admin]: { canViewDashboard: true, canReadTraces: true, canWriteTraces: true, canManageSettings: true, canManageMembers: true, canManageBilling: false, canCreateApiKeys: true, canDeleteData: true },
  [LangfuseRole.Member]: { canViewDashboard: true, canReadTraces: true, canWriteTraces: true, canManageSettings: false, canManageMembers: false, canManageBilling: false, canCreateApiKeys: false, canDeleteData: false },
  [LangfuseRole.Viewer]: { canViewDashboard: true, canReadTraces: true, canWriteTraces: false, canManageSettings: false, canManageMembers: false, canManageBilling: false, canCreateApiKeys: false, canDeleteData: false },
  [LangfuseRole.ApiOnly]: { canViewDashboard: false, canReadTraces: true, canWriteTraces: true, canManageSettings: false, canManageMembers: false, canManageBilling: false, canCreateApiKeys: false, canDeleteData: false },
};

function checkPermission(role: LangfuseRole, permission: keyof LangfusePermissions): void {
  if (!ROLE_PERMISSIONS[role][permission]) {
    throw new ForbiddenError(`Permission denied: ${permission} requires higher role than ${role}`);
  }
}
```

## Scoped API Keys

```typescript
interface ScopedApiKey {
  publicKey: string; secretKey: string; name: string;
  scope: { permissions: ("read" | "write")[]; projects?: string[]; environments?: string[]; ipAllowlist?: string[]; rateLimit?: number; };
}

class ScopedLangfuseClient {
  trace(params) {
    if (!this.scope.permissions.includes("write")) throw new ForbiddenError("No write permission");
    if (this.scope.projects?.length) {
      const projectId = params.metadata?.projectId;
      if (projectId && !this.scope.projects.includes(projectId)) throw new ForbiddenError("Not authorized for project");
    }
    return this.langfuse.trace(params);
  }
}
```

## Project-Based Access Control

```typescript
class ProjectAccessController {
  async getUserRole(userId: string, projectId: string): Promise<LangfuseRole | null> {
    const project = this.projects.get(projectId);
    const member = project?.members.find(m => m.userId === userId);
    return member?.role || null;
  }

  async addMember(projectId: string, member, addedBy: string) {
    const adderRole = await this.getUserRole(addedBy, projectId);
    if (!adderRole || !hasPermission(adderRole, "canManageMembers")) throw new ForbiddenError("Cannot add members");
    if (this.isHigherRole(member.role, adderRole)) throw new ForbiddenError("Cannot add higher role");
    // Add member
  }
}
```

## SSO Integration

```typescript
class LangfuseSSO {
  mapGroupsToRole(groups: string[]): LangfuseRole {
    for (const group of groups) {
      if (this.config.groupMapping[group]) return this.config.groupMapping[group];
    }
    return LangfuseRole.Viewer;
  }

  async handleSAMLAssertion(assertion) {
    if (!assertion.user.email.endsWith(`@${this.config.domain}`)) throw new UnauthorizedError("Domain not allowed");
    return { userId: assertion.user.id, email: assertion.user.email, role: this.mapGroupsToRole(assertion.user.groups) };
  }
}

// Example config
const ssoConfig = {
  provider: "okta", domain: "company.com",
  groupMapping: { "Engineering-Admins": LangfuseRole.Admin, "Engineering": LangfuseRole.Member, "Data-Team": LangfuseRole.Viewer },
};
```

## RBAC Audit Logging

```typescript
class RBACAuditLogger {
  async log(event) {
    const auditEvent = { ...event, timestamp: new Date() };
    await this.persist(auditEvent);
    if (event.action === "permission_denied") await this.alertSecurityTeam(auditEvent);
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
