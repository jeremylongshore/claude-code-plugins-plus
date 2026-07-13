# Documenso Enterprise RBAC - Implementation Guide

## Documenso Team Roles

| Role | Documents | Templates | Team Settings | API Access |
|------|-----------|-----------|---------------|------------|
| Owner | Full | Full | Full | Full |
| Admin | Full | Full | Manage members | Full |
| Member | Create/Edit own | Use | None | Limited |
| Viewer | View only | View | None | Read-only |

## Role Implementation

### Step 1: Define Application Roles

```typescript
// src/auth/roles.ts
export enum SigningRole {
  Admin = "admin",
  Manager = "manager",
  User = "user",
  Viewer = "viewer",
  ApiService = "api_service",
}

export interface SigningPermissions {
  documents: {
    create: boolean;
    read: boolean;
    update: boolean;
    delete: boolean;
    send: boolean;
  };
  templates: {
    create: boolean;
    read: boolean;
    update: boolean;
    delete: boolean;
    use: boolean;
  };
  team: {
    manageMembers: boolean;
    manageSettings: boolean;
    viewAuditLog: boolean;
  };
  api: {
    useApi: boolean;
    manageWebhooks: boolean;
  };
}

export const ROLE_PERMISSIONS: Record<SigningRole, SigningPermissions> = {
  [SigningRole.Admin]: {
    documents: { create: true, read: true, update: true, delete: true, send: true },
    templates: { create: true, read: true, update: true, delete: true, use: true },
    team: { manageMembers: true, manageSettings: true, viewAuditLog: true },
    api: { useApi: true, manageWebhooks: true },
  },
  [SigningRole.Manager]: {
    documents: { create: true, read: true, update: true, delete: true, send: true },
    templates: { create: true, read: true, update: true, delete: false, use: true },
    team: { manageMembers: false, manageSettings: false, viewAuditLog: true },
    api: { useApi: true, manageWebhooks: false },
  },
  [SigningRole.User]: {
    documents: { create: true, read: true, update: true, delete: false, send: true },
    templates: { create: false, read: true, update: false, delete: false, use: true },
    team: { manageMembers: false, manageSettings: false, viewAuditLog: false },
    api: { useApi: false, manageWebhooks: false },
  },
  [SigningRole.Viewer]: {
    documents: { create: false, read: true, update: false, delete: false, send: false },
    templates: { create: false, read: true, update: false, delete: false, use: false },
    team: { manageMembers: false, manageSettings: false, viewAuditLog: false },
    api: { useApi: false, manageWebhooks: false },
  },
  [SigningRole.ApiService]: {
    documents: { create: true, read: true, update: true, delete: false, send: true },
    templates: { create: false, read: true, update: false, delete: false, use: true },
    team: { manageMembers: false, manageSettings: false, viewAuditLog: false },
    api: { useApi: true, manageWebhooks: false },
  },
};
```

### Step 2: Permission Checking

```typescript
// src/auth/permissions.ts
import { SigningRole, ROLE_PERMISSIONS, SigningPermissions } from "./roles";

type PermissionPath =
  | `documents.${keyof SigningPermissions["documents"]}`
  | `templates.${keyof SigningPermissions["templates"]}`
  | `team.${keyof SigningPermissions["team"]}`
  | `api.${keyof SigningPermissions["api"]}`;

export function hasPermission(
  role: SigningRole,
  permission: PermissionPath
): boolean {
  const [category, action] = permission.split(".") as [
    keyof SigningPermissions,
    string
  ];

  const permissions = ROLE_PERMISSIONS[role];
  return (permissions[category] as any)[action] ?? false;
}

export function checkPermission(
  role: SigningRole,
  permission: PermissionPath
): void {
  if (!hasPermission(role, permission)) {
    throw new ForbiddenError(
      `Permission denied: ${permission} requires higher role than ${role}`
    );
  }
}

export class ForbiddenError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ForbiddenError";
  }
}
```

### Step 3: Express Middleware

