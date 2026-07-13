# Gamma Enterprise RBAC - Implementation Details

## Define Roles and Permissions

```typescript
// models/rbac.ts
enum Permission {
  PRESENTATION_VIEW = 'presentation:view',
  PRESENTATION_CREATE = 'presentation:create',
  PRESENTATION_EDIT_OWN = 'presentation:edit:own',
  PRESENTATION_EDIT_TEAM = 'presentation:edit:team',
  PRESENTATION_EDIT_ALL = 'presentation:edit:all',
  PRESENTATION_DELETE = 'presentation:delete',
  PRESENTATION_EXPORT = 'presentation:export',
  TEAM_VIEW = 'team:view',
  TEAM_MANAGE = 'team:manage',
  WORKSPACE_VIEW = 'workspace:view',
  WORKSPACE_MANAGE = 'workspace:manage',
  BILLING_VIEW = 'billing:view',
  BILLING_MANAGE = 'billing:manage',
  API_KEYS_MANAGE = 'api_keys:manage',
}

interface Role {
  name: string;
  permissions: Permission[];
  inherits?: string;
}

const roles: Record<string, Role> = {
  viewer: {
    name: 'Viewer',
    permissions: [Permission.PRESENTATION_VIEW, Permission.TEAM_VIEW, Permission.WORKSPACE_VIEW],
  },
  editor: {
    name: 'Editor',
    permissions: [Permission.PRESENTATION_CREATE, Permission.PRESENTATION_EDIT_OWN, Permission.PRESENTATION_EXPORT],
    inherits: 'viewer',
  },
  team_lead: {
    name: 'Team Lead',
    permissions: [Permission.PRESENTATION_EDIT_TEAM, Permission.PRESENTATION_DELETE, Permission.TEAM_MANAGE],
    inherits: 'editor',
  },
  workspace_admin: {
    name: 'Workspace Admin',
    permissions: [Permission.PRESENTATION_EDIT_ALL, Permission.WORKSPACE_MANAGE, Permission.BILLING_VIEW],
    inherits: 'team_lead',
  },
  org_admin: {
    name: 'Organization Admin',
    permissions: [Permission.BILLING_MANAGE, Permission.API_KEYS_MANAGE],
    inherits: 'workspace_admin',
  },
};
```

## Permission Resolution Service

```typescript
// services/rbac-service.ts
class RBACService {
  private rolePermissions: Map<string, Set<Permission>> = new Map();

  constructor() {
    this.resolveRoleHierarchy();
  }

  private resolveRoleHierarchy() {
    const resolve = (roleName: string): Set<Permission> => {
      if (this.rolePermissions.has(roleName)) {
        return this.rolePermissions.get(roleName)!;
      }
      const role = roles[roleName];
      const permissions = new Set<Permission>(role.permissions);
      if (role.inherits) {
        const inherited = resolve(role.inherits);
        inherited.forEach(p => permissions.add(p));
      }
      this.rolePermissions.set(roleName, permissions);
      return permissions;
    };
    Object.keys(roles).forEach(resolve);
  }

  hasPermission(userRole: string, permission: Permission): boolean {
    const permissions = this.rolePermissions.get(userRole);
    return permissions?.has(permission) ?? false;
  }
}

export const rbac = new RBACService();
```

## Authorization Middleware

```typescript
// middleware/authorize.ts
function authorize(...requiredPermissions: Permission[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user;
    if (!user) return res.status(401).json({ error: 'Unauthorized' });

    const userRole = await getUserRole(user.id, req.params.workspaceId);
    const hasAllPermissions = requiredPermissions.every(permission =>
      rbac.hasPermission(userRole, permission)
    );

    if (!hasAllPermissions) {
      return res.status(403).json({ error: 'Forbidden', required: requiredPermissions, userRole });
    }
    next();
  };
}
```

## Resource-Level Authorization

```typescript
// services/resource-auth.ts
interface ResourcePolicy {
  action: string;
  conditions: (user: User, resource: any) => boolean;
}

const presentationPolicies: ResourcePolicy[] = [
  {
    action: 'edit',
    conditions: (user, presentation) => {
      if (presentation.ownerId === user.id) return true;
      if (user.role === 'team_lead' && presentation.teamId === user.teamId) return true;
      if (user.role === 'workspace_admin' || user.role === 'org_admin') return true;
      return false;
    },
  },
];
```

## Multi-Tenant Isolation

```typescript
// middleware/tenant.ts
async function tenantIsolation(req: Request, res: Response, next: NextFunction) {
  const user = req.user;
  const workspaceId = req.params.workspaceId || req.headers['x-workspace-id'];

  const membership = await db.workspaceMemberships.findUnique({
    where: { userId_workspaceId: { userId: user.id, workspaceId } },
  });

  if (!membership) {
    return res.status(403).json({ error: 'Not a member of this workspace' });
  }

  req.workspace = await db.workspaces.findUnique({ where: { id: workspaceId } });
  req.userRole = membership.role;
  next();
}

app.use('/api/workspaces/:workspaceId', tenantIsolation);
```

## Audit Authorization Events

```typescript
// lib/auth-audit.ts
async function logAuthorizationEvent(
  userId: string, action: string, resource: string,
  resourceId: string, granted: boolean, reason?: string
) {
  await db.authAuditLog.create({
    data: { userId, action, resource, resourceId, granted, reason, timestamp: new Date() },
  });

  if (!granted) {
    metrics.increment('authorization.denied', { action, resource });
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
