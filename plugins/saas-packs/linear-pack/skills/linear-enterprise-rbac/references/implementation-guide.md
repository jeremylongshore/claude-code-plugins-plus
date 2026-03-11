# Linear Enterprise RBAC - Implementation Guide

Detailed implementation examples and code patterns.

## Linear Permission Model

### Built-in Roles
| Role | Scope | Permissions |
|------|-------|-------------|
| Organization Admin | Org-wide | Full access, billing, SSO |
| Organization Member | Org-wide | Access granted teams |
| Team Admin | Per-team | Manage team settings |
| Team Member | Per-team | Create/edit issues |
| Guest | Per-team | Limited view access |

### API Key Scopes
| Scope | Access Level |
|-------|-------------|
| `read` | Read-only access |
| `write` | Create and update |
| `issues:create` | Create issues only |
| `admin` | Administrative actions |

## Instructions

### Step 1: Define Application Roles
```typescript
// lib/rbac/roles.ts
export enum AppRole {
  ADMIN = "admin",
  MANAGER = "manager",
  DEVELOPER = "developer",
  VIEWER = "viewer",
}

export interface RolePermissions {
  canCreateIssues: boolean;
  canUpdateIssues: boolean;
  canDeleteIssues: boolean;
  canManageProjects: boolean;
  canManageCycles: boolean;
  canManageTeam: boolean;
  canViewMetrics: boolean;
  allowedTeams: string[] | "*";
  issueStateTransitions: string[];
}

export const ROLE_PERMISSIONS: Record<AppRole, RolePermissions> = {
  [AppRole.ADMIN]: {
    canCreateIssues: true,
    canUpdateIssues: true,
    canDeleteIssues: true,
    canManageProjects: true,
    canManageCycles: true,
    canManageTeam: true,
    canViewMetrics: true,
    allowedTeams: "*",
    issueStateTransitions: ["*"],
  },
  [AppRole.MANAGER]: {
    canCreateIssues: true,
    canUpdateIssues: true,
    canDeleteIssues: false,
    canManageProjects: true,
    canManageCycles: true,
    canManageTeam: false,
    canViewMetrics: true,
    allowedTeams: "*",
    issueStateTransitions: ["*"],
  },
  [AppRole.DEVELOPER]: {
    canCreateIssues: true,
    canUpdateIssues: true,
    canDeleteIssues: false,
    canManageProjects: false,
    canManageCycles: false,
    canManageTeam: false,
    canViewMetrics: false,
    allowedTeams: [], // Set per-user
    issueStateTransitions: ["Todo->InProgress", "InProgress->InReview", "InReview->Done"],
  },
  [AppRole.VIEWER]: {
    canCreateIssues: false,
    canUpdateIssues: false,
    canDeleteIssues: false,
    canManageProjects: false,
    canManageCycles: false,
    canManageTeam: false,
    canViewMetrics: false,
    allowedTeams: [],
    issueStateTransitions: [],
  },
};
```

### Step 2: Permission Guard Implementation
```typescript
// lib/rbac/guards.ts
import { LinearClient } from "@linear/sdk";
import { AppRole, ROLE_PERMISSIONS, RolePermissions } from "./roles";

interface UserContext {
  userId: string;
  email: string;
  role: AppRole;
  teamAccess: string[];
}

export class PermissionGuard {
  private permissions: RolePermissions;
  private userContext: UserContext;
  private linearClient: LinearClient;

  constructor(client: LinearClient, context: UserContext) {
    this.linearClient = client;
    this.userContext = context;
    this.permissions = {
      ...ROLE_PERMISSIONS[context.role],
      allowedTeams: context.teamAccess.length > 0
        ? context.teamAccess
        : ROLE_PERMISSIONS[context.role].allowedTeams,
    };
  }

  canAccessTeam(teamKey: string): boolean {
    if (this.permissions.allowedTeams === "*") return true;
    return this.permissions.allowedTeams.includes(teamKey);
  }

  canCreateIssue(teamKey: string): boolean {
    return this.permissions.canCreateIssues && this.canAccessTeam(teamKey);
  }

  canUpdateIssue(teamKey: string): boolean {
    return this.permissions.canUpdateIssues && this.canAccessTeam(teamKey);
  }

  canTransitionState(fromState: string, toState: string): boolean {
    const transitions = this.permissions.issueStateTransitions;
    if (transitions.includes("*")) return true;
    return transitions.includes(`${fromState}->${toState}`);
  }

  async assertCanCreateIssue(teamKey: string): Promise<void> {
    if (!this.canCreateIssue(teamKey)) {
      throw new ForbiddenError(
        `User ${this.userContext.email} cannot create issues in team ${teamKey}`
      );
    }
  }

  async assertCanUpdateIssue(issueId: string): Promise<void> {
    const issue = await this.linearClient.issue(issueId);
    const team = await issue.team;

    if (!this.canUpdateIssue(team?.key ?? "")) {
      throw new ForbiddenError(
        `User ${this.userContext.email} cannot update issues in team ${team?.key}`
      );
    }
  }
}
```

