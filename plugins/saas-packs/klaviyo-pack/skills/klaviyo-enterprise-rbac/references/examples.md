# Klaviyo Enterprise RBAC — Worked Examples

Concrete scenarios showing how the scoped-key + application-RBAC model from
`SKILL.md` and `references/implementation.md` plays out in practice.

## Example 1: Least-privilege key per service

A reporting dashboard should never be able to send campaigns or write profiles.
Give it a read-only key and let the RBAC layer refuse anything else.

```typescript
// Reporting Dashboard -- read-only
// Key scopes: campaigns:read, metrics:read, segments:read, profiles:read
const reportingSession = new ApiKeySession(process.env.KLAVIYO_KEY_REPORTING!);
```

Result: even if application code accidentally calls a write endpoint, Klaviyo
returns `403 permission_denied` because the key lacks the scope — defence in
depth beyond the app-level `checkPermission` guard.

## Example 2: Gating a route by permission

The `marketer` role can send campaigns but must not delete profiles. The
middleware enforces this before the handler runs.

```typescript
// Marketer hits this — allowed (canSendCampaigns: true)
app.post('/api/klaviyo/campaigns/send',
  requireKlaviyoPermission('canSendCampaigns'),
  campaignSendHandler
);

// Marketer hits this — blocked with 403 (canDeleteProfiles: false)
app.delete('/api/klaviyo/profiles/:id',
  requireKlaviyoPermission('canDeleteProfiles'),
  profileDeleteHandler
);
```

The blocked request returns:

```json
{
  "error": "Forbidden",
  "message": "Role 'marketer' does not have permission: canDeleteProfiles"
}
```

## Example 3: Resolving a session from a role

Map an authenticated user's role to the correctly-scoped API key at request time.

```typescript
const role = req.user.klaviyoRole as AppRole;   // e.g. 'developer'
const session = getSessionForRole(role);         // uses KLAVIYO_KEY_DEVELOPER
// session now carries only the developer scopes: profiles:*, events:*, lists:*, webhooks:*, templates:*
```

If no key is configured for the role, `getSessionForRole` throws
`No API key configured for role: <role>` — fail closed rather than fall back to
an over-privileged key.

## Example 4: OAuth scope minimization for a marketplace app

A third-party integration should request only the scopes it uses. Requesting
`profiles:read profiles:write events:write lists:read` (not all scopes) keeps the
consent screen honest and limits blast radius if the token leaks.

```typescript
scopes: ['profiles:read', 'profiles:write', 'events:write', 'lists:read'],
```

## Example 5: Alerting on a destructive action

The audit trail flags profile deletions in real time so a compromised admin key
does not silently wipe data.

```typescript
if (entry.action === 'DELETE' && entry.resource.includes('profile')) {
  await alertSecurityTeam(`Profile deletion by ${entry.userId} (${entry.role})`);
}
```
