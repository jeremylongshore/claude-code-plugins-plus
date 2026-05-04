# Guidewire Cloud API — Auth Reference

Endpoint catalog and response shapes for the auth-side of Cloud API integration. Operational patterns (caching, rotation, recovery) live in `SKILL.md`; this document is the static reference.

## OAuth2 token endpoint

```
POST https://hub.[TENANT].guidewire.net/oauth/token
Content-Type: application/x-www-form-urlencoded
```

**Request body (URL-encoded):**

| Field | Required | Notes |
|---|---|---|
| `grant_type` | yes | always `client_credentials` for service apps |
| `client_id` | yes | from GCC > Identity & Access > Applications |
| `client_secret` | yes | rotatable; supports dual-secret window during rotation |
| `scope` | yes | space-separated tenant-configured scope strings |

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "pc.account.read pc.account.write"
}
```

`expires_in` is advisory; the JWT's `exp` claim is authoritative. Decode and use `exp` for cache-expiry math, not `Date.now() + 3600 * 1000`. Clock skew between the runtime and Hub is the most common cause of premature `401`.

**Error responses (400):**

```json
{ "error": "invalid_client", "error_description": "..." }
{ "error": "invalid_scope", "error_description": "..." }
{ "error": "invalid_grant", "error_description": "..." }
```

`invalid_grant` indicates the secret was rotated and the runtime still holds the old value — fall back to the secondary secret per dual-secret pattern, or trigger a controlled restart if no secondary is configured.

## JWT structure (decoded)

A typical Guidewire-issued JWT decodes to (header omitted):

```json
{
  "iss": "https://hub.[TENANT].guidewire.net",
  "sub": "[client-id]",
  "aud": ["pc", "cc", "bc"],
  "exp": 1735689600,
  "iat": 1735686000,
  "scope": "pc.account.read pc.account.write cc.claim.read",
  "tenant": "[tenant-slug]"
}
```

Validate `aud` matches the product you are calling (calling PC with a token whose `aud` lacks `pc` returns `401` even with valid scopes). Validate `scope` contains every required scope on every refresh — this is the scope-drift gate.

## Verification probe (CI smoke test)

```http
GET https://[TENANT].guidewire.net/pc/rest/v1/account/v1/accounts?pageSize=1
Authorization: Bearer [token]
```

Returns `200 OK` with the canonical Cloud API response envelope. Use this in CI as a deploy-gate: a deploy that cannot list accounts has broken auth and should not pass the gate.

```json
{
  "count": 42,
  "data": [
    {
      "attributes": { "accountNumber": "A000001", "accountStatus": { "code": "Active" } },
      "checksum": "abc123",
      "links": { "self": { "href": "/account/v1/accounts/pc:8001" } }
    }
  ],
  "links": { "next": { "href": "/account/v1/accounts?pageSize=1&offsetToken=..." } }
}
```

## HTTP status code matrix (auth-relevant)

| Status | When | Action |
|---|---|---|
| `200` on `/oauth/token` | normal token issuance | cache and reuse |
| `400` on `/oauth/token` | `invalid_client`, `invalid_scope`, `invalid_grant` | inspect `error` field, do not retry blindly |
| `429` on `/oauth/token` | thundering-herd refresh | single-flight gate is missing or broken; fix the cache |
| `500/502/503` on `/oauth/token` | transient Hub or upstream issue | retry with exponential backoff, max 3 attempts |
| `401` on Cloud API | token expired, audience mismatch, or scope no longer issued | proactive refresh window prevents most expiry cases; verify `aud` claim |
| `403` on Cloud API | least-privilege violation | do not retry; alert and re-issue with corrected role assignment in GCC |
| `409` on Cloud API | stale `checksum` (not auth) | covered in `guidewire-sdk-patterns` |
| TLS handshake failure | private-CA chain not trusted | install CA at JVM/init-container layer |

## Domain conventions reference

| Pattern | Domain | Used for |
|---|---|---|
| `gcc.guidewire.com` | `*.guidewire.com` | Console UI; tenant administration; app registration |
| `hub.[TENANT].guidewire.net` | `*.guidewire.net` | OAuth2 token issuance |
| `[TENANT].guidewire.net/pc/rest/v1` | `*.guidewire.net` | PolicyCenter Cloud API runtime |
| `[TENANT].guidewire.net/cc/rest/v1` | `*.guidewire.net` | ClaimCenter Cloud API runtime |
| `[TENANT].guidewire.net/bc/rest/v1` | `*.guidewire.net` | BillingCenter Cloud API runtime |

Egress firewalls must allow `*.guidewire.net` for runtime APIs; `*.guidewire.com` egress is only required for tools that hit the console (CLI utilities, infrastructure-as-code that registers apps). A common misconfiguration is allowing only `*.guidewire.com` and seeing every Cloud API call fail at DNS resolution.

## Authorization Code flow (Jutro browser apps)

This skill covers Service Application (Client Credentials) flow only. Browser applications using Jutro frontends use the Authorization Code flow with PKCE, which requires session/cookie handling outside the scope of a backend integration. Treat that as a separate integration shape.

Reference: [RFC 7636 — PKCE](https://datatracker.ietf.org/doc/html/rfc7636) and the Guidewire Cloud Platform Identity Federation guide on the developer portal.

## Related references

- `references/implementation-guide.md` — extended walkthrough with environment-specific notes
- Sibling skill `guidewire-sdk-patterns` — REST client patterns, retry/backoff, error mapping
- Sibling skill `guidewire-security-and-rbac` — secret-store architecture, audit trail, PII handling
