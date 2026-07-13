# HubSpot Agency Multi-Portal — API Reference

Endpoint catalog, per-portal rate limit behavior, token format details, portal identity verification, and the audit log schema. Operational patterns (credential router, bulk onboarding, rotation) live in `SKILL.md` and `implementation-guide.md`; this document is the static reference.

## Portal Identity Endpoint

The single most important endpoint for multi-portal management. Use it to verify that a token belongs to the expected portal before admitting it to the credential store, and to detect portal type changes (e.g., trial → standard, standard → sandbox).

```
GET https://api.hubapi.com/account-info/v3/details
Authorization: Bearer {private_app_token}
```

### Response (200 OK)

```json
{
  "portalId": 12345678,
  "timeZone": "America/New_York",
  "currency": "USD",
  "utcOffset": "-05:00",
  "utcOffsetMilliseconds": -18000000,
  "uiDomain": "app.hubspot.com",
  "dataHostingLocation": "na1",
  "portalType": "STANDARD"
}
```

### Response fields

| Field | Type | Notes |
|---|---|---|
| `portalId` | `number` | The definitive identifier for this portal. Store this and verify on every onboard and rotation. |
| `timeZone` | `string` | IANA timezone string — use for scheduling compliance reports to client's local business hours |
| `currency` | `string` | ISO 4217 currency code — relevant for deal/revenue reporting |
| `dataHostingLocation` | `string` | `"na1"` / `"eu1"` / `"au1"` — must match the `pat-{datacenter}-*` prefix of the token |
| `portalType` | `string` | `"STANDARD"` / `"DEVELOPER"` / `"SANDBOX"` / `"TRIAL"` — alert if a client portal changes type unexpectedly |

### Error responses

| Status | Meaning | Action |
|---|---|---|
| `401` | Token revoked or malformed | Reject; flag for rotation |
| `403` | Token lacks `account-info` scope | Re-create private app with `account-info` scope |
| `404` | Portal does not exist | Token may belong to a deleted portal; retire from credential store |

### Required private app scope

The private app must have `account-info` (read) scope to call this endpoint. This scope is in addition to any CRM scopes the integration needs.

## Token Format and Portal Detection

HubSpot private-app tokens use a structured prefix that encodes the datacenter:

```
pat-{datacenter}-{8hex}-{4hex}-{4hex}-{4hex}-{12hex}
# Examples:
# pat-na1-{your-uuid}   (North America)
# pat-eu1-{your-uuid}   (Europe)
# pat-au1-{your-uuid}   (Australia)
```

### Datacenter codes

| Code | Region | HubSpot data center |
|---|---|---|
| `na1` | North America | Virginia, USA |
| `eu1` | Europe | Frankfurt, Germany |
| `au1` | Australia/APAC | Sydney, Australia |

### Token validation regex

```typescript
const PRIVATE_APP_TOKEN_RE = /^pat-(na1|eu1|au1)-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function validateTokenFormat(token: string): { valid: boolean; datacenter?: string } {
  const match = token.match(PRIVATE_APP_TOKEN_RE);
  if (!match) return { valid: false };
  return { valid: true, datacenter: match[1] };
}
```

**Important:** The token's datacenter prefix must match the portal's `dataHostingLocation` returned by `account-info/v3/details`. A mismatch will cause 404 errors on API calls even though the token authenticates correctly (HubSpot routes based on `Authorization` header, but some endpoints may return wrong-datacenter errors).

## Per-Portal Rate Limits

Every HubSpot portal has its own independent quota. Agency integrations reading all portals have `N portals × 500K/day` total capacity — but only if each portal is accessed with its own token. A shared token collapses all quota to the token's home portal.

### Quota by portal tier

| Portal Tier | Burst limit | Daily limit |
|---|---|---|
| Free | 100 req/10s | 250,000 |
| Starter | 100 req/10s | 250,000 |
| Professional | 150 req/10s | 500,000 |
| Enterprise | 150 req/10s | 500,000 |
| Sandbox portals | 100 req/10s | 250,000 |

### Rate limit response headers

HubSpot returns these headers on every API response. Log them in every audit record.

| Header | Type | Notes |
|---|---|---|
| `X-HubSpot-RateLimit-Daily` | `number` | Portal's total daily quota |
| `X-HubSpot-RateLimit-Daily-Remaining` | `number` | Remaining calls today — **primary monitoring signal** |
| `X-HubSpot-RateLimit-Interval-Milliseconds` | `number` | Rolling window duration in ms (usually 10,000) |
| `X-HubSpot-RateLimit-Max` | `number` | Max calls allowed in the rolling window |
| `X-HubSpot-RateLimit-Remaining` | `number` | Remaining calls in the current rolling window |
| `Retry-After` | `number` | Seconds to wait before retrying (on 429 only) |

### 429 response body

