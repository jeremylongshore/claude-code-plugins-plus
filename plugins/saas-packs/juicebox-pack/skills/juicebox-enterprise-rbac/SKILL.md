---
name: juicebox-enterprise-rbac
description: |
  Configure Juicebox enterprise RBAC with role definitions, permission guards,
  team-based access control, and audit logging.
  Use when restricting search/enrichment/export by role, isolating candidate pools
  per team, or building authorization middleware for Juicebox API operations.
  Trigger with phrases like "juicebox RBAC", "juicebox permissions",
  "juicebox access control", "juicebox team permissions".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Enterprise RBAC

## Overview

Juicebox search/enrichment/export operations touch sensitive candidate data and need role-based gates. This skill defines four roles (admin, recruiter, hiring_manager, viewer), wires permission guards into Express middleware, isolates candidate pools by team, and logs every access decision for audit.

## Prerequisites

- Juicebox API credentials (`username` and `api_token`)
- Node.js 18+ with TypeScript and Express
- Database with Prisma ORM (PostgreSQL recommended)
- Identity provider for SSO (Okta, Auth0, or Azure AD) on enterprise plan

## Instructions

### Step 1: Define roles and their permissions

Map four business roles to granular permissions covering search, enrichment, contact reveal, export, and administration.

```typescript
// lib/rbac/permissions.ts
export enum Permission {
  SEARCH_READ = 'search:read',
  SEARCH_ADVANCED = 'search:advanced',
  SEARCH_EXPORT = 'search:export',

  PROFILE_READ = 'profile:read',
  PROFILE_ENRICH = 'profile:enrich',
  PROFILE_CONTACT = 'profile:contact',
  PROFILE_NOTES = 'profile:notes',

  TEAM_VIEW = 'team:view',
  TEAM_MANAGE = 'team:manage',

  ADMIN_SETTINGS = 'admin:settings',
  ADMIN_BILLING = 'admin:billing',
  ADMIN_AUDIT = 'admin:audit'
}

export enum Role {
  ADMIN = 'admin',
  RECRUITER = 'recruiter',
  HIRING_MANAGER = 'hiring_manager',
  VIEWER = 'viewer'
}

export const rolePermissions: Record<Role, Permission[]> = {
  [Role.ADMIN]: Object.values(Permission),

  [Role.RECRUITER]: [
    Permission.SEARCH_READ,
    Permission.SEARCH_ADVANCED,
    Permission.SEARCH_EXPORT,
    Permission.PROFILE_READ,
    Permission.PROFILE_ENRICH,
    Permission.PROFILE_CONTACT,
    Permission.PROFILE_NOTES,
    Permission.TEAM_VIEW
  ],

  [Role.HIRING_MANAGER]: [
    Permission.SEARCH_READ,
    Permission.PROFILE_READ,
    Permission.PROFILE_NOTES,
    Permission.TEAM_VIEW
  ],

  [Role.VIEWER]: [
    Permission.SEARCH_READ,
    Permission.PROFILE_READ,
    Permission.TEAM_VIEW
  ]
};
```

| Role | Search | Enrich | Contact reveal | Export | Team manage | Admin |
|------|--------|--------|----------------|--------|-------------|-------|
| admin | all | yes | yes | yes | yes | yes |
| recruiter | basic + advanced | yes | yes | yes | view only | no |
| hiring_manager | basic only | no | no | no | view only | no |
| viewer | basic only | no | no | no | view only | no |

### Step 2: Build the permission checker

A stateless checker that resolves a user's effective permissions from their role plus any custom overrides.

```typescript
// lib/rbac/permission-checker.ts
import { Permission, Role, rolePermissions } from './permissions';

interface User {
  id: string;
  role: Role;
  customPermissions?: Permission[];
  teamIds: string[];
}

export class PermissionChecker {
  private readonly effectivePermissions: Set<Permission>;

  constructor(private user: User) {
    const base = rolePermissions[user.role] ?? [];
    const custom = user.customPermissions ?? [];
    this.effectivePermissions = new Set([...base, ...custom]);
  }

  has(permission: Permission): boolean {
    return this.effectivePermissions.has(permission);
  }

  hasAll(permissions: Permission[]): boolean {
    return permissions.every(p => this.effectivePermissions.has(p));
  }

  hasAny(permissions: Permission[]): boolean {
    return permissions.some(p => this.effectivePermissions.has(p));
  }

  canAccessTeam(teamId: string): boolean {
    if (this.user.role === Role.ADMIN) return true;
    return this.user.teamIds.includes(teamId);
  }
}
```

