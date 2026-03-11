# Apollo Enterprise RBAC - Implementation Guide

> Full implementation details and code examples for the `apollo-enterprise-rbac` skill.

# Apollo Enterprise RBAC

## Overview
Implement role-based access control for Apollo.io integrations with granular permissions, team isolation, and audit trails.

## Role Hierarchy

```
Super Admin
    |
    +-- Admin
    |     |
    |     +-- Sales Manager
    |     |       |
    |     |       +-- Sales Rep
    |     |
    |     +-- Marketing Manager
    |             |
    |             +-- Marketing User
    |
    +-- Read Only
```

## Permission Definitions

```typescript
// src/lib/rbac/permissions.ts
export const PERMISSIONS = {
  // Contact permissions
  'contacts:read': 'View contact information',
  'contacts:create': 'Add new contacts',
  'contacts:update': 'Edit contact information',
  'contacts:delete': 'Delete contacts',
  'contacts:export': 'Export contact data',
  'contacts:reveal_email': 'Reveal email addresses (uses credits)',

  // Search permissions
  'search:basic': 'Basic people search',
  'search:advanced': 'Advanced search filters',
  'search:bulk': 'Bulk search operations',

  // Enrichment permissions
  'enrich:person': 'Enrich individual contacts',
  'enrich:company': 'Enrich company data',
  'enrich:bulk': 'Bulk enrichment operations',

  // Sequence permissions
  'sequences:read': 'View sequences',
  'sequences:create': 'Create new sequences',
  'sequences:edit': 'Edit sequences',
  'sequences:delete': 'Delete sequences',
  'sequences:enroll': 'Add contacts to sequences',
  'sequences:send': 'Send emails through sequences',

  // Admin permissions
  'admin:users': 'Manage users',
  'admin:roles': 'Manage roles',
  'admin:settings': 'Configure settings',
  'admin:billing': 'View/manage billing',
  'admin:audit': 'View audit logs',
  'admin:api_keys': 'Manage API keys',
} as const;

export type Permission = keyof typeof PERMISSIONS;
```

## Role Definitions

```typescript
// src/lib/rbac/roles.ts
import { Permission } from './permissions';

interface Role {
  name: string;
  description: string;
  permissions: Permission[];
  inherits?: string[];
}

export const ROLES: Record<string, Role> = {
  super_admin: {
    name: 'Super Admin',
    description: 'Full system access',
    permissions: Object.keys(PERMISSIONS) as Permission[],
  },

  admin: {
    name: 'Admin',
    description: 'Administrative access without billing',
    permissions: [
      'contacts:read', 'contacts:create', 'contacts:update', 'contacts:delete', 'contacts:export',
      'search:basic', 'search:advanced', 'search:bulk',
      'enrich:person', 'enrich:company', 'enrich:bulk',
      'sequences:read', 'sequences:create', 'sequences:edit', 'sequences:delete', 'sequences:enroll', 'sequences:send',
      'admin:users', 'admin:roles', 'admin:settings', 'admin:audit',
    ],
  },

  sales_manager: {
    name: 'Sales Manager',
    description: 'Manage sales team and sequences',
    permissions: [
      'contacts:read', 'contacts:create', 'contacts:update', 'contacts:export', 'contacts:reveal_email',
      'search:basic', 'search:advanced',
      'enrich:person', 'enrich:company',
      'sequences:read', 'sequences:create', 'sequences:edit', 'sequences:enroll', 'sequences:send',
    ],
  },

  sales_rep: {
    name: 'Sales Representative',
    description: 'Basic sales access',
    permissions: [
      'contacts:read', 'contacts:create', 'contacts:update', 'contacts:reveal_email',
      'search:basic',
      'enrich:person',
      'sequences:read', 'sequences:enroll',
    ],
  },

  marketing_manager: {
    name: 'Marketing Manager',
    description: 'Manage marketing campaigns',
    permissions: [
      'contacts:read', 'contacts:export',
      'search:basic', 'search:advanced', 'search:bulk',
      'enrich:person', 'enrich:company', 'enrich:bulk',
      'sequences:read', 'sequences:create', 'sequences:edit',
    ],
  },

  marketing_user: {
    name: 'Marketing User',
    description: 'Basic marketing access',
    permissions: [
      'contacts:read',
      'search:basic',
      'sequences:read',
    ],
  },

  read_only: {
    name: 'Read Only',
    description: 'View-only access',
    permissions: [
      'contacts:read',
      'search:basic',
      'sequences:read',
    ],
  },
};
```