```json
{
  "status": "error",
  "message": "You have reached your secondly limit.",
  "error": "RATE_LIMIT",
  "errorType": "TEN_SECONDLY_ROLLING",
  "policyName": "TEN_SECONDLY_ROLLING",
  "requestId": "abc123"
}
```

Distinct `errorType` values:

| `errorType` | Meaning | Backoff strategy |
|---|---|---|
| `TEN_SECONDLY_ROLLING` | Burst limit hit | Wait `Retry-After` seconds (usually 10) |
| `DAILY` | Daily quota exhausted | Stop for this portal until midnight UTC; alert |

## Authorization Header

```
Authorization: Bearer {private_app_token}
```

No other auth schemes (Basic, API Key query param) should be used in new integrations. The `hapikey` query parameter is deprecated.

## CRM Write Endpoint Pattern

For multi-portal safety, always log the `id` returned from write operations alongside the `clientSlug` and `portalId`. This creates a recoverable audit trail if a write accidentally lands in the wrong portal.

```
POST https://api.hubapi.com/crm/v3/objects/{objectType}
Authorization: Bearer {token}
Content-Type: application/json

{
  "properties": {
    "email": "contact@example.com",
    "firstname": "Jane",
    "lastname": "Doe"
  }
}
```

Response `201 Created`:

```json
{
  "id": "701",
  "properties": {
    "email": "contact@example.com",
    "firstname": "Jane",
    "lastname": "Doe",
    "hs_object_id": "701",
    "createdate": "2026-05-11T12:00:00.000Z"
  },
  "createdAt": "2026-05-11T12:00:00.000Z",
  "updatedAt": "2026-05-11T12:00:00.000Z",
  "archived": false
}
```

The response does NOT include `portalId` — this is why the credential router must enforce token isolation before the call, not via post-hoc response validation.

## Audit Log Schema

Every API call made through the agency router must emit a structured audit record. The schema is the single source of truth for compliance reporting and SLA verification.

### JSON audit record

```json
{
  "ts": "2026-05-11T14:30:00.000Z",
  "portalId": 12345678,
  "clientSlug": "acme-corp",
  "method": "POST",
  "path": "/crm/v3/objects/contacts",
  "statusCode": 201,
  "durationMs": 187,
  "objectType": "contacts",
  "objectId": "701",
  "actor": "hubspot-agency-router/2.0.0",
  "rateLimitRemaining": 498230,
  "requestId": "abc123def456"
}
```

### Field definitions

| Field | Type | Required | Notes |
|---|---|---|---|
| `ts` | ISO 8601 string | Yes | UTC timestamp of the request completion |
| `portalId` | number | Yes | From the credential store — verified on onboard |
| `clientSlug` | string | Yes | kebab-case client identifier |
| `method` | string | Yes | `GET` / `POST` / `PATCH` / `DELETE` |
| `path` | string | Yes | API path without base URL |
| `statusCode` | number | Yes | HTTP response code |
| `durationMs` | number | Yes | Round-trip latency |
| `objectType` | string | When CRM call | `contacts` / `deals` / `companies` / etc. |
| `objectId` | string | When single-object call | Object ID from path or response |
| `actor` | string | Yes | Service name and version |
| `rateLimitRemaining` | number | Yes | From `X-HubSpot-RateLimit-Daily-Remaining` header |
| `requestId` | string | When present | From HubSpot response headers |

### Audit log storage options

| Storage | Use when | Notes |
|---|---|---|
| `stdout` (JSON lines) | Containers / Kubernetes | Collected by log aggregator (Datadog, Splunk, CloudWatch) |
| Append-only file | VM / bare-metal | Rotate with logrotate; use `.jsonl` extension |
| Database table | Query-heavy compliance | Index on `(clientSlug, ts)` for report queries |
| Message queue | High volume | Kafka / SQS → ETL → database; decouples write latency |

### GDPR/CCPA compliance query pattern

```sql
-- Per-client API call summary for a date range (SQLite / PostgreSQL)
SELECT
  clientSlug,
  portalId,
  DATE(ts) AS call_date,
  method,
  objectType,
  COUNT(*) AS call_count,
  MIN(durationMs) AS min_ms,
  MAX(durationMs) AS max_ms,
  AVG(durationMs) AS avg_ms
FROM audit_log
WHERE clientSlug = 'acme-corp'
  AND ts >= '2026-05-01'
  AND ts < '2026-06-01'
GROUP BY clientSlug, portalId, call_date, method, objectType
ORDER BY call_date, objectType;
```

## Token Rotation API Limitation

HubSpot does not provide an API for rotating private-app tokens. Rotation is UI-only:

**Settings → Integrations → Private Apps → {your app} → Auth tab → Rotate token**

Rotating generates a new token and **immediately** revokes the old one. There is no overlap window. This means all downstream systems must be updated before rotation, or they will fail immediately.

See `implementation-guide.md` for the per-portal rotation runbook with cross-system checklist.