### Step 3: Wire permission guards into Express middleware

Create reusable middleware that rejects requests before they reach Juicebox API calls.

```typescript
// middleware/authorization.ts
import { Request, Response, NextFunction } from 'express';
import { Permission } from '../lib/rbac/permissions';
import { PermissionChecker } from '../lib/rbac/permission-checker';

export function requirePermissions(...permissions: Permission[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const checker = new PermissionChecker(req.user);

    if (!checker.hasAll(permissions)) {
      logAccessDenied(req.user.id, permissions, req.path);
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: permissions,
        your_role: req.user.role
      });
    }

    next();
  };
}

function logAccessDenied(userId: string, required: Permission[], path: string): void {
  console.log(JSON.stringify({
    event: 'access_denied',
    userId,
    required,
    path,
    timestamp: new Date().toISOString()
  }));
}

// Mount on routes
import { Router } from 'express';
const router = Router();

// Search — all roles can read, but export needs SEARCH_EXPORT
router.get('/api/search',
  requirePermissions(Permission.SEARCH_READ),
  searchController.search
);

router.post('/api/search/export',
  requirePermissions(Permission.SEARCH_READ, Permission.SEARCH_EXPORT),
  searchController.exportResults
);

// Enrichment — recruiter+ only
router.post('/api/profiles/:id/enrich',
  requirePermissions(Permission.PROFILE_READ, Permission.PROFILE_ENRICH),
  profileController.enrich
);

// Contact reveal — recruiter+ only
router.get('/api/profiles/:id/contact',
  requirePermissions(Permission.PROFILE_CONTACT),
  profileController.getContact
);
```

### Step 4: Implement team-based access control

Restrict which candidate pools each team can see. A recruiter on the "Engineering" team cannot view candidates sourced by the "Sales" team.

```typescript
// lib/rbac/team-access.ts
import { PrismaClient } from '@prisma/client';

export class TeamAccessControl {
  constructor(private db: PrismaClient) {}

  async filterByTeamAccess<T extends { teamId: string }>(
    userId: string,
    userTeamIds: string[],
    items: T[]
  ): Promise<T[]> {
    return items.filter(item => userTeamIds.includes(item.teamId));
  }

  async assertTeamAccess(userId: string, targetTeamId: string): Promise<void> {
    const membership = await this.db.teamMemberships.findFirst({
      where: { userId, teamId: targetTeamId, active: true }
    });

    if (!membership) {
      throw new TeamAccessError(
        `User ${userId} is not a member of team ${targetTeamId}`
      );
    }
  }
}

export class TeamAccessError extends Error {
  readonly statusCode = 403;
  constructor(message: string) {
    super(message);
    this.name = 'TeamAccessError';
  }
}

// Middleware that filters search results by team
export function enforceTeamScope() {
  return async (req: Request, res: Response, next: NextFunction) => {
    const checker = new PermissionChecker(req.user);

    // Admins see everything
    if (req.user.role === 'admin') return next();

    // Inject team filter into Juicebox search params
    req.juiceboxFilters = {
      ...req.juiceboxFilters,
      teamIds: req.user.teamIds
    };

    next();
  };
}
```

### Step 5: Add audit logging for every access decision

Log grants and denials with enough context for compliance review.

