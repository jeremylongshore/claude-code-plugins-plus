# MaintainX Enterprise RBAC - Implementation Guide

> Full implementation details and code examples for the `maintainx-enterprise-rbac` skill.

# MaintainX Enterprise RBAC

## Overview

Configure enterprise-grade role-based access control for MaintainX integrations, including SSO integration, permission management, and audit logging.

## Prerequisites

- MaintainX Enterprise plan
- Identity Provider (IdP) with SAML/OIDC
- Understanding of RBAC concepts

## MaintainX Role Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MaintainX Role Hierarchy                          │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      ORGANIZATION ADMIN                        │  │
│  │  Full access to all features, users, and settings             │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                               │                                      │
│              ┌────────────────┼────────────────┐                    │
│              ▼                ▼                ▼                    │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │
│  │    ADMIN      │  │  SUPERVISOR   │  │   REQUESTER   │           │
│  │               │  │               │  │               │           │
│  │ Manage users  │  │ Manage work   │  │ Submit        │           │
│  │ Manage assets │  │ Assign tasks  │  │ requests only │           │
│  │ Full WO access│  │ View reports  │  │               │           │
│  └───────────────┘  └───────┬───────┘  └───────────────┘           │
│                             │                                       │
│              ┌──────────────┴──────────────┐                       │
│              ▼                             ▼                       │
│  ┌───────────────┐              ┌───────────────┐                  │
│  │  TECHNICIAN   │              │    VIEWER     │                  │
│  │               │              │               │                  │
│  │ Execute work  │              │ Read-only     │                  │
│  │ Update status │              │ View reports  │                  │
│  └───────────────┘              └───────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Role Definition

```typescript
// src/rbac/roles.ts

enum MaintainXRole {
  OrganizationAdmin = 'ORGANIZATION_ADMIN',
  Admin = 'ADMIN',
  Supervisor = 'SUPERVISOR',
  Technician = 'TECHNICIAN',
  Requester = 'REQUESTER',
  Viewer = 'VIEWER',
}

interface Permission {
  resource: string;
  actions: ('create' | 'read' | 'update' | 'delete' | 'assign')[];
}

const rolePermissions: Record<MaintainXRole, Permission[]> = {
  [MaintainXRole.OrganizationAdmin]: [
    { resource: '*', actions: ['create', 'read', 'update', 'delete', 'assign'] },
  ],
  [MaintainXRole.Admin]: [
    { resource: 'workorders', actions: ['create', 'read', 'update', 'delete', 'assign'] },
    { resource: 'assets', actions: ['create', 'read', 'update', 'delete'] },
    { resource: 'locations', actions: ['create', 'read', 'update', 'delete'] },
    { resource: 'users', actions: ['create', 'read', 'update'] },
  ],
  [MaintainXRole.Supervisor]: [
    { resource: 'workorders', actions: ['create', 'read', 'update', 'assign'] },
    { resource: 'assets', actions: ['read'] },
    { resource: 'locations', actions: ['read'] },
    { resource: 'users', actions: ['read'] },
    { resource: 'reports', actions: ['read'] },
  ],
  [MaintainXRole.Technician]: [
    { resource: 'workorders', actions: ['read', 'update'] },
    { resource: 'assets', actions: ['read'] },
    { resource: 'locations', actions: ['read'] },
  ],
  [MaintainXRole.Requester]: [
    { resource: 'workrequests', actions: ['create', 'read'] },
    { resource: 'workorders', actions: ['read'] },
  ],
  [MaintainXRole.Viewer]: [
    { resource: 'workorders', actions: ['read'] },
    { resource: 'assets', actions: ['read'] },
    { resource: 'locations', actions: ['read'] },
    { resource: 'reports', actions: ['read'] },
  ],
};

function hasPermission(
  role: MaintainXRole,
  resource: string,
  action: string
): boolean {
  const permissions = rolePermissions[role];

  return permissions.some(p => {
    const resourceMatch = p.resource === '*' || p.resource === resource;
    const actionMatch = p.actions.includes(action as any);
    return resourceMatch && actionMatch;
  });
}

export { MaintainXRole, hasPermission, rolePermissions };
```

### Step 2: SAML SSO Integration