```typescript
// src/middleware/auth.ts
import { Request, Response, NextFunction } from "express";
import { SigningRole, hasPermission } from "../auth";

// Extend Express Request type
declare global {
  namespace Express {
    interface Request {
      user?: {
        id: string;
        email: string;
        role: SigningRole;
        teamId?: string;
      };
    }
  }
}

export function requireRole(requiredRole: SigningRole) {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = req.user;

    if (!user) {
      return res.status(401).json({ error: "Authentication required" });
    }

    const roleHierarchy = [
      SigningRole.Viewer,
      SigningRole.User,
      SigningRole.Manager,
      SigningRole.Admin,
    ];

    const userRoleIndex = roleHierarchy.indexOf(user.role);
    const requiredRoleIndex = roleHierarchy.indexOf(requiredRole);

    if (userRoleIndex < requiredRoleIndex) {
      return res.status(403).json({
        error: "Forbidden",
        message: `Role ${requiredRole} required, you have ${user.role}`,
      });
    }

    next();
  };
}

export function requirePermission(permission: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = req.user;

    if (!user) {
      return res.status(401).json({ error: "Authentication required" });
    }

    if (!hasPermission(user.role, permission as any)) {
      return res.status(403).json({
        error: "Forbidden",
        message: `Permission '${permission}' denied for role ${user.role}`,
      });
    }

    next();
  };
}
```

### Step 4: Document Ownership

```typescript
// src/services/document-access.ts
interface DocumentOwnership {
  documentId: string;
  ownerId: string;
  teamId?: string;
  sharedWith: string[];  // User IDs with explicit access
}

class DocumentAccessService {
  private ownership = new Map<string, DocumentOwnership>();

  async canAccess(
    userId: string,
    userRole: SigningRole,
    documentId: string
  ): Promise<boolean> {
    // Admins can access all team documents
    if (userRole === SigningRole.Admin) {
      return true;
    }

    const ownership = this.ownership.get(documentId);
    if (!ownership) {
      return false;
    }

    // Owner always has access
    if (ownership.ownerId === userId) {
      return true;
    }

    // Check explicit sharing
    if (ownership.sharedWith.includes(userId)) {
      return true;
    }

    // Managers can access team documents
    if (userRole === SigningRole.Manager && ownership.teamId) {
      const userTeam = await this.getUserTeam(userId);
      return userTeam === ownership.teamId;
    }

    return false;
  }

  async canModify(
    userId: string,
    userRole: SigningRole,
    documentId: string
  ): Promise<boolean> {
    // Viewers cannot modify
    if (userRole === SigningRole.Viewer) {
      return false;
    }

    // Others need access + not viewer
    return this.canAccess(userId, userRole, documentId);
  }

  async registerDocument(
    documentId: string,
    ownerId: string,
    teamId?: string
  ): Promise<void> {
    this.ownership.set(documentId, {
      documentId,
      ownerId,
      teamId,
      sharedWith: [],
    });
  }

  async shareDocument(
    documentId: string,
    shareWithUserId: string
  ): Promise<void> {
    const ownership = this.ownership.get(documentId);
    if (ownership) {
      ownership.sharedWith.push(shareWithUserId);
    }
  }

  private async getUserTeam(userId: string): Promise<string | undefined> {
    // Implement team lookup
    return undefined;
  }
}

export const documentAccess = new DocumentAccessService();
```

### Step 5: API Route Protection