```typescript
// lib/rbac/audit-log.ts
import { Permission } from './permissions';

interface AuditEntry {
  userId: string;
  action: string;
  resource: string;
  resourceId?: string;
  granted: boolean;
  permissions: Permission[];
  ip: string;
  userAgent: string;
  timestamp: Date;
}

export class RBACAuditLog {
  constructor(private db: PrismaClient) {}

  async log(entry: AuditEntry): Promise<void> {
    await this.db.rbacAuditLog.create({ data: entry });

    if (!entry.granted) {
      await this.checkForBruteForce(entry.userId);
    }
  }

  private async checkForBruteForce(userId: string): Promise<void> {
    const oneHourAgo = new Date(Date.now() - 3_600_000);
    const denials = await this.db.rbacAuditLog.count({
      where: {
        userId,
        granted: false,
        timestamp: { gte: oneHourAgo }
      }
    });

    if (denials > 10) {
      console.log(JSON.stringify({
        event: 'security_alert',
        type: 'excessive_access_denials',
        userId,
        denials_last_hour: denials,
        severity: 'high'
      }));
    }
  }

  async getAuditTrail(
    userId: string,
    since: Date
  ): Promise<AuditEntry[]> {
    return this.db.rbacAuditLog.findMany({
      where: { userId, timestamp: { gte: since } },
      orderBy: { timestamp: 'desc' },
      take: 500
    });
  }
}
```

## Output

- `lib/rbac/permissions.ts` — Role enum, Permission enum, role-to-permission mapping
- `lib/rbac/permission-checker.ts` — stateless checker with `has`, `hasAll`, `hasAny`, `canAccessTeam`
- `middleware/authorization.ts` — Express middleware factory `requirePermissions()` with route examples
- `lib/rbac/team-access.ts` — team membership check, result filtering, team scope middleware
- `lib/rbac/audit-log.ts` — audit entry persistence with brute-force detection

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `401 Authentication required` | No user object on request (JWT missing or invalid) | Verify JWT middleware runs before authorization middleware |
| `403 Insufficient permissions` | User's role lacks required permission for the endpoint | Check `rolePermissions` mapping; grant via custom permissions if role is correct |
| `403 TeamAccessError` | User tried to access a candidate pool owned by another team | Add user to the target team via admin panel, or use admin role |
| `security_alert: excessive_access_denials` | Same user denied 10+ times in one hour | Investigate whether user role is misconfigured or account is compromised |
| `P2002 Unique constraint failed` | Duplicate audit log entry (race condition) | Add `@@unique([userId, timestamp, action])` with millisecond precision, or use `createMany` with `skipDuplicates` |

## Examples

**Guard a Juicebox enrichment endpoint and log the decision:**

```typescript
import { PermissionChecker } from './lib/rbac/permission-checker';
import { RBACAuditLog } from './lib/rbac/audit-log';
import { Permission, Role } from './lib/rbac/permissions';
import { prisma } from './lib/db';

const user = { id: 'u_123', role: Role.HIRING_MANAGER, teamIds: ['team_eng'], customPermissions: [] };
const checker = new PermissionChecker(user);
const audit = new RBACAuditLog(prisma);

const canEnrich = checker.has(Permission.PROFILE_ENRICH);
// false — hiring managers cannot enrich

await audit.log({
  userId: user.id,
  action: 'profile:enrich',
  resource: 'profile',
  resourceId: 'prof_456',
  granted: canEnrich,
  permissions: [Permission.PROFILE_ENRICH],
  ip: '10.0.1.50',
  userAgent: 'internal-service/1.0',
  timestamp: new Date()
});
```

**Filter search results by team scope:**

```typescript
import { TeamAccessControl } from './lib/rbac/team-access';
import { prisma } from './lib/db';

const teamAccess = new TeamAccessControl(prisma);

const allResults = [
  { id: 'p1', name: 'Alice', teamId: 'team_eng' },
  { id: 'p2', name: 'Bob', teamId: 'team_sales' },
  { id: 'p3', name: 'Carol', teamId: 'team_eng' }
];

const visible = await teamAccess.filterByTeamAccess(
  'u_123',
  ['team_eng'],
  allResults
);
// [{ id: 'p1', name: 'Alice', teamId: 'team_eng' }, { id: 'p3', name: 'Carol', teamId: 'team_eng' }]
```

## Resources

- [Juicebox API authentication](https://juicebox.ai/docs)
- [OWASP access control cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html)
- [Prisma authorization patterns](https://www.prisma.io/docs/guides/authorization)

## Next Steps

After RBAC, see `juicebox-data-handling` for PII classification and GDPR compliance on the data these roles protect.
