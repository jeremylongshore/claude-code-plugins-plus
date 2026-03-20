---
name: evernote-enterprise-rbac
description: |
  Implement enterprise RBAC for Evernote integrations.
  Use when building multi-tenant systems, implementing
  role-based access, or handling business accounts.
  Trigger with phrases like "evernote enterprise", "evernote rbac",
  "evernote business", "evernote permissions".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Enterprise RBAC

## Overview
Implement role-based access control for Evernote integrations, including Evernote Business account handling, shared notebook permissions, multi-tenant architecture, and authorization middleware.

## Prerequisites
- Understanding of Evernote Business accounts and shared notebooks
- Multi-tenant application architecture
- Authentication/authorization infrastructure

## Instructions

### Step 1: Evernote Permission Model

Evernote has built-in sharing permissions for notebooks: `READ_NOTEBOOK`, `MODIFY_NOTEBOOK_PLUS_ACTIVITY`, `READ_NOTEBOOK_PLUS_ACTIVITY`, `GROUP`, `FULL_ACCESS`. Map these to your application's role system.

```javascript
const EvernotePermissions = {
  READ: 'READ_NOTEBOOK',
  WRITE: 'MODIFY_NOTEBOOK_PLUS_ACTIVITY',
  FULL: 'FULL_ACCESS'
};

const AppRoles = {
  viewer: [EvernotePermissions.READ],
  editor: [EvernotePermissions.READ, EvernotePermissions.WRITE],
  admin:  [EvernotePermissions.FULL]
};
```

### Step 2: RBAC Service

Build a service that checks whether a user has the required permission for an operation. Query shared notebook privileges via `noteStore.listSharedNotebooks()` and `getSharedNotebookByAuth()`.

```javascript
class RBACService {
  async canAccess(userToken, notebookGuid, requiredPermission) {
    const noteStore = this.getAuthenticatedNoteStore(userToken);
    const sharedNotebooks = await noteStore.listSharedNotebooks();
    const shared = sharedNotebooks.find(sn => sn.notebookGuid === notebookGuid);
    if (!shared) return false;
    return this.hasPermission(shared.privilege, requiredPermission);
  }
}
```

### Step 3: Authorization Middleware

Create Express middleware that validates the user's Evernote token and checks permissions before allowing access to protected routes.

### Step 4: Evernote Business Integration

For Evernote Business accounts, use `authenticateToBusiness()` to get a business token. Business notebooks are shared across the organization. Use `getBusinessNotebooks()` to list them.

### Step 5: Multi-Tenant Support

Isolate tenant data by scoping all Evernote operations to the tenant's access token. Never mix tokens between tenants. Store tenant-to-token mappings with encryption at rest.

For the full RBAC service, middleware, Business account integration, and multi-tenant architecture, see [Implementation Guide](references/implementation-guide.md).

## Output
- Evernote permission model mapped to application roles
- `RBACService` class with permission checking
- Express authorization middleware for protected routes
- Evernote Business account integration
- Multi-tenant token isolation and scoping

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `PERMISSION_DENIED` | User lacks required notebook permission | Verify shared notebook privileges |
| `INVALID_AUTH` | Business token expired | Re-authenticate with `authenticateToBusiness()` |
| Tenant data leak | Token scoping error | Validate tenant ID on every request |
| `LIMIT_REACHED` on sharing | Too many shared notebooks | Clean up unused shares (500 max per notebook) |

## Resources
- [Sharing and Permissions](https://dev.evernote.com/doc/articles/sharing.php)
- [API Key Permissions](https://dev.evernote.com/doc/articles/permissions.php)
- [Evernote Business](https://evernote.com/business)
- [API Reference - SharedNotebook](https://dev.evernote.com/doc/reference/)

## Next Steps
For migration strategies, see `evernote-migration-deep-dive`.

## Examples

**Team workspace**: Create a shared notebook for each team. Assign `editor` role to team members and `viewer` role to stakeholders. Use middleware to enforce permissions on all note operations.

**Business account sync**: Authenticate to the business account, list all business notebooks, and sync shared notes to a central dashboard accessible by all organization members.