```typescript
// src/auth/saml-sso.ts
import { Strategy as SamlStrategy } from 'passport-saml';
import passport from 'passport';

interface SamlConfig {
  entryPoint: string;
  issuer: string;
  cert: string;
  callbackUrl: string;
}

// SAML configuration
const samlConfig: SamlConfig = {
  entryPoint: process.env.SAML_ENTRY_POINT!,  // IdP SSO URL
  issuer: process.env.SAML_ISSUER!,           // SP Entity ID
  cert: process.env.SAML_CERT!,               // IdP Certificate
  callbackUrl: `${process.env.APP_URL}/auth/saml/callback`,
};

// Map IdP groups to MaintainX roles
const groupRoleMapping: Record<string, MaintainXRole> = {
  'MaintainX-Admins': MaintainXRole.Admin,
  'MaintainX-Supervisors': MaintainXRole.Supervisor,
  'MaintainX-Technicians': MaintainXRole.Technician,
  'MaintainX-Requesters': MaintainXRole.Requester,
  'MaintainX-Viewers': MaintainXRole.Viewer,
};

// Configure Passport SAML strategy
passport.use(new SamlStrategy(
  {
    ...samlConfig,
    passReqToCallback: true,
  },
  async (req, profile, done) => {
    try {
      // Extract user info from SAML assertion
      const email = profile.email || profile.nameID;
      const groups = profile.groups || [];

      // Determine role from groups
      let role = MaintainXRole.Viewer;  // Default role
      for (const [group, mappedRole] of Object.entries(groupRoleMapping)) {
        if (groups.includes(group)) {
          role = mappedRole;
          break;
        }
      }

      // Find or create user
      const user = await findOrCreateUser({
        email,
        firstName: profile.firstName,
        lastName: profile.lastName,
        role,
        ssoId: profile.nameID,
      });

      return done(null, user);
    } catch (error) {
      return done(error);
    }
  }
));

// Routes
app.get('/auth/saml', passport.authenticate('saml'));

app.post('/auth/saml/callback',
  passport.authenticate('saml', { failureRedirect: '/login' }),
  (req, res) => {
    res.redirect('/');
  }
);
```

### Step 3: Permission Middleware

```typescript
// src/middleware/authorization.ts
import { Request, Response, NextFunction } from 'express';

interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    email: string;
    role: MaintainXRole;
  };
}

// Check permission middleware
function requirePermission(resource: string, action: string) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    if (!hasPermission(req.user.role, resource, action)) {
      auditLogger.log({
        type: 'ACCESS_DENIED',
        userId: req.user.id,
        resource,
        action,
        ip: req.ip,
      });

      return res.status(403).json({
        error: 'Forbidden',
        message: `You don't have permission to ${action} ${resource}`,
      });
    }

    next();
  };
}

