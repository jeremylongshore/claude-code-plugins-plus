---
name: glean-enterprise-rbac
description: 'Map AD/Okta groups to Glean document permissions using allowedGroups.

  Trigger: "glean enterprise rbac", "enterprise-rbac".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.8.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- enterprise-search
- glean
compatibility: Designed for Claude Code
---
# Glean Enterprise RBAC

## Overview

Glean's enterprise search aggregates content from dozens of connectors (Google Drive, Confluence, Slack, Salesforce). RBAC ensures users only see documents they are authorized to access. Permissions flow from source systems through connector-level ACLs into Glean's unified index. Misconfigured permissions mean search results leak sensitive data across teams. SOC 2 and GDPR compliance require document-level access control and full audit trails on who searched what.

## Role Hierarchy

| Role | Permissions | Scope |
|------|------------|-------|
| Super Admin | Create API tokens, manage all connectors, configure SSO | Organization-wide |
| Admin | Add/edit datasources, manage user groups, view analytics | Assigned datasources |
| Content Manager | Set document permissions, manage allowedGroups per datasource | Own datasources |
| User | Search and view permitted documents | Documents matching ACLs |
| Viewer | Search only, no document previews or snippets | Restricted document set |

## Permission Check

```typescript
async function checkDocumentAccess(userId: string, documentId: string): Promise<boolean> {
  const response = await fetch(`${GLEAN_API}/permissions/check`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${GLEAN_API_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId, documentId }),
  });
  const result = await response.json();
  return result.hasAccess ?? false;
}
```

## Role Assignment

```typescript
async function assignDatasourceRole(email: string, datasource: string, role: 'admin' | 'viewer'): Promise<void> {
  await fetch(`${GLEAN_API}/datasources/${datasource}/permissions`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${GLEAN_API_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ user: email, role, allowedGroups: [`${datasource}-${role}s`] }),
  });
}

async function revokeDatasourceAccess(email: string, datasource: string): Promise<void> {
  await fetch(`${GLEAN_API}/datasources/${datasource}/permissions/${email}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${GLEAN_API_TOKEN}` },
  });
}
```

## Audit Logging

```typescript
interface GleanAuditEntry {
  timestamp: string; userId: string; action: 'search' | 'view' | 'index' | 'permission_change';
  datasource: string; query?: string; documentId?: string; result: 'allowed' | 'denied';
}

function logSearchAccess(entry: GleanAuditEntry): void {
  console.log(JSON.stringify({ ...entry, org: process.env.GLEAN_ORG_ID }));
}
```

## RBAC Checklist

- [ ] Each connector maps source-system ACLs to Glean allowedGroups
- [ ] API tokens scoped per datasource, not organization-wide
- [ ] SAML/SSO groups synced with Glean user groups daily
- [ ] Document-level permissions verified after each connector sync
- [ ] Search analytics reviewed monthly for unauthorized access patterns
- [ ] Token rotation policy enforced quarterly
- [ ] Sensitive datasources restricted to named allowedGroups only

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| User sees documents from wrong team | AllowedGroups not mapped to connector | Reconfigure connector ACL mapping in admin console |
| `403 Forbidden` on search API | Expired or wrong-scope API token | Regenerate token with correct datasource scope |
| Stale permissions after IdP change | Connector sync lag | Trigger manual resync from Glean admin |
| Missing search results | Overly restrictive allowedGroups | Audit group membership against source system ACLs |

## Prerequisites

- A source-of-truth group inventory, named data owner, and two synthetic test identities: one authorized and one explicitly denied.
- A least-privilege admin role that can stage a mapping in one non-production datasource without changing organization-wide access.
- A rollback record capturing the prior mapping by opaque group ID; never place real group membership exports or search results in tickets.

## Instructions

1. Map source ACL groups to opaque target groups and require a one-to-one owner approval for every expanded access path.
2. Stage the change on a low-risk datasource, then run the allow and deny test identities against a fictitious document identifier.
3. Promote only when both tests match the source ACL; otherwise restore the prior mapping and investigate the IdP or connector sync boundary.
4. Log the actor, change request, datasource, mapping revision, and outcomes without query text, document titles, or user email addresses.
5. Recheck after the next identity synchronization and revoke the mapping immediately if it grants access beyond the approved scope.

## Output

Produce an RBAC change receipt: datasource, prior and new mapping revisions, approving owner, staged/production status, synthetic allow and deny outcomes, sync watermark, and rollback reference. The receipt must contain only opaque IDs and aggregate counts.

## Examples

Example: `datasource=staging-contracts; mapping_rev=42; owner=legal-ops; allow_probe=pass; deny_probe=pass; sync=2026-08-27T14:00Z; rollback=rev41`. This proves the boundary without disclosing membership or content.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps

See `glean-security-basics`.