## RBAC Service

```typescript
// src/services/rbac/rbac.service.ts
import { User } from '../../models/user.model';
import { ROLES } from '../../lib/rbac/roles';
import { Permission } from '../../lib/rbac/permissions';

export class RBACService {
  async getUserPermissions(userId: string): Promise<Permission[]> {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      include: {
        roles: true,
        customPermissions: true,
      },
    });

    if (!user) {
      return [];
    }

    const permissions = new Set<Permission>();

    // Add role permissions
    for (const role of user.roles) {
      const roleDef = ROLES[role.name];
      if (roleDef) {
        roleDef.permissions.forEach(p => permissions.add(p));
      }
    }

    // Add custom permissions
    user.customPermissions.forEach(p => {
      if (p.granted) {
        permissions.add(p.permission as Permission);
      } else {
        permissions.delete(p.permission as Permission);
      }
    });

    return Array.from(permissions);
  }

  async hasPermission(userId: string, permission: Permission): Promise<boolean> {
    const permissions = await this.getUserPermissions(userId);
    return permissions.includes(permission);
  }

  async hasAnyPermission(userId: string, permissions: Permission[]): Promise<boolean> {
    const userPermissions = await this.getUserPermissions(userId);
    return permissions.some(p => userPermissions.includes(p));
  }

  async hasAllPermissions(userId: string, permissions: Permission[]): Promise<boolean> {
    const userPermissions = await this.getUserPermissions(userId);
    return permissions.every(p => userPermissions.includes(p));
  }
}

export const rbac = new RBACService();
```

## Permission Middleware

```typescript
// src/middleware/rbac.middleware.ts
import { Request, Response, NextFunction } from 'express';
import { rbac } from '../services/rbac/rbac.service';
import { Permission } from '../lib/rbac/permissions';

export function requirePermission(...permissions: Permission[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userId = req.user?.id;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const hasPermission = await rbac.hasAnyPermission(userId, permissions);

    if (!hasPermission) {
      // Audit failed access attempt
      await auditLog.create({
        action: 'PERMISSION_DENIED',
        actor: userId,
        resource: req.path,
        metadata: { requiredPermissions: permissions },
      });

      return res.status(403).json({
        error: 'Permission denied',
        required: permissions,
      });
    }

    next();
  };
}

// Usage in routes
router.get('/contacts',
  requirePermission('contacts:read'),
  contactController.list
);

router.post('/contacts',
  requirePermission('contacts:create'),
  contactController.create
);

router.delete('/contacts/:id',
  requirePermission('contacts:delete'),
  contactController.delete
);

router.post('/search/bulk',
  requirePermission('search:bulk', 'search:advanced'),
  searchController.bulkSearch
);
```

## Team-Based Access Control

```typescript
// src/services/rbac/team-access.ts
export class TeamAccessService {
  async getAccessibleContacts(
    userId: string,
    teamId: string
  ): Promise<string[]> {
    // Check user's team membership
    const membership = await prisma.teamMember.findFirst({
      where: { userId, teamId },
      include: { team: true },
    });

    if (!membership) {
      return [];
    }

    // Build access scope
    const accessScope = await this.buildAccessScope(userId, membership);

    // Return contact IDs user can access
    const contacts = await prisma.contact.findMany({
      where: accessScope,
      select: { id: true },
    });

    return contacts.map(c => c.id);
  }

  private async buildAccessScope(
    userId: string,
    membership: TeamMembership
  ): Promise<any> {
    // Team admins can see all team contacts
    if (membership.role === 'admin' || membership.role === 'manager') {
      return { teamId: membership.teamId };
    }

    // Regular members see own contacts + shared
    return {
      OR: [
        { ownerId: userId },
        { sharedWith: { some: { userId } } },
        { teamId: membership.teamId, isPublic: true },
      ],
    };
  }
}

// Middleware for team-scoped access
export function requireTeamAccess(resourceType: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userId = req.user?.id;
    const resourceId = req.params.id;

    const hasAccess = await teamAccess.canAccessResource(
      userId,
      resourceType,
      resourceId
    );

    if (!hasAccess) {
      return res.status(403).json({
        error: 'You do not have access to this resource',
      });
    }

    next();
  };
}
```

