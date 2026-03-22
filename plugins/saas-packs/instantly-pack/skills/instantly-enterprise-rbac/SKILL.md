---
name: instantly-enterprise-rbac
description: |
  Configure Instantly.ai workspace access control, team management, and API key governance.
  Use when managing workspace members, setting up team permissions,
  or implementing API key governance for multi-user Instantly workspaces.
  Trigger with phrases like "instantly team", "instantly permissions",
  "instantly workspace members", "instantly access control", "instantly rbac".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, enterprise, access-control, team-management]

---
# Instantly Enterprise RBAC

## Overview
Manage workspace access control in Instantly API v2. Covers workspace member management, API key governance with scoped permissions, workspace group management (for agencies), custom tag-based resource isolation, and audit logging. Instantly uses workspace-level isolation — each workspace is a separate tenant with its own data and API keys.

## Prerequisites
- Instantly Hypergrowth plan or higher
- Workspace admin access
- API key with `all:all` scope (for admin operations)

## Instructions

### Step 1: Workspace Member Management
```typescript
import { InstantlyClient } from "./src/instantly/client";
const client = new InstantlyClient();

// List workspace members
async function listMembers() {
  const members = await client.request<Array<{
    id: string;
    email: string;
    role: string;
    timestamp_created: string;
  }>>("/workspace-members");

  console.log("Workspace Members:");
  for (const m of members) {
    console.log(`  ${m.email} — role: ${m.role} (joined: ${m.timestamp_created})`);
  }
  return members;
}

// Invite new member
async function inviteMember(email: string) {
  const member = await client.request<{ id: string; email: string }>("/workspace-members", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
  console.log(`Invited: ${member.email} (${member.id})`);
  return member;
}

// Update member role
async function updateMemberRole(memberId: string, role: string) {
  await client.request(`/workspace-members/${memberId}`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

// Remove member
async function removeMember(memberId: string) {
  await client.request(`/workspace-members/${memberId}`, { method: "DELETE" });
  console.log(`Removed member: ${memberId}`);
}
```

### Step 2: API Key Governance
```typescript
// Create scoped API keys for different team roles
async function createScopedKeys() {
  // Analytics-only key for the marketing team
  const analyticsKey = await client.request<{ id: string; key: string; name: string }>(
    "/api-keys",
    {
      method: "POST",
      body: JSON.stringify({
        name: "Marketing — Analytics Read Only",
        scopes: ["campaigns:read", "accounts:read"],
      }),
    }
  );
  console.log(`Analytics key: ${analyticsKey.name} (${analyticsKey.id})`);

  // Campaign management key for SDR team
  const sdrKey = await client.request<{ id: string; key: string; name: string }>(
    "/api-keys",
    {
      method: "POST",
      body: JSON.stringify({
        name: "SDR — Campaign Management",
        scopes: ["campaigns:all", "leads:all"],
      }),
    }
  );
  console.log(`SDR key: ${sdrKey.name} (${sdrKey.id})`);

  // Webhook-only key for integration service
  const webhookKey = await client.request<{ id: string; key: string; name: string }>(
    "/api-keys",
    {
      method: "POST",
      body: JSON.stringify({
        name: "Integration Service — Webhook Handler",
        scopes: ["leads:read"],
      }),
    }
  );
  console.log(`Webhook key: ${webhookKey.name} (${webhookKey.id})`);
}

// List all API keys
async function auditApiKeys() {
  const keys = await client.request<Array<{
    id: string; name: string; scopes: string[]; timestamp_created: string;
  }>>("/api-keys");

  console.log("API Keys:");
  for (const key of keys) {
    console.log(`  ${key.name} (${key.id})`);
    console.log(`    Scopes: ${key.scopes.join(", ")}`);
    console.log(`    Created: ${key.timestamp_created}`);
  }

  // Flag overprivileged keys
  const overprivileged = keys.filter((k) =>
    k.scopes.includes("all:all") || k.scopes.includes("all:update")
  );
  if (overprivileged.length > 0) {
    console.log(`\nWARNING: ${overprivileged.length} key(s) with all:all scope:`);
    overprivileged.forEach((k) => console.log(`  ${k.name} — consider reducing scope`));
  }
}

// Revoke a key
async function revokeApiKey(keyId: string) {
  await client.request(`/api-keys/${keyId}`, { method: "DELETE" });
  console.log(`Revoked API key: ${keyId}`);
}
```

