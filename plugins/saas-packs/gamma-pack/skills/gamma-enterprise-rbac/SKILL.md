---
name: gamma-enterprise-rbac
description: |
  Implement enterprise role-based access control for Gamma integrations.
  Use when configuring team permissions, multi-tenant access,
  or enterprise authorization patterns.
  Trigger with phrases like "gamma RBAC", "gamma permissions",
  "gamma access control", "gamma enterprise", "gamma roles".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, authentication, rbac]

---
# Gamma Enterprise RBAC

## Overview

Implement role-based access control for Gamma API integrations. Gamma's API uses a single API key per workspace -- granular permissions must be implemented in your application layer. The Teams and Business plans support workspace-level collaboration with shared themes and folders.

## Prerequisites

- Gamma Teams or Business subscription
- Application database for user/role storage
- Completed `gamma-install-auth` setup

## Gamma Access Model

```
Gamma Workspace (1 API key)
├── Themes (shared across workspace)
├── Folders (shared across workspace)
└── Generations (tied to API key, not individual users)

Your Application Layer (you implement this):
├── Organization
│   ├── Admin (manage API key, configure themes)
│   ├── Editor (generate presentations, use templates)
│   ├── Viewer (view generated presentations, download exports)
│   └── Guest (no generation access)
```

**Key point:** Gamma's API does not have per-user authentication. All API calls use the workspace API key. You must enforce per-user permissions in your application.

## Instructions

### Step 1: Define Role Hierarchy

```typescript
// src/auth/gamma-roles.ts
type GammaRole = "guest" | "viewer" | "editor" | "admin";

const PERMISSIONS: Record<GammaRole, string[]> = {
  guest: [],
  viewer: ["generation:view", "export:download"],
  editor: ["generation:view", "generation:create", "export:download", "template:use"],
  admin: [
    "generation:view", "generation:create", "export:download",
    "template:use", "template:manage", "theme:manage",
    "settings:manage", "member:manage",
  ],
};

function hasPermission(role: GammaRole, permission: string): boolean {
  return PERMISSIONS[role]?.includes(permission) ?? false;
}
```

### Step 2: Authorization Middleware

```typescript
// src/middleware/gamma-auth.ts
import { Request, Response, NextFunction } from "express";

function requireGammaPermission(permission: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = req.user; // Set by your auth middleware
    if (!user) return res.status(401).json({ error: "Unauthorized" });

    if (!hasPermission(user.gammaRole, permission)) {
      return res.status(403).json({
        error: "Forbidden",
        required: permission,
        userRole: user.gammaRole,
      });
    }
    next();
  };
}

// Usage
app.post("/api/presentations",
  requireGammaPermission("generation:create"),
  async (req, res) => {
    const gamma = createGammaClient({ apiKey: process.env.GAMMA_API_KEY! });
    const { generationId } = await gamma.generate(req.body);
    // Track ownership in your database
    await db.generations.create({
      data: { generationId, userId: req.user.id, teamId: req.user.teamId },
    });
    res.json({ generationId });
  }
);

app.get("/api/presentations/:id",
  requireGammaPermission("generation:view"),
  async (req, res) => {
    // Only return if user owns it or is in the same team
    const gen = await db.generations.findFirst({
      where: { generationId: req.params.id, teamId: req.user.teamId },
    });
    if (!gen) return res.status(404).json({ error: "Not found" });
    res.json(gen);
  }
);
```

### Step 3: Multi-Tenant Workspace Isolation

```typescript
// src/tenant/gamma-tenant.ts
// Each tenant can have their own Gamma workspace (API key)
// or share a workspace with resource-level isolation

interface Tenant {
  id: string;
  name: string;
  gammaApiKey: string; // Encrypted in database
}

class TenantGammaService {
  private clients = new Map<string, ReturnType<typeof createGammaClient>>();

  getClient(tenant: Tenant) {
    if (!this.clients.has(tenant.id)) {
      this.clients.set(
        tenant.id,
        createGammaClient({ apiKey: tenant.gammaApiKey })
      );
    }
    return this.clients.get(tenant.id)!;
  }

  async generate(tenant: Tenant, userId: string, content: string, options: any = {}) {
    const gamma = this.getClient(tenant);
    const { generationId } = await gamma.generate({
      content,
      ...options,
    });

    // Track with tenant isolation
    await db.generations.create({
      data: { generationId, tenantId: tenant.id, userId },
    });

    return { generationId };
  }
}
```

### Step 4: Credit Quota Per User/Team

```typescript
// src/quota/gamma-quotas.ts
interface Quota {
  maxGenerationsPerDay: number;
  maxCreditsPerMonth: number;
}

const ROLE_QUOTAS: Record<GammaRole, Quota> = {
  guest: { maxGenerationsPerDay: 0, maxCreditsPerMonth: 0 },
  viewer: { maxGenerationsPerDay: 0, maxCreditsPerMonth: 0 },
  editor: { maxGenerationsPerDay: 10, maxCreditsPerMonth: 500 },
  admin: { maxGenerationsPerDay: 50, maxCreditsPerMonth: 5000 },
};

async function checkQuota(userId: string, role: GammaRole): Promise<boolean> {
  const quota = ROLE_QUOTAS[role];
  if (quota.maxGenerationsPerDay === 0) return false;

  const todayCount = await db.generations.count({
    where: {
      userId,
      createdAt: { gte: new Date(new Date().toDateString()) },
    },
  });

  return todayCount < quota.maxGenerationsPerDay;
}
```

### Step 5: Audit Logging

```typescript
// src/audit/gamma-audit.ts
async function auditGammaAction(entry: {
  userId: string;
  teamId: string;
  action: string;
  resourceId?: string;
  metadata?: Record<string, any>;
}) {
  await db.auditLog.create({
    data: {
      ...entry,
      timestamp: new Date(),
      service: "gamma",
    },
  });
}

// Usage
await auditGammaAction({
  userId: req.user.id,
  teamId: req.user.teamId,
  action: "generation.create",
  resourceId: generationId,
  metadata: { outputFormat: "presentation", credits: result.creditsUsed },
});
```

## Permission Matrix

| Permission | Guest | Viewer | Editor | Admin |
|------------|-------|--------|--------|-------|
| View presentations | No | Yes | Yes | Yes |
| Download exports | No | Yes | Yes | Yes |
| Create generations | No | No | Yes | Yes |
| Use templates | No | No | Yes | Yes |
| Manage themes/folders | No | No | No | Yes |
| Manage team members | No | No | No | Yes |
| Configure API key | No | No | No | Yes |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Insufficient role | Check user's `gammaRole` assignment |
| Cross-tenant access | Wrong API key | Verify tenant isolation in `getClient()` |
| Quota exceeded | Too many generations | Show remaining quota, wait for reset |
| Privilege escalation | Missing role check | Verify middleware on all routes |

## Resources

- [Gamma Teams](https://gamma.app/pricing)
- [RBAC Best Practices](https://csrc.nist.gov/projects/role-based-access-control)
- [OWASP Access Control](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html)

## Next Steps

Proceed to `gamma-migration-deep-dive` for platform migration.
