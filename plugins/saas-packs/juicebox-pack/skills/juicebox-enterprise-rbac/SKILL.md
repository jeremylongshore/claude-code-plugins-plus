---
name: juicebox-enterprise-rbac
description: 'Configure Juicebox team access.

  Trigger: "juicebox rbac", "juicebox team roles".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- recruiting
- juicebox
compatibility: Designed for Claude Code
---
# Juicebox Enterprise RBAC

## Overview

Juicebox provides AI-powered people search and analysis for recruiting and sales teams. Enterprise RBAC controls who can search candidate databases, enrich profiles with contact info, trigger outreach sequences, and export data. Workspace admins manage team seats and API usage limits. Analysts run searches but may be restricted from exporting PII. Viewers can review saved searches without accessing raw contact data. SOC 2 compliance requires audit logging on all data enrichment and export actions.

## Role Hierarchy

| Role | Permissions | Scope |
|------|------------|-------|
| Workspace Admin | Manage seats, billing, API keys, configure integrations | Entire workspace |
| Recruiter | Search, enrich, access contact info, run outreach campaigns | All datasets |
| Analyst | Search and enrich profiles, view analytics dashboards | Assigned datasets |
| Sourcer | Search and enrich only, no contact reveal or outreach | Assigned datasets |
| Viewer | View saved searches and reports, no data access or export | Read-only |

## Permission Check

```typescript
async function checkJuiceboxAccess(userId: string, action: string, datasetId: string): Promise<boolean> {
  const response = await fetch(`${JUICEBOX_API}/v1/workspaces/${WORKSPACE_ID}/permissions`, {
    headers: { Authorization: `Bearer ${JUICEBOX_API_KEY}`, 'Content-Type': 'application/json' },
  });
  const perms = await response.json();
  const user = perms.members.find((m: any) => m.id === userId);
  if (!user) return false;
  const rolePerms = ROLE_PERMISSIONS[user.role];
  return rolePerms?.[action] && (user.datasets.includes(datasetId) || user.role === 'admin');
}
```

## Role Assignment

```typescript
async function assignWorkspaceRole(email: string, role: string, datasets: string[]): Promise<void> {
  await fetch(`${JUICEBOX_API}/v1/workspaces/${WORKSPACE_ID}/members`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${JUICEBOX_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, role, datasetAccess: datasets }),
  });
}

async function revokeAccess(email: string): Promise<void> {
  await fetch(`${JUICEBOX_API}/v1/workspaces/${WORKSPACE_ID}/members/${email}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${JUICEBOX_API_KEY}` },
  });
}
```

## Audit Logging

```typescript
interface JuiceboxAuditEntry {
  timestamp: string; userId: string; role: string;
  action: 'search' | 'enrich' | 'contact_reveal' | 'export' | 'outreach' | 'role_change';
  datasetId: string; recordCount?: number; result: 'allowed' | 'denied';
}

function logAccess(entry: JuiceboxAuditEntry): void {
  console.log(JSON.stringify({ ...entry, workspaceId: process.env.JUICEBOX_WORKSPACE_ID }));
}
```

## RBAC Checklist

- [ ] Workspace admin role limited to designated team leads
- [ ] Contact reveal and export restricted to recruiter role and above
- [ ] Dataset access scoped per team to prevent cross-team data leakage
- [ ] API key usage monitored with rate limits per role
- [ ] Viewer role enforced for stakeholders who only need reporting
- [ ] All enrichment and export actions logged for SOC 2 compliance
- [ ] Quarterly access review to remove departed team members

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `403` on contact reveal endpoint | User role lacks contact permission | Upgrade to recruiter role or request admin approval |
| Export returns empty results | Dataset not assigned to user | Add dataset to user's access list in workspace settings |
| API rate limit exceeded | Too many enrichment calls per hour | Check role-based rate limits, batch requests |
| Saved search not visible | Search created in different dataset scope | Verify dataset access or share search explicitly |
| Seat limit reached | All workspace licenses used | Remove inactive members or upgrade plan |

## Resources

- [Juicebox Enterprise](https://juicebox.ai/enterprise)
- [Juicebox API Docs](https://docs.juicebox.ai/)

## Next Steps

See `juicebox-security-basics`.