### Step 3: Secure Linear Client Factory
```typescript
// lib/rbac/secure-client.ts
import { LinearClient } from "@linear/sdk";
import { PermissionGuard } from "./guards";
import { UserContext } from "./types";

export class SecureLinearClient {
  private client: LinearClient;
  private guard: PermissionGuard;

  constructor(client: LinearClient, context: UserContext) {
    this.client = client;
    this.guard = new PermissionGuard(client, context);
  }

  async createIssue(input: {
    teamId: string;
    teamKey: string;
    title: string;
    description?: string;
  }) {
    await this.guard.assertCanCreateIssue(input.teamKey);

    return this.client.createIssue({
      teamId: input.teamId,
      title: input.title,
      description: input.description,
    });
  }

  async updateIssue(issueId: string, input: Record<string, unknown>) {
    await this.guard.assertCanUpdateIssue(issueId);

    return this.client.updateIssue(issueId, input);
  }

  async transitionIssue(issueId: string, newStateId: string) {
    const issue = await this.client.issue(issueId);
    const currentState = await issue.state;
    const newState = await this.client.workflowState(newStateId);

    if (!this.guard.canTransitionState(currentState?.name ?? "", newState.name)) {
      throw new ForbiddenError(
        `Cannot transition from ${currentState?.name} to ${newState.name}`
      );
    }

    return this.client.updateIssue(issueId, { stateId: newStateId });
  }

  // Filter issues by accessible teams
  async getAccessibleIssues(filter?: Record<string, unknown>) {
    const teams = await this.getAccessibleTeams();
    const teamKeys = teams.map(t => t.key);

    return this.client.issues({
      filter: {
        ...filter,
        team: { key: { in: teamKeys } },
      },
    });
  }

  private async getAccessibleTeams() {
    const allTeams = await this.client.teams();

    if (this.guard["permissions"].allowedTeams === "*") {
      return allTeams.nodes;
    }

    return allTeams.nodes.filter(t =>
      (this.guard["permissions"].allowedTeams as string[]).includes(t.key)
    );
  }
}
```

### Step 4: SSO Integration
```typescript
// lib/auth/sso.ts
import { OAuth2Client } from "google-auth-library";

interface SSOConfig {
  provider: "google" | "okta" | "azure";
  clientId: string;
  clientSecret: string;
  domain?: string;
}

interface SSOUser {
  email: string;
  name: string;
  groups: string[];
}

export async function verifySSOToken(
  token: string,
  config: SSOConfig
): Promise<SSOUser> {
  switch (config.provider) {
    case "google":
      return verifyGoogleToken(token, config);
    case "okta":
      return verifyOktaToken(token, config);
    case "azure":
      return verifyAzureToken(token, config);
    default:
      throw new Error(`Unknown SSO provider: ${config.provider}`);
  }
}

async function verifyGoogleToken(token: string, config: SSOConfig): Promise<SSOUser> {
  const client = new OAuth2Client(config.clientId);

  const ticket = await client.verifyIdToken({
    idToken: token,
    audience: config.clientId,
  });

  const payload = ticket.getPayload()!;

  return {
    email: payload.email!,
    name: payload.name!,
    groups: [], // Would come from Google Workspace groups API
  };
}

// Map SSO groups to app roles
export function mapGroupsToRole(groups: string[]): AppRole {
  if (groups.includes("linear-admins")) return AppRole.ADMIN;
  if (groups.includes("linear-managers")) return AppRole.MANAGER;
  if (groups.includes("linear-developers")) return AppRole.DEVELOPER;
  return AppRole.VIEWER;
}

// Map SSO groups to team access
export function mapGroupsToTeams(groups: string[]): string[] {
  const teamMapping: Record<string, string[]> = {
    "engineering": ["ENG", "PLATFORM", "INFRA"],
    "product": ["PROD", "DESIGN"],
    "all-teams": ["*"],
  };

  const teams = new Set<string>();
  for (const group of groups) {
    const mappedTeams = teamMapping[group];
    if (mappedTeams) {
      mappedTeams.forEach(t => teams.add(t));
    }
  }

  return Array.from(teams);
}
```

### Step 5: Audit Logging
```typescript
// lib/rbac/audit.ts
interface AuditEntry {
  timestamp: Date;
  userId: string;
  userEmail: string;
  action: string;
  resource: string;
  resourceId: string;
  teamKey: string;
  allowed: boolean;
  reason?: string;
}

export class AuditLogger {
  async log(entry: Omit<AuditEntry, "timestamp">): Promise<void> {
    const fullEntry: AuditEntry = {
      ...entry,
      timestamp: new Date(),
    };

    // Log to structured logging
    logger.info({
      event: "rbac_audit",
      ...fullEntry,
    });

    // Store in database for compliance
    await db.insert(auditLog).values(fullEntry);
  }

  async logAccess(
    user: UserContext,
    action: string,
    resource: string,
    resourceId: string,
    teamKey: string,
    allowed: boolean
  ): Promise<void> {
    await this.log({
      userId: user.userId,
      userEmail: user.email,
      action,
      resource,
      resourceId,
      teamKey,
      allowed,
      reason: allowed ? undefined : "Permission denied",
    });
  }
}

export const auditLogger = new AuditLogger();
```

### Step 6: API Middleware
```typescript
// middleware/rbac.ts
import { SecureLinearClient } from "../lib/rbac/secure-client";

export async function rbacMiddleware(req: Request, res: Response, next: NextFunction) {
  try {
    // Get user from session/JWT
    const user = await getUserFromRequest(req);

    // Create permission-aware client
    const linearClient = new LinearClient({
      apiKey: process.env.LINEAR_API_KEY!,
    });

    const secureClient = new SecureLinearClient(linearClient, {
      userId: user.id,
      email: user.email,
      role: user.role,
      teamAccess: user.teams,
    });

    // Attach to request
    req.linearClient = secureClient;

    next();
  } catch (error) {
    res.status(403).json({ error: "Access denied" });
  }
}
```
