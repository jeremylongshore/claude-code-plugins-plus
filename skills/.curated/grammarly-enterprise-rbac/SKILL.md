---
name: grammarly-enterprise-rbac
description: 'Configure Grammarly enterprise role-based access control.

  Use when managing team access, configuring organization settings,

  or implementing Grammarly enterprise governance.

  Trigger with phrases like "grammarly enterprise", "grammarly teams",

  "grammarly rbac", "grammarly organization", "grammarly admin".

  '
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- grammarly
- writing
- enterprise
compatibility: Designed for Claude Code
---
# Grammarly Enterprise RBAC

## Overview

Grammarly enterprise deployments manage writing quality across teams with different access levels. Organization admins control style guides, tone profiles, and brand rules. Team admins assign seats and configure suggestion types (clarity, engagement, delivery). Members write with team defaults while guests get read-only access to shared documents. HIPAA and SOC 2 compliance in regulated industries require audit trails on who accessed which writing suggestions and AI detection results.

## Role Hierarchy

| Role | Permissions | Scope |
|------|------------|-------|
| Org Admin | Manage billing, SSO config, all style guides, API credentials | Organization-wide |
| Team Admin | Assign seats, configure suggestion settings, manage style guides | Own team |
| Member | Write with team settings, access scoring and AI detection APIs | Own team |
| Guest | View shared documents, read-only style guide access | Invited documents only |
| API Service | OAuth-scoped access to scoring, AI detection, plagiarism APIs | Per-credential scope |

## Permission Check

```typescript
async function checkGrammarlyAccess(userId: string, team: string, scope: string): Promise<boolean> {
  const response = await fetch(`${GRAMMARLY_API}/organizations/${ORG_ID}/permissions`, {
    headers: { Authorization: `Bearer ${GRAMMARLY_OAUTH_TOKEN}`, 'Content-Type': 'application/json' },
  });
  const perms = await response.json();
  const userPerms = perms.members.find((m: any) => m.id === userId);
  if (!userPerms) return false;
  return userPerms.team === team && userPerms.scopes.includes(scope);
}
```

## Role Assignment

```typescript
async function assignTeamRole(email: string, team: string, role: 'admin' | 'member' | 'guest'): Promise<void> {
  await fetch(`${GRAMMARLY_API}/organizations/${ORG_ID}/teams/${team}/members`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${GRAMMARLY_OAUTH_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, role }),
  });
}

async function revokeTeamAccess(email: string, team: string): Promise<void> {
  await fetch(`${GRAMMARLY_API}/organizations/${ORG_ID}/teams/${team}/members/${email}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${GRAMMARLY_OAUTH_TOKEN}` },
  });
}
```

## Audit Logging

```typescript
interface GrammarlyAuditEntry {
  timestamp: string; userId: string; team: string;
  action: 'score_check' | 'ai_detection' | 'plagiarism_scan' | 'style_guide_edit' | 'seat_change';
  scope: string; documentId?: string; result: 'allowed' | 'denied';
}

function logAccess(entry: GrammarlyAuditEntry): void {
  console.log(JSON.stringify({ ...entry, orgId: process.env.GRAMMARLY_ORG_ID }));
}
```

## RBAC Checklist

- [ ] Separate OAuth credentials per team, never share org-level keys
- [ ] OAuth scopes limited to required APIs per team (score, AI, plagiarism)
- [ ] Style guide editing restricted to team admins and above
- [ ] Guest role enforced for external collaborators
- [ ] API token rotation enforced quarterly
- [ ] SSO/SAML configured for all user authentication
- [ ] Seat usage audited monthly to reclaim inactive licenses

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` on API call | Expired OAuth token | Refresh token or regenerate credentials |
| User cannot access AI detection | Team lacks `ai-detection:read` scope | Add scope to team's OAuth client |
| Style guide edits not saving | User has member role, not admin | Promote to team admin or request admin to edit |
| Guest sees full suggestion set | Role not properly scoped on invite | Re-invite with explicit guest role |
| Seat limit reached | All team licenses assigned | Remove inactive members or purchase additional seats |

## Resources

- [Grammarly Enterprise](https://www.grammarly.com/business)
- [Grammarly Developer API](https://developer.grammarly.com/)

## Next Steps

See `grammarly-security-basics`.