```typescript
// src/api/documents.ts
import express from "express";
import { requirePermission, requireRole } from "../middleware/auth";
import { SigningRole } from "../auth";
import { documentAccess } from "../services/document-access";

const router = express.Router();

// Create document - requires documents.create permission
router.post(
  "/documents",
  requirePermission("documents.create"),
  async (req, res) => {
    const { title, templateId } = req.body;
    const userId = req.user!.id;

    const doc = await signingService.createDocument(title, templateId);

    // Register ownership
    await documentAccess.registerDocument(
      doc.documentId,
      userId,
      req.user!.teamId
    );

    res.json(doc);
  }
);

// Delete document - requires documents.delete AND ownership
router.delete(
  "/documents/:id",
  requirePermission("documents.delete"),
  async (req, res) => {
    const documentId = req.params.id;
    const { id: userId, role } = req.user!;

    // Check ownership
    const canModify = await documentAccess.canModify(userId, role, documentId);
    if (!canModify) {
      return res.status(403).json({ error: "Not authorized for this document" });
    }

    await signingService.deleteDocument(documentId);
    res.json({ deleted: true });
  }
);

// Team management - requires team.manageMembers permission
router.post(
  "/team/members",
  requirePermission("team.manageMembers"),
  async (req, res) => {
    const { email, role } = req.body;
    // Add team member logic
    res.json({ added: true });
  }
);

// Audit log - requires team.viewAuditLog permission
router.get(
  "/team/audit-log",
  requirePermission("team.viewAuditLog"),
  async (req, res) => {
    const auditLog = await getAuditLog(req.user!.teamId!);
    res.json(auditLog);
  }
);

export default router;
```

### Step 6: Audit Logging

```typescript
// src/audit/logger.ts
interface AuditEntry {
  timestamp: Date;
  userId: string;
  userEmail: string;
  userRole: SigningRole;
  action: string;
  resourceType: "document" | "template" | "team" | "settings";
  resourceId: string;
  details: Record<string, any>;
  ipAddress?: string;
  success: boolean;
}

class AuditLogger {
  async log(entry: Omit<AuditEntry, "timestamp">): Promise<void> {
    const fullEntry: AuditEntry = {
      ...entry,
      timestamp: new Date(),
    };

    // Store in database
    await db.auditLog.create({ data: fullEntry });

    // Log to monitoring
    console.log(
      `[AUDIT] ${entry.action} ${entry.resourceType}:${entry.resourceId} ` +
      `by ${entry.userEmail} (${entry.userRole}) - ${entry.success ? "OK" : "DENIED"}`
    );

    // Alert on security events
    if (this.isSecurityEvent(entry)) {
      await this.alertSecurity(fullEntry);
    }
  }

  private isSecurityEvent(entry: Omit<AuditEntry, "timestamp">): boolean {
    return (
      !entry.success ||
      entry.action.includes("delete") ||
      entry.action.includes("permission") ||
      entry.resourceType === "team"
    );
  }

  private async alertSecurity(entry: AuditEntry): Promise<void> {
    // Send to security team
  }
}

export const auditLogger = new AuditLogger();

// Middleware to log all protected actions
export function auditMiddleware(action: string, resourceType: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();

    // Capture original end function
    const originalEnd = res.end;

    res.end = function (chunk?: any, encoding?: any) {
      // Log after response is sent
      auditLogger.log({
        userId: req.user?.id ?? "anonymous",
        userEmail: req.user?.email ?? "unknown",
        userRole: req.user?.role ?? SigningRole.Viewer,
        action,
        resourceType: resourceType as any,
        resourceId: req.params.id ?? "none",
        details: {
          method: req.method,
          path: req.path,
          durationMs: Date.now() - startTime,
          statusCode: res.statusCode,
        },
        ipAddress: req.ip,
        success: res.statusCode < 400,
      });

      return originalEnd.call(this, chunk, encoding);
    };

    next();
  };
}
```

## Multi-Tenant Architecture

```typescript
// src/tenant/context.ts
interface TenantContext {
  tenantId: string;
  documensoApiKey: string;
  features: {
    templatesEnabled: boolean;
    webhooksEnabled: boolean;
    maxDocumentsPerMonth: number;
  };
}

const tenantContexts = new Map<string, TenantContext>();

export function getTenantContext(tenantId: string): TenantContext {
  const context = tenantContexts.get(tenantId);
  if (!context) {
    throw new Error(`Unknown tenant: ${tenantId}`);
  }
  return context;
}

export function getDocumensoClientForTenant(tenantId: string): Documenso {
  const context = getTenantContext(tenantId);

  return new Documenso({
    apiKey: context.documensoApiKey,
  });
}
```