## API Key Scoping

```typescript
// src/lib/rbac/api-key-scope.ts
interface ApiKeyScope {
  permissions: Permission[];
  rateLimit: number;
  ipAllowlist?: string[];
  expiresAt?: Date;
}

export async function createScopedApiKey(
  userId: string,
  scope: ApiKeyScope
): Promise<string> {
  // Validate user has the permissions they're granting
  const userPermissions = await rbac.getUserPermissions(userId);
  const invalidPermissions = scope.permissions.filter(
    p => !userPermissions.includes(p)
  );

  if (invalidPermissions.length > 0) {
    throw new Error(`Cannot grant permissions you don't have: ${invalidPermissions.join(', ')}`);
  }

  // Generate key
  const apiKey = generateSecureKey();

  // Store with scope
  await prisma.apiKey.create({
    data: {
      key: hashApiKey(apiKey),
      userId,
      permissions: scope.permissions,
      rateLimit: scope.rateLimit,
      ipAllowlist: scope.ipAllowlist,
      expiresAt: scope.expiresAt,
    },
  });

  return apiKey;
}

// Middleware to enforce API key scope
export function enforceApiKeyScope(requiredPermissions: Permission[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const apiKey = req.headers['x-api-key'];

    if (!apiKey) {
      return res.status(401).json({ error: 'API key required' });
    }

    const keyRecord = await prisma.apiKey.findFirst({
      where: { key: hashApiKey(apiKey as string) },
    });

    if (!keyRecord) {
      return res.status(401).json({ error: 'Invalid API key' });
    }

    // Check expiration
    if (keyRecord.expiresAt && new Date() > keyRecord.expiresAt) {
      return res.status(401).json({ error: 'API key expired' });
    }

    // Check IP allowlist
    if (keyRecord.ipAllowlist?.length > 0) {
      const clientIp = req.ip;
      if (!keyRecord.ipAllowlist.includes(clientIp)) {
        return res.status(403).json({ error: 'IP not allowed' });
      }
    }

    // Check permissions
    const hasPermission = requiredPermissions.every(
      p => keyRecord.permissions.includes(p)
    );

    if (!hasPermission) {
      return res.status(403).json({
        error: 'API key lacks required permissions',
        required: requiredPermissions,
      });
    }

    next();
  };
}
```

## Admin Dashboard

```typescript
// src/routes/admin/rbac.ts
router.get('/users/:id/permissions',
  requirePermission('admin:users'),
  async (req, res) => {
    const permissions = await rbac.getUserPermissions(req.params.id);
    res.json({ permissions });
  }
);

router.post('/users/:id/roles',
  requirePermission('admin:roles'),
  async (req, res) => {
    const { roles } = req.body;
    await rbac.assignRoles(req.params.id, roles);
    res.json({ success: true });
  }
);

router.get('/audit/access-denied',
  requirePermission('admin:audit'),
  async (req, res) => {
    const logs = await prisma.auditLog.findMany({
      where: { action: 'PERMISSION_DENIED' },
      orderBy: { createdAt: 'desc' },
      take: 100,
    });
    res.json({ logs });
  }
);
```

## Output
- Role-based permission system
- Team-based access control
- API key scoping
- Permission middleware
- Admin dashboard endpoints

## Error Handling
| Issue | Resolution |
|-------|------------|
| Missing permissions | Request role upgrade |
| Team access denied | Check team membership |
| API key scope error | Regenerate with correct scope |
| Role conflict | Higher role takes precedence |

## Resources
- [RBAC Best Practices](https://auth0.com/docs/manage-users/access-control/rbac)
- [OWASP Access Control](https://owasp.org/www-community/Access_Control)
- [Apollo Team Permissions](https://knowledge.apollo.io/)

## Next Steps
Proceed to `apollo-migration-deep-dive` for migration strategies.
