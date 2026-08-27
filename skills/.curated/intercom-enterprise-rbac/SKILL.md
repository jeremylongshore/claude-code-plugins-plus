---
name: intercom-enterprise-rbac
description: |
  Configure Intercom enterprise OAuth, admin roles, and app-level access control.
  Use when implementing OAuth integration, managing admin permissions, or setting
  up organization-level controls for Intercom — e.g. gating a delete endpoint by
  role, installing a public app for a customer workspace, or adding admin audit
  logging.
  Trigger with phrases like "intercom OAuth", "intercom RBAC", "intercom
  enterprise", "intercom roles", "intercom permissions", "intercom admin access".
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Enterprise RBAC

## Overview

Configure enterprise-grade access control for Intercom integrations with OAuth
scopes, admin role management, and app-level permission enforcement.

The workflow covers the full path: enumerate the workspace's admins and teams,
authorize a public app with least-privilege scopes, enforce per-operation
permissions at the application layer, route conversations to teams, and audit
sensitive admin actions.

The high-level workflow lives here; complete, copy-ready code for every step is in
[references/implementation.md](references/implementation.md), and end-to-end
scenarios are in [references/examples.md](references/examples.md).

## Prerequisites

- Intercom workspace with admin access
- Understanding of OAuth 2.0 flows
- For public apps: OAuth configured in Developer Hub
- `intercom-client` installed and `INTERCOM_ACCESS_TOKEN` (or OAuth client
  credentials) available in the environment

## Intercom Admin Roles

Intercom has built-in admin roles that control workspace access:

| Role | API Access | Capabilities |
|------|-----------|-------------|
| Owner | Full | All operations, billing, workspace settings |
| Admin | Full | Manage contacts, conversations, content |
| Agent | Limited | Reply to conversations, view contacts |
| Custom roles | Configurable | Enterprise plan feature |

These built-in roles govern access inside the Intercom UI and API. Map them onto
explicit permissions (Step 3) rather than trusting the role name alone.

## Instructions

Follow the five steps in order. Each step's full code is in
[references/implementation.md](references/implementation.md) under the matching
heading — the skeletons below show the essential call surface.

### Step 1: List admins and roles

Enumerate every admin and team to map real identities to permissions.

```typescript
const client = new IntercomClient({ token: process.env.INTERCOM_ACCESS_TOKEN! });
const adminList = await client.admins.list();
// admin.type is "admin" or "team" — teams are used for routing in Step 4
```

### Step 2: OAuth scope-based access control

For public apps, request the **minimal** scopes required, build the authorization
URL with a CSRF `state`, and exchange the returned code for a per-workspace token.

```typescript
const authUrl = getAuthUrl(crypto.randomUUID());  // redirect the user here
const { token } = await exchangeCode(code);        // on callback
```

Store one token per workspace (`WorkspaceAuth`) for multi-tenant installs. Full
exchange + storage code: see references.

### Step 3: App-level permission enforcement

Define an explicit `IntercomPermission` union, map each role to a permission set,
and gate operations with middleware — never rely on the role name at the call site.

```typescript
function checkPermission(role: string, perm: IntercomPermission): boolean { /* … */ }
app.delete("/api/contacts/:id", requirePermission("contacts:delete"), handler);
```

### Step 4: Team-based conversation assignment

Filter admins where `type === "team"`, then assign conversations to the right
team by topic via `client.conversations.assign(...)`.

### Step 5: Audit logging for admin actions

Record every privileged action to a durable audit store, mirror it as an Intercom
data event for visibility, and warn on `delete`/`settings` operations.

For the OAuth scope-to-endpoint mapping, see the **OAuth Scope Reference** table
in [references/implementation.md](references/implementation.md).

## Output

Applying this skill produces:

- An admin/team inventory printed from `client.admins.list()` (name, email, id, type).
- A working OAuth authorization + token-exchange flow that yields a per-workspace
  access token stored as a `WorkspaceAuth` record.
- A permission layer (`ROLE_PERMISSIONS`, `checkPermission`, `requirePermission`)
  that returns `403 Forbidden` with the missing permission when a caller lacks it.
- Topic-based team routing on conversations.
- Audit entries in the audit store plus mirrored `admin-action-logged` Intercom data
  events, with console warnings on sensitive actions.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| OAuth callback fails | Wrong redirect URI | Match exactly in Developer Hub |
| `forbidden` (403) | Missing OAuth scope | Add scope, user must re-authorize |
| Token revoked | User uninstalled app | Handle gracefully, notify admin |
| Admin not found | Admin left workspace | Remove from the local system |
| Team assignment fails | Team ID invalid | List teams first with `admins.list()` |

## Examples

- **Gate a delete endpoint by role** — only owners reach the handler; agents get
  a structured `403`. See [references/examples.md](references/examples.md) § Example 1.
- **Install a public app for a new customer workspace** — consent → code exchange
  → per-workspace token persistence. See § Example 2.
- **Route + audit a sensitive assignment in one flow** — route to the billing team
  and record the action. See § Example 3.

## Resources

- [Authentication](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication)
- [Setting up OAuth](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/setting-up-oauth)
- [OAuth Scopes](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/oauth-scopes)
- [Admins API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/admins)

## Next Steps

For major workspace migrations that move data and reconfigure roles at scale, see
the `intercom-migration-deep-dive` skill, which builds on the RBAC primitives
established here.