### Step 3: Workspace Group Management (Agency Pattern)
```typescript
// For agencies managing multiple client workspaces
async function manageWorkspaceGroups() {
  // List workspace group members
  const groupMembers = await client.request<Array<{
    id: string; email: string;
  }>>("/workspace-group-members");

  console.log("Workspace Group Members:");
  for (const m of groupMembers) {
    console.log(`  ${m.email} (${m.id})`);
  }

  // Add member to workspace group
  await client.request("/workspace-group-members", {
    method: "POST",
    body: JSON.stringify({ email: "team@agency.com" }),
  });

  // Get admin users
  const admins = await client.request<Array<{
    id: string; email: string;
  }>>("/workspace-group-members/admin");
  console.log("Admins:", admins.map((a) => a.email).join(", "));
}
```

### Step 4: Custom Tags for Resource Isolation
```typescript
// Use custom tags to organize campaigns and accounts by team/client
async function setupTeamTags() {
  // Create tags for each team
  const teams = ["SDR-West", "SDR-East", "Marketing", "Enterprise"];

  for (const team of teams) {
    const tag = await client.request<{ id: string; label: string }>("/custom-tags", {
      method: "POST",
      body: JSON.stringify({
        label: team,
        description: `Resources owned by ${team} team`,
      }),
    });
    console.log(`Created tag: ${tag.label} (${tag.id})`);
  }
}

// Assign tag to campaign or account
async function tagResource(tagId: string, resourceId: string) {
  await client.request("/custom-tags/toggle-resource", {
    method: "POST",
    body: JSON.stringify({
      tag_id: tagId,
      resource_id: resourceId,
    }),
  });
}

// Filter campaigns by tag
async function getCampaignsByTeam(tagId: string) {
  return client.request<Campaign[]>(`/campaigns?tag_ids=${tagId}&limit=100`);
}

// Filter accounts by tag
async function getAccountsByTeam(tagId: string) {
  return client.request<Account[]>(`/accounts?tag_ids=${tagId}&limit=100`);
}
```

### Step 5: Audit Logging
```typescript
// Review workspace audit logs
async function reviewAuditLogs() {
  const logs = await client.request<Array<{
    id: string;
    action: string;
    resource: string;
    user: string;
    timestamp_created: string;
  }>>("/audit-logs?limit=50");

  console.log("Recent Audit Events:");
  for (const log of logs) {
    console.log(`  ${log.timestamp_created} | ${log.user} | ${log.action} | ${log.resource}`);
  }

  return logs;
}

// Workspace ownership transfer
async function changeWorkspaceOwner(newOwnerUserId: string) {
  await client.request("/workspaces/current/change-owner", {
    method: "POST",
    body: JSON.stringify({ new_owner_id: newOwnerUserId }),
  });
  console.log("Workspace ownership transferred");
}
```

## Access Control Matrix

| Role | Campaigns | Leads | Accounts | Webhooks | API Keys | Members |
|------|-----------|-------|----------|----------|----------|---------|
| Admin | Full | Full | Full | Full | Full | Full |
| Manager | Create/Edit | Create/Edit | View | Create | View | View |
| SDR | Launch/Pause | Import | View | - | - | - |
| Viewer | View only | View only | View only | - | - | - |

## Key API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/workspace-members` | Invite member |
| `GET` | `/workspace-members` | List members |
| `PATCH` | `/workspace-members/{id}` | Update role |
| `DELETE` | `/workspace-members/{id}` | Remove member |
| `POST` | `/api-keys` | Create scoped key |
| `GET` | `/api-keys` | List keys |
| `DELETE` | `/api-keys/{id}` | Revoke key |
| `POST` | `/custom-tags` | Create tag |
| `POST` | `/custom-tags/toggle-resource` | Tag a resource |
| `GET` | `/audit-logs` | View audit trail |
| `POST` | `/workspaces/current/change-owner` | Transfer ownership |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `403` on member operations | Not workspace admin | Use admin API key |
| Can't revoke own key | Self-revocation blocked | Use another key or dashboard |
| Tags not filtering | Wrong tag_id format | Ensure UUID format |
| Audit logs empty | Feature not available on plan | Upgrade to higher tier |

## Resources
- [Instantly API Key Management](https://developer.instantly.ai/api/v2/apikey)
- [Workspace Members API](https://developer.instantly.ai/)
- [Custom Tags API](https://developer.instantly.ai/api/v2/schemas)

## Next Steps
For migration strategies, see `instantly-migration-deep-dive`.
