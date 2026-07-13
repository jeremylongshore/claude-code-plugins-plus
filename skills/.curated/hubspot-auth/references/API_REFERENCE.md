# HubSpot Auth — API Reference

Endpoint catalog, token shapes, rate-limit headers, and scope catalog for HubSpot authentication. Operational patterns (caching, rotation, multi-portal) live in `SKILL.md`; this document is the static reference.

## Token Types

| Type | Format | Expiry | Use |
|---|---|---|---|
| Private App token | `pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | None (rotate manually) | Server-to-server; no user context |
| OAuth access token | `CIX9...` | 1800 seconds (30 min) | User-authorized; scoped to user consent |
| OAuth refresh token | opaque string | 525,600 min (~1 year) if unused | Exchanges for new access tokens |

## OAuth Token Endpoint

```
POST https://api.hubapi.com/oauth/v1/token
Content-Type: application/x-www-form-urlencoded
```

### Authorization code exchange (first connect)

| Field | Required | Value |
|---|---|---|
| `grant_type` | yes | `authorization_code` |
| `client_id` | yes | from developer portal |
| `client_secret` | yes | from developer portal |
| `redirect_uri` | yes | must match registered URI exactly |
| `code` | yes | code from `?code=` query param in callback |

### Refresh token exchange (ongoing)

| Field | Required | Value |
|---|---|---|
| `grant_type` | yes | `refresh_token` |
| `client_id` | yes | from developer portal |
| `client_secret` | yes | from developer portal |
| `redirect_uri` | yes | must match registered URI |
| `refresh_token` | yes | from prior token response |

### Token response (200 OK)

```json
{
  "access_token": "CIX9...",
  "refresh_token": "abc123...",
  "expires_in": 1800,
  "token_type": "bearer"
}
```

Note: `scope` is NOT included in token response. Validate scopes separately via token-info endpoint.

### Token info endpoint

```
GET https://api.hubapi.com/oauth/v1/access-tokens/{access_token}
```

Response includes `scope_to_scope_description`, `hub_id`, `user`, `token_type`, `expires_in`.

### Error responses

| Status | `error` | Meaning |
|---|---|---|
| 400 | `invalid_client` | Wrong client ID or secret |
| 400 | `invalid_grant` | Authorization code expired or already used |
| 400 | `REFRESH_TOKEN_NOT_FOUND` | Refresh token expired (>1 year unused) or revoked |
| 401 | `INVALID_AUTHENTICATION` | Token expired, malformed, or revoked |
| 403 | `MISSING_SCOPES` | Token lacks required scope |
| 429 | `RATE_LIMIT` | Auth endpoint rate limit hit |

## OAuth Authorization URL

```
GET https://app.hubspot.com/oauth/authorize
  ?client_id={client_id}
  &redirect_uri={redirect_uri}
  &scope={space-separated scopes}
  &optional_scope={space-separated optional scopes}
```

## Authorization Header

```
Authorization: Bearer {access_token_or_private_app_token}
```

## Rate Limit Headers

HubSpot returns these on every response:

| Header | Value |
|---|---|
| `X-HubSpot-RateLimit-Daily` | Daily quota (varies by tier) |
| `X-HubSpot-RateLimit-Daily-Remaining` | Remaining today |
| `X-HubSpot-RateLimit-Interval-Milliseconds` | Rolling window size (ms) |
| `X-HubSpot-RateLimit-Max` | Max calls in window |
| `X-HubSpot-RateLimit-Remaining` | Remaining in window |
| `Retry-After` | Seconds to wait (on 429) |

### Rate limits by tier

| Tier | Burst | Daily |
|---|---|---|
| Free / Starter | 100 req/10s | 250,000 |
| Professional | 150 req/10s | 500,000 |
| Enterprise | 150 req/10s | 500,000 |
| OAuth apps | 100 req/10s per portal | varies |

Auth token endpoint additional limit: **10 requests/10s**.

## Scope Catalog (CRM — common)

| Scope | Access |
|---|---|
| `crm.objects.contacts.read` | Read contact records |
| `crm.objects.contacts.write` | Create/update/delete contacts |
| `crm.objects.companies.read` | Read company records |
| `crm.objects.companies.write` | Create/update/delete companies |
| `crm.objects.deals.read` | Read deal records |
| `crm.objects.deals.write` | Create/update/delete deals |
| `crm.objects.custom.read` | Read custom objects |
| `crm.objects.custom.write` | Write custom objects |
| `crm.schemas.contacts.read` | Read contact property definitions |
| `crm.schemas.contacts.write` | Manage contact properties |
| `crm.associations.read` | Read CRM associations |
| `crm.associations.write` | Write CRM associations |
| `tickets` | Read/write support tickets |
| `e-commerce` | Read/write e-commerce data |
| `automation` | Read/write workflow automations |
| `oauth` | Required for OAuth public apps |

Full catalog: https://developers.hubspot.com/docs/guides/apps/authentication/scopes

## Private App Token Format

```
pat-{datacenter}-{32-char-uuid}
# Example: pat-na1-{your-uuid-here}
```

Datacenter codes: `na1` (North America), `eu1` (Europe), `au1` (Australia).

The token datacenter code must match the portal's datacenter; requests to the wrong datacenter endpoint return 404.

## Token Revocation

HubSpot does not expose a `/revoke` endpoint. To invalidate:

- **Private app token**: Rotate in Settings → Integrations → Private Apps → your app → Rotate token
- **OAuth token**: Disconnect the app from Settings → Integrations → Connected Apps, or the user disconnects from their account

Rotation generates a new token immediately; the old token stops working instantly.