// Check role middleware
function requireRole(...allowedRoles: MaintainXRole[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Required role: ${allowedRoles.join(' or ')}`,
      });
    }

    next();
  };
}

// Usage
app.get('/api/workorders',
  requirePermission('workorders', 'read'),
  getWorkOrders
);

app.post('/api/workorders',
  requirePermission('workorders', 'create'),
  createWorkOrder
);

app.delete('/api/workorders/:id',
  requirePermission('workorders', 'delete'),
  deleteWorkOrder
);

// Admin-only endpoint
app.get('/api/admin/users',
  requireRole(MaintainXRole.OrganizationAdmin, MaintainXRole.Admin),
  getUsers
);
```

### Step 4: Location-Based Access Control

```typescript
// src/rbac/location-access.ts

interface LocationAccess {
  userId: string;
  locationIds: string[];
  includeChildren: boolean;
}

class LocationAccessControl {
  private accessRules: Map<string, LocationAccess> = new Map();

  setAccess(userId: string, locationIds: string[], includeChildren = true) {
    this.accessRules.set(userId, {
      userId,
      locationIds,
      includeChildren,
    });
  }

  async canAccessWorkOrder(userId: string, workOrder: WorkOrder): Promise<boolean> {
    const access = this.accessRules.get(userId);

    // No restrictions = full access
    if (!access || access.locationIds.length === 0) {
      return true;
    }

    // Check if work order's location is accessible
    if (!workOrder.locationId) {
      return true;  // No location = accessible
    }

    if (access.locationIds.includes(workOrder.locationId)) {
      return true;
    }

    // Check child locations if enabled
    if (access.includeChildren) {
      const childLocations = await this.getChildLocations(access.locationIds);
      return childLocations.includes(workOrder.locationId);
    }

    return false;
  }

  private async getChildLocations(parentIds: string[]): Promise<string[]> {
    // Recursively get all child location IDs
    const children: string[] = [];
    const locations = await maintainxClient.getLocations();

    function findChildren(parentId: string) {
      locations.locations
        .filter(l => l.parentId === parentId)
        .forEach(l => {
          children.push(l.id);
          findChildren(l.id);
        });
    }

    parentIds.forEach(findChildren);
    return children;
  }
}

// Apply location filter to queries
async function filterByLocationAccess(
  userId: string,
  workOrders: WorkOrder[]
): Promise<WorkOrder[]> {
  const lac = new LocationAccessControl();
  const filtered = [];

  for (const wo of workOrders) {
    if (await lac.canAccessWorkOrder(userId, wo)) {
      filtered.push(wo);
    }
  }

  return filtered;
}
```

### Step 5: Audit Logging

```typescript
// src/rbac/audit.ts

interface AuditEntry {
  timestamp: Date;
  type: 'ACCESS_GRANTED' | 'ACCESS_DENIED' | 'DATA_MODIFIED' | 'LOGIN' | 'LOGOUT';
  userId: string;
  userEmail?: string;
  userRole?: MaintainXRole;
  resource?: string;
  resourceId?: string;
  action?: string;
  ip: string;
  userAgent?: string;
  details?: any;
}

class AuditLogger {
  private store: AuditStore;

  async log(entry: Omit<AuditEntry, 'timestamp'>): Promise<void> {
    const fullEntry: AuditEntry = {
      ...entry,
      timestamp: new Date(),
    };

    // Store in database
    await this.store.insert(fullEntry);

    // Log to console for immediate visibility
    console.log(`[AUDIT] ${entry.type}: ${entry.userId} - ${entry.resource}/${entry.action}`);

    // Alert on suspicious activity
    if (entry.type === 'ACCESS_DENIED') {
      await this.checkForSuspiciousActivity(entry.userId);
    }
  }

  private async checkForSuspiciousActivity(userId: string): Promise<void> {
    // Check for repeated access denials
    const recentDenials = await this.store.count({
      userId,
      type: 'ACCESS_DENIED',
      timestamp: { $gte: new Date(Date.now() - 5 * 60 * 1000) },  // Last 5 minutes
    });

    if (recentDenials > 10) {
      await alertSecurityTeam({
        type: 'SUSPICIOUS_ACCESS_PATTERN',
        userId,
        message: `User ${userId} has ${recentDenials} access denials in the last 5 minutes`,
      });
    }
  }

  // Generate compliance report
  async generateComplianceReport(startDate: Date, endDate: Date): Promise<any> {
    const entries = await this.store.find({
      timestamp: { $gte: startDate, $lte: endDate },
    });

    return {
      period: { start: startDate, end: endDate },
      totalEvents: entries.length,
      byType: this.groupBy(entries, 'type'),
      byUser: this.groupBy(entries, 'userId'),
      accessDenials: entries.filter(e => e.type === 'ACCESS_DENIED'),
      loginEvents: entries.filter(e => e.type === 'LOGIN'),
    };
  }
}

const auditLogger = new AuditLogger();
export { auditLogger };
```

### Step 6: API Key Scoping

```typescript
// src/rbac/api-keys.ts

interface ScopedApiKey {
  id: string;
  name: string;
  keyHash: string;
  permissions: Permission[];
  locationRestrictions?: string[];
  createdBy: string;
  createdAt: Date;
  expiresAt?: Date;
  lastUsedAt?: Date;
}

class ApiKeyManager {
  async createScopedKey(
    name: string,
    permissions: Permission[],
    options?: {
      locationRestrictions?: string[];
      expiresIn?: number;  // days
    }
  ): Promise<{ key: string; id: string }> {
    const rawKey = generateSecureToken(32);
    const keyHash = hashApiKey(rawKey);

    const apiKey: ScopedApiKey = {
      id: generateId(),
      name,
      keyHash,
      permissions,
      locationRestrictions: options?.locationRestrictions,
      createdBy: getCurrentUserId(),
      createdAt: new Date(),
      expiresAt: options?.expiresIn
        ? new Date(Date.now() + options.expiresIn * 24 * 60 * 60 * 1000)
        : undefined,
    };

    await this.store.insert(apiKey);

    return {
      key: rawKey,  // Only returned once
      id: apiKey.id,
    };
  }

  async validateKey(rawKey: string): Promise<ScopedApiKey | null> {
    const keyHash = hashApiKey(rawKey);
    const apiKey = await this.store.findOne({ keyHash });

    if (!apiKey) return null;

    // Check expiration
    if (apiKey.expiresAt && apiKey.expiresAt < new Date()) {
      return null;
    }

    // Update last used
    await this.store.update(
      { id: apiKey.id },
      { $set: { lastUsedAt: new Date() } }
    );

    return apiKey;
  }
}
```

## Output

- Role definitions implemented
- SAML SSO integration
- Permission middleware
- Location-based access control
- Audit logging
- Scoped API keys

## Enterprise Security Checklist

- [ ] SSO configured with IdP
- [ ] Role mappings defined
- [ ] Permission checks on all endpoints
- [ ] Audit logging enabled
- [ ] Location restrictions configured
- [ ] API key rotation policy
- [ ] Compliance reports automated

## Resources

- [MaintainX Enterprise](https://www.getmaintainx.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OWASP Access Control](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/)

## Next Steps

For complete platform migration, see `maintainx-migration-deep-dive`.
