# Juicebox Enterprise RBAC - Implementation Guide

Detailed implementation examples and code patterns.

## Role Hierarchy

```
Admin
├── Manager
│   ├── Senior Recruiter
│   │   └── Recruiter
│   └── Hiring Manager
├── Analyst (read-only)
└── API Service Account
```

## Instructions

### Step 1: Define Roles and Permissions
```typescript
// lib/rbac/permissions.ts
export enum Permission {
  // Search permissions
  SEARCH_READ = 'search:read',
  SEARCH_ADVANCED = 'search:advanced',
  SEARCH_EXPORT = 'search:export',

  // Profile permissions
  PROFILE_READ = 'profile:read',
  PROFILE_ENRICH = 'profile:enrich',
  PROFILE_CONTACT = 'profile:contact',
  PROFILE_NOTES = 'profile:notes',

  // Team permissions
  TEAM_VIEW = 'team:view',
  TEAM_MANAGE = 'team:manage',

  // Admin permissions
  ADMIN_SETTINGS = 'admin:settings',
  ADMIN_BILLING = 'admin:billing',
  ADMIN_AUDIT = 'admin:audit'
}

export enum Role {
  ADMIN = 'admin',
  MANAGER = 'manager',
  SENIOR_RECRUITER = 'senior_recruiter',
  RECRUITER = 'recruiter',
  HIRING_MANAGER = 'hiring_manager',
  ANALYST = 'analyst',
  SERVICE_ACCOUNT = 'service_account'
}

export const rolePermissions: Record<Role, Permission[]> = {
  [Role.ADMIN]: Object.values(Permission), // All permissions

  [Role.MANAGER]: [
    Permission.SEARCH_READ,
    Permission.SEARCH_ADVANCED,
    Permission.SEARCH_EXPORT,
    Permission.PROFILE_READ,
    Permission.PROFILE_ENRICH,
    Permission.PROFILE_CONTACT,
    Permission.PROFILE_NOTES,
    Permission.TEAM_VIEW,
    Permission.TEAM_MANAGE
  ],

  [Role.SENIOR_RECRUITER]: [
    Permission.SEARCH_READ,
    Permission.SEARCH_ADVANCED,
    Permission.SEARCH_EXPORT,
    Permission.PROFILE_READ,
    Permission.PROFILE_ENRICH,
    Permission.PROFILE_CONTACT,
    Permission.PROFILE_NOTES,
    Permission.TEAM_VIEW
  ],

  [Role.RECRUITER]: [
    Permission.SEARCH_READ,
    Permission.PROFILE_READ,
    Permission.PROFILE_CONTACT,
    Permission.PROFILE_NOTES
  ],

  [Role.HIRING_MANAGER]: [
    Permission.SEARCH_READ,
    Permission.PROFILE_READ,
    Permission.PROFILE_NOTES,
    Permission.TEAM_VIEW
  ],

  [Role.ANALYST]: [
    Permission.SEARCH_READ,
    Permission.PROFILE_READ,
    Permission.TEAM_VIEW
  ],

  [Role.SERVICE_ACCOUNT]: [
    Permission.SEARCH_READ,
    Permission.PROFILE_READ,
    Permission.PROFILE_ENRICH
  ]
};
```

### Step 2: Implement Permission Checker
```typescript
// lib/rbac/permission-checker.ts
export class PermissionChecker {
  constructor(private user: User) {}

  hasPermission(permission: Permission): boolean {
    const userPermissions = this.getUserPermissions();
    return userPermissions.includes(permission);
  }

  hasAnyPermission(permissions: Permission[]): boolean {
    return permissions.some(p => this.hasPermission(p));
  }

  hasAllPermissions(permissions: Permission[]): boolean {
    return permissions.every(p => this.hasPermission(p));
  }

  private getUserPermissions(): Permission[] {
    const role = this.user.role as Role;
    const basePermissions = rolePermissions[role] || [];

    // Add any custom permissions assigned to user
    const customPermissions = this.user.customPermissions || [];

    return [...new Set([...basePermissions, ...customPermissions])];
  }

  // Check permission with data-level access
  async canAccessProfile(profileId: string): Promise<boolean> {
    if (!this.hasPermission(Permission.PROFILE_READ)) {
      return false;
    }

    // Check team-level access
    if (this.user.teamRestrictions?.length > 0) {
      const profile = await db.profiles.findUnique({
        where: { id: profileId },
        select: { ownedByTeam: true }
      });
      return this.user.teamRestrictions.includes(profile?.ownedByTeam);
    }

    return true;
  }
}
```

