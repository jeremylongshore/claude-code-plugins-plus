---
name: klaviyo-enterprise-rbac
description: |
  Configure Klaviyo enterprise access control with API key scopes and OAuth.
  Use when implementing per-key scoping, configuring OAuth app authorization,
  or setting up organization-level access controls for Klaviyo.
  Trigger with phrases like "klaviyo scopes", "klaviyo RBAC",
  "klaviyo enterprise", "klaviyo permissions", "klaviyo OAuth", "klaviyo access control".
allowed-tools: Read, Write
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Enterprise RBAC

## Overview

Enterprise access control for Klaviyo: API key scoping with granular read/write permissions, OAuth app authorization flows, and application-level RBAC built on top of Klaviyo's scope system. Klaviyo has no built-in roles, so you compose least-privilege access from scoped keys plus an application permission layer.

## Prerequisites

- Klaviyo account with API key management access
- Understanding of OAuth 2.0 (for OAuth apps)
- Application requiring per-user or per-role Klaviyo access

## Klaviyo Access Control Model

Klaviyo uses **scoped API keys** and **OAuth** for access control. There are no built-in "roles" in Klaviyo's API -- you implement RBAC by creating multiple API keys with different scopes.

### API Key Scopes

| Scope | Read | Write | What It Controls |
|-------|------|-------|-----------------|
| `accounts` | Account info | N/A | Organization name, timezone |
| `campaigns` | List campaigns | Create/send campaigns | Email, SMS, push campaigns |
| `catalogs` | Browse items | CRUD catalog items | Product catalog management |
| `coupons` | List coupons | Create coupons | Coupon/discount codes |
| `data-privacy` | N/A | Delete profiles | GDPR/CCPA deletion requests |
| `events` | Query events | Track events | Server-side event tracking |
| `flows` | List flows | Create/update flows | Flow automation |
| `images` | List images | Upload images | Email template images |
| `lists` | List lists | CRUD lists/members | List management |
| `metrics` | Query metrics | N/A | Metric aggregations |
| `profiles` | Read profiles | Create/update profiles | Profile management |
| `segments` | Read segments | N/A | Segment queries |
| `tags` | Read tags | CRUD tags | Resource tagging |
| `templates` | Read templates | Create/update templates | Email templates |
| `webhooks` | List webhooks | CRUD webhooks | Webhook subscriptions |

## Instructions

The full, copy-ready code for every step lives in
[the implementation walkthrough](references/implementation.md). At a high level
the workflow is five steps:

1. **Create scoped API keys** — one key per service/role in the Klaviyo
   dashboard (**Settings > API Keys**), each granted only the scopes it needs.
   A profile-sync service gets `profiles:*` + `lists:*`; a reporting dashboard
   gets `*:read` only; the admin key gets everything and is used sparingly.
2. **Model application-level RBAC** — map each app role (admin, marketer,
   developer, viewer, service) to a permission set and to its scoped key, so the
   app enforces intent and the key enforces the hard boundary.
3. **Add permission middleware** — reject requests whose role lacks the required
   permission before the handler runs (401 for no role, 403 for wrong role).
4. **Wire the OAuth app flow** — for third-party/marketplace integrations,
   request only the scopes the app uses, then exchange the code for tokens.
5. **Record an audit trail** — log every access with role/action/resource and
   alert the security team on destructive actions like profile deletion.

The essential skeleton — a least-privilege key plus the permission check — looks
like this:

```typescript
// One scoped key per service — reporting is read-only
const reportingSession = new ApiKeySession(process.env.KLAVIYO_KEY_REPORTING!);

// App-level guard: refuse before the handler runs
app.post('/api/klaviyo/campaigns/send',
  requireKlaviyoPermission('canSendCampaigns'),
  campaignSendHandler
);
```

See [the implementation walkthrough](references/implementation.md) for the role
permission matrix, `getSessionForRole`, the middleware, the OAuth exchange, the
audit logger, and the full environment variable layout in
[the implementation walkthrough](references/implementation.md).

## Output

Applying this skill produces:

- **Multiple scoped API keys** in Klaviyo, one per service/role, each holding
  only the scopes that service needs (defence in depth beyond app-level checks).
- **An RBAC module** (`src/klaviyo/rbac.ts`) exporting `checkPermission` and
  `getSessionForRole`, mapping the five app roles to permissions and keys.
- **Permission middleware** (`src/middleware/klaviyo-auth.ts`) that returns 401
  when no role is assigned and 403 when a role lacks the requested permission.
- **An OAuth flow** for marketplace apps requesting minimized scopes.
- **An audit log** (`src/klaviyo/audit.ts`) that records access and alerts on
  destructive actions.

A blocked request returns a structured 403, e.g.:

```json
{ "error": "Forbidden", "message": "Role 'marketer' does not have permission: canDeleteProfiles" }
```

## Examples

Grounded, end-to-end scenarios — least-privilege keys, route gating by
permission, resolving a session from a role, OAuth scope minimization, and
alerting on a destructive action — are collected in
[the examples reference](references/examples.md).

Quick illustration — a marketer is allowed to send campaigns but blocked from
deleting profiles, purely from the role permission set:

```typescript
// canSendCampaigns: true  -> allowed
app.post('/api/klaviyo/campaigns/send', requireKlaviyoPermission('canSendCampaigns'), campaignSendHandler);

// canDeleteProfiles: false -> 403 Forbidden
app.delete('/api/klaviyo/profiles/:id', requireKlaviyoPermission('canDeleteProfiles'), profileDeleteHandler);
```

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `permission_denied` | 403 | API key missing required scope | Create new key with correct scopes |
| OAuth code expired | 400 | User took too long to authorize | Retry authorization flow |
| Token refresh failed | 401 | Refresh token revoked | Re-authorize the app |
| Role not assigned | 401 | User missing `klaviyoRole` | Assign role in your user management |

## Resources

- [Full implementation walkthrough](references/implementation.md) — all five steps, verbatim code
- [Worked examples](references/examples.md) — least-privilege, route gating, OAuth minimization
- [Klaviyo API Scopes](https://developers.klaviyo.com/en/docs/authenticate_)
- [OAuth Setup Guide](https://developers.klaviyo.com/en/docs/set_up_oauth)
- [Update OAuth Scopes](https://developers.klaviyo.com/en/docs/update_your_oauth_scopes)
- For major migrations, see the `klaviyo-migration-deep-dive` skill.
