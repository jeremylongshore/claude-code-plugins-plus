---
name: glean-enterprise-rbac
description: |
  Map AD/Okta groups to Glean document permissions using allowedGroups.
  Trigger: "glean enterprise rbac", "enterprise-rbac".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
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

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps

See `glean-security-basics`.