### Step 3: Authorization Middleware
```typescript
// middleware/authorization.ts
import { Permission } from '../lib/rbac/permissions';
import { PermissionChecker } from '../lib/rbac/permission-checker';

export function requirePermission(...permissions: Permission[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user;

    if (!user) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const checker = new PermissionChecker(user);

    if (!checker.hasAllPermissions(permissions)) {
      await logAccessDenied(user, permissions, req);
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: permissions
      });
    }

    next();
  };
}

export function requireAnyPermission(...permissions: Permission[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user;

    if (!user) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const checker = new PermissionChecker(user);

    if (!checker.hasAnyPermission(permissions)) {
      await logAccessDenied(user, permissions, req);
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: permissions
      });
    }

    next();
  };
}

// Usage in routes
app.get('/api/search',
  requirePermission(Permission.SEARCH_READ),
  searchController.search
);

app.post('/api/profiles/:id/enrich',
  requirePermission(Permission.PROFILE_READ, Permission.PROFILE_ENRICH),
  profileController.enrich
);

app.get('/api/profiles/:id/contact',
  requirePermission(Permission.PROFILE_CONTACT),
  profileController.getContact
);
```

### Step 4: Team-Based Access Control
```typescript
// lib/rbac/team-access.ts
export class TeamAccessControl {
  constructor(private db: Database) {}

  async canAccessTeamData(userId: string, teamId: string): Promise<boolean> {
    const membership = await this.db.teamMemberships.findFirst({
      where: {
        userId,
        teamId,
        active: true
      }
    });

    return !!membership;
  }

  async filterByTeamAccess<T extends { teamId: string }>(
    userId: string,
    items: T[]
  ): Promise<T[]> {
    const userTeams = await this.getUserTeams(userId);
    return items.filter(item => userTeams.includes(item.teamId));
  }

  async getUserTeams(userId: string): Promise<string[]> {
    const memberships = await this.db.teamMemberships.findMany({
      where: { userId, active: true },
      select: { teamId: true }
    });
    return memberships.map(m => m.teamId);
  }
}
```

### Step 5: Audit Trail
```typescript
// lib/rbac/audit.ts
export class RBACauditLog {
  async logAccess(event: {
    userId: string;
    action: string;
    resource: string;
    resourceId?: string;
    granted: boolean;
    permissions: Permission[];
  }): Promise<void> {
    await db.rbacAuditLog.create({
      data: {
        ...event,
        timestamp: new Date(),
        ip: getCurrentIP(),
        userAgent: getCurrentUserAgent()
      }
    });

    // Alert on suspicious patterns
    if (!event.granted) {
      await this.checkSuspiciousActivity(event.userId);
    }
  }

  private async checkSuspiciousActivity(userId: string): Promise<void> {
    const recentDenials = await db.rbacAuditLog.count({
      where: {
        userId,
        granted: false,
        timestamp: { gte: new Date(Date.now() - 3600000) } // Last hour
      }
    });

    if (recentDenials > 10) {
      await alertService.send({
        type: 'security',
        message: `User ${userId} has ${recentDenials} access denials in last hour`,
        severity: 'high'
      });
    }
  }
}
```

## API Key Scopes

```typescript
// For service accounts, use scoped API keys
const serviceAccountKey = await juicebox.apiKeys.create({
  name: 'integration-service',
  scopes: [
    'search:read',
    'profiles:read',
    'profiles:enrich'
  ],
  expiresAt: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000), // 90 days
  ipAllowlist: ['10.0.0.0/8']
});
```

## RBAC Checklist

```markdown

## Enterprise RBAC Setup

### Role Definition
- [ ] Roles mapped to business functions
- [ ] Permissions granular and well-defined
- [ ] Role hierarchy documented
- [ ] Service account roles separate

### Implementation
- [ ] Permission checks on all endpoints
- [ ] Team-level access enforced
- [ ] Audit logging enabled
- [ ] Suspicious activity alerts

### Integration
- [ ] SSO/SAML configured
- [ ] Group sync from IdP
- [ ] JIT provisioning enabled
- [ ] Offboarding automation
```
