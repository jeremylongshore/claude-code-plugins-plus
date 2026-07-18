---
name: notion-enterprise-rbac
description: 'Configure Notion enterprise access control with OAuth, workspace permissions,
  and audit logging.

  Use when implementing OAuth public integrations, managing multi-workspace access,

  or building permission-aware Notion applications.

  Trigger with phrases like "notion SSO", "notion RBAC",

  "notion enterprise", "notion OAuth", "notion permissions", "notion multi-workspace".

  '
allowed-tools: Read, Write, Edit
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Enterprise RBAC

## Overview

Implement enterprise-grade access control for Notion integrations. This covers the full OAuth 2.0 authorization flow for public integrations (multi-tenant), per-workspace token storage with encryption at rest, Notion's page-level permission model and how to handle `ObjectNotFound` vs `RestrictedResource`, an application-level role system (admin/editor/viewer) layered on top of Notion's permissions, comprehensive audit logging to a Notion database, and workspace deauthorization cleanup.

## Prerequisites

- Notion public integration created at <https://www.notion.so/my-integrations> (for OAuth)
- `@notionhq/client` v2+ installed (`npm install @notionhq/client`)
- Python alternative: `notion-client` (`pip install notion-client`)
- Database for storing per-workspace tokens (PostgreSQL, DynamoDB, etc.)
- HTTPS endpoint for OAuth callback (required by Notion)

## Instructions

The workflow has three steps. Each is summarized here with its key entry
point; the complete, copy-ready code for all three lives in
[the full implementation reference](references/implementation.md).

### Step 1: OAuth 2.0 Authorization Flow

Notion uses OAuth 2.0 for public integrations to reach external workspaces.
Build an authorization URL with a random `state` for CSRF protection, redirect
the user, then on callback verify the state and exchange the code for a
workspace access token. Notion's token endpoint uses HTTP Basic auth with your
client id and secret:

```typescript
function getAuthorizationUrl(state: string): string {
  const params = new URLSearchParams({
    client_id: process.env.NOTION_OAUTH_CLIENT_ID!,
    response_type: 'code',
    owner: 'user',       // 'user' = user-level token, 'workspace' = workspace-level
    redirect_uri: process.env.NOTION_REDIRECT_URI!,
    state,               // CSRF protection — must verify on callback
  });
  return `https://api.notion.com/v1/oauth/authorize?${params}`;
}
```

The token exchange returns `access_token`, `bot_id` (the primary key per
installation), `workspace_id`, and owner metadata. A Python equivalent and the
full Express callback handler are in the
[implementation reference](references/implementation.md).

### Step 2: Token Storage and Permission-Aware API Calls

Store one token per `bot_id` (encrypt `access_token` at rest — use KMS or
column-level encryption in production), and construct a per-workspace `Client`
on demand. Wrap every page read so Notion's permission model is handled
explicitly rather than crashing:

```typescript
// ObjectNotFound = page exists but is NOT shared with the integration
// (NOT the same as deleted); RestrictedResource = missing capability;
// Unauthorized = token revoked. See the reference for the full switch.
async function safePageAccess(notion: Client, pageId: string) { /* ... */ }
```

The full `TokenStore` class, the complete `safePageAccess` switch, and a
`discoverAccessiblePages` search-pagination helper are in the
[implementation reference](references/implementation.md).

### Step 3: Application-Level Roles and Audit Logging

Layer an application role system (`admin`/`editor`/`viewer`) on top of Notion's
permissions via a `ROLE_PERMISSIONS` table and a `requirePermission` Express
middleware, and record every authorization decision through an `auditLog`
function that writes structured logs and optionally a Notion audit database.
Audit writes must never crash the app (wrap in try/catch), and workspace
deauthorization should log then revoke the stored token. The complete role
table, middleware, route examples, `auditLog`, and `handleDeauthorization` are
in the
[implementation reference](references/implementation.md).

## Output

- Complete OAuth 2.0 flow for multi-workspace access (TypeScript + Python)
- Per-workspace token storage with encryption guidance
- Permission-aware API calls handling ObjectNotFound vs RestrictedResource
- Content discovery via `search` endpoint
- Application-level role system (admin/editor/viewer) with Express middleware
- Comprehensive audit logging to structured logs and optionally to Notion database
- Workspace deauthorization cleanup handler

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| OAuth callback fails | Redirect URI mismatch | Must match exactly in integration settings (including trailing slash) |
| `invalid_grant` on token exchange | Code expired or already used | Authorization codes are single-use; restart OAuth flow |
| `ObjectNotFound` on page access | Page not shared with integration | User must share via "..." menu > Connections |
| `RestrictedResource` | Integration missing capability | Edit capabilities at notion.so/my-integrations |
| `Unauthorized` (401) | Token revoked by user | Prompt re-authorization; clean up stored token |
| State mismatch on callback | CSRF attack or session expired | Reject the callback; redirect to start OAuth again |

## Examples

A complete Express integration that wires the OAuth start and callback routes,
persists the workspace token, records a `workspace_authorized` audit entry, and
exposes a `/workspaces` listing endpoint is provided in
[the worked examples reference](references/examples.md).
It composes the `getAuthorizationUrl`, `exchangeCodeForToken`, `tokenStore`, and
`auditLog` building blocks from the three Instructions steps into a runnable
end-to-end flow.

## Resources

- [Full implementation walkthrough](references/implementation.md) — copy-ready code for all three steps
- [Worked Express example](references/examples.md) — end-to-end OAuth integration
- [Notion OAuth Authorization](https://developers.notion.com/docs/authorization) — full OAuth guide
- [Create a Token (OAuth)](https://developers.notion.com/reference/create-a-token) — token exchange endpoint
- [Authentication Reference](https://developers.notion.com/reference/authentication) — auth header format
- [Notion Capabilities](https://developers.notion.com/docs/create-a-notion-integration#capabilities) — read/update/insert/delete
- [Sharing and Permissions](https://developers.notion.com/docs/create-a-notion-integration#sharing-and-permissions) — page-level model
- **Next step:** for migrating data to and from Notion, see the `notion-migration-deep-dive` skill.
