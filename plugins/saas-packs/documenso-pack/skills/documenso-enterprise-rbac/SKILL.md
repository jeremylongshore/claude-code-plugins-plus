---
name: documenso-enterprise-rbac
description: |
  Configure Documenso enterprise role-based access control and team management.
  Use when implementing team permissions, configuring organizational roles,
  or setting up enterprise access controls.
  Trigger with phrases like "documenso RBAC", "documenso teams",
  "documenso permissions", "documenso enterprise", "documenso roles".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, rbac]

---
# Documenso Enterprise RBAC

## Overview

Configure team-based access control and enterprise features in Documenso. The Team plan enables multi-user collaboration with shared documents. Enterprise adds SSO (OIDC), audit logging, and organization-level management.

## Prerequisites

- Documenso Team or Enterprise plan
- Understanding of RBAC concepts
- For SSO: OIDC-compatible identity provider (Okta, Azure AD, Google Workspace, Auth0)

## Documenso Team Model

```
Organization
├── Team A
│   ├── Owner (full control)
│   ├── Admin (manage members, settings)
│   └── Member (create, view, sign team documents)
├── Team B
│   └── ...
└── Personal Accounts (separate from teams)
```

**Key concepts:**
- Teams are separate from personal accounts -- team documents are owned by the team
- Team API keys access all team documents; personal keys only access personal documents
- Each team member can have Owner, Admin, or Member role
- Unlimited teams and users on Team/Enterprise plans (early adopter pricing)

## Instructions

### Step 1: Team API Key Scoping

```typescript
import { Documenso } from "@documenso/sdk-typescript";

// Personal key: only YOUR documents
const personalClient = new Documenso({
  apiKey: process.env.DOCUMENSO_PERSONAL_KEY!,
});

// Team key: all documents in the team
const teamClient = new Documenso({
  apiKey: process.env.DOCUMENSO_TEAM_KEY!,
});

// Common mistake: using personal key for team operations
// Results in 403 Forbidden on team resources
```

### Step 2: Application-Level RBAC

Documenso handles team membership internally. For finer-grained control in your app, implement an authorization layer:

```typescript
// src/auth/documenso-rbac.ts
type Role = "viewer" | "editor" | "admin" | "owner";

interface TeamMember {
  userId: string;
  teamId: string;
  role: Role;
}

const PERMISSIONS: Record<Role, string[]> = {
  viewer: ["documents:read"],
  editor: ["documents:read", "documents:create", "documents:send"],
  admin: ["documents:read", "documents:create", "documents:send", "documents:delete", "members:manage"],
  owner: ["documents:read", "documents:create", "documents:send", "documents:delete", "members:manage", "team:settings", "team:billing"],
};

function hasPermission(member: TeamMember, permission: string): boolean {
  return PERMISSIONS[member.role]?.includes(permission) ?? false;
}

// Middleware
function requirePermission(permission: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const member = req.teamMember; // Set by auth middleware
    if (!hasPermission(member, permission)) {
      return res.status(403).json({
        error: "Forbidden",
        required: permission,
        userRole: member.role,
      });
    }
    next();
  };
}

// Usage
app.delete("/api/documents/:id",
  requirePermission("documents:delete"),
  async (req, res) => {
    await teamClient.documents.deleteV0(parseInt(req.params.id));
    res.json({ deleted: true });
  }
);
```

### Step 3: Enterprise SSO Configuration

Documenso Enterprise supports SSO via OIDC. Configuration is done in the admin panel:

```text
SSO Setup (Enterprise only):
1. Navigate to Organization Settings > SSO
2. Select your OIDC provider
3. Enter:
   - Client ID (from your IdP)
   - Client Secret (from your IdP)
   - Issuer URL (e.g., https://login.microsoftonline.com/{tenant}/v2.0)
4. Configure redirect URI in your IdP:
   https://sign.yourcompany.com/api/auth/callback/oidc
5. Test with a non-admin user first

Supported providers:
- Google Workspace
- Microsoft Entra ID (Azure AD)
- Okta
- Auth0
- Any OIDC-compliant provider

Once enabled, team members sign in via:
https://sign.yourcompany.com/sso/{organization-slug}
```

### Step 4: Audit Logging (Enterprise)

Enterprise includes built-in audit logging. For additional application-level auditing:

```typescript
// src/audit/documenso-audit.ts
interface AuditEntry {
  timestamp: string;
  userId: string;
  teamId: string;
  action: string;
  resourceType: "document" | "template" | "team" | "member";
  resourceId: string;
  metadata: Record<string, any>;
}

async function auditLog(entry: Omit<AuditEntry, "timestamp">) {
  const log: AuditEntry = {
    ...entry,
    timestamp: new Date().toISOString(),
  };

  // Write to your audit store (database, CloudWatch, etc.)
  console.log(JSON.stringify(log));

  // Example: document sent
  // { action: "document.send", resourceType: "document",
  //   resourceId: "42", userId: "user_123", teamId: "team_456" }
}

// Wrap Documenso operations with audit logging
async function sendDocumentAudited(
  client: Documenso,
  documentId: number,
  userId: string,
  teamId: string
) {
  await client.documents.sendV0(documentId);
  await auditLog({
    userId,
    teamId,
    action: "document.send",
    resourceType: "document",
    resourceId: String(documentId),
    metadata: { status: "PENDING" },
  });
}
```

### Step 5: Multi-Tenant Architecture

```typescript
// src/tenant/documenso-tenant.ts
// Each tenant maps to a Documenso team with its own API key

interface Tenant {
  id: string;
  name: string;
  documensoTeamApiKey: string; // Encrypted in database
}

class TenantDocumensoService {
  private clients = new Map<string, Documenso>();

  getClient(tenant: Tenant): Documenso {
    if (!this.clients.has(tenant.id)) {
      this.clients.set(
        tenant.id,
        new Documenso({ apiKey: tenant.documensoTeamApiKey })
      );
    }
    return this.clients.get(tenant.id)!;
  }

  // Ensure tenant isolation — never cross-access
  async getDocument(tenant: Tenant, documentId: number) {
    const client = this.getClient(tenant);
    return client.documents.getV0(documentId);
    // Team API keys automatically scope to team documents
  }
}
```

## Permission Matrix

| Action | Member | Admin | Owner |
|--------|--------|-------|-------|
| View team documents | Yes | Yes | Yes |
| Create documents | Yes | Yes | Yes |
| Send for signing | Yes | Yes | Yes |
| Delete documents | No | Yes | Yes |
| Manage team members | No | Yes | Yes |
| Team settings / billing | No | No | Yes |
| Configure SSO | No | No | Yes |

## Error Handling

| RBAC Issue | Cause | Solution |
|------------|-------|----------|
| 403 Forbidden | Personal key on team resource | Use team-scoped API key |
| Cannot delete | Not Admin/Owner role | Request role upgrade from team Owner |
| SSO login fails | Wrong OIDC configuration | Verify Client ID, Secret, and Issuer URL |
| Tenant data leak | Wrong API key for tenant | Validate tenant isolation in tests |

## Resources

- [Documenso Teams](https://documenso.com/features/teams)
- [SSO Portal Documentation](https://docs.documenso.com/users/organisations/sso)
- [Enterprise Features](https://documenso.com/blog/introducing-self-hosted-signing-infrastructure-for-enterprise)
- [OWASP Access Control](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html)

## Next Steps

For migration strategies, see `documenso-migration-deep-dive`.
