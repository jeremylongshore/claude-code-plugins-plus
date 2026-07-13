# HubSpot Rate Limit Survival — API Reference

Static reference for rate-limit headers, limit tiers by plan, batch API endpoint signatures, and 429 response shapes. Operational patterns (token bucket, queue architecture, shutoff valve) live in `SKILL.md`; this document is the lookup table.

## Rate Limit Headers

HubSpot returns these headers on **every** API response — not just 429s. Read them on every call to maintain an accurate local picture of both rate-limit buckets.

| Header | Type | Description |
|---|---|---|
| `X-HubSpot-RateLimit-Daily` | integer | Total daily quota for this portal (varies by plan; see tier table below) |
| `X-HubSpot-RateLimit-Daily-Remaining` | integer | Calls remaining in the current UTC day. Resets at midnight UTC. |
| `X-HubSpot-RateLimit-Interval-Milliseconds` | integer | Length of the rolling burst window in milliseconds. Typically `10000` (10 seconds). |
| `X-HubSpot-RateLimit-Max` | integer | Maximum calls permitted in one burst window. Reveals plan tier: 100 = standard, 150 = OAuth Professional, 1000 = Ops Hub Enterprise 10s window. |
| `X-HubSpot-RateLimit-Remaining` | integer | Calls remaining in the current burst window. Not shared with daily counter — these are independent. |
| `Retry-After` | integer (seconds) | Present only on 429 responses. The exact number of seconds HubSpot instructs you to wait before retrying. Always honor this value precisely — do not substitute a fixed or exponential delay when this header is present. |

**Critical semantic distinction:** `X-HubSpot-RateLimit-Daily-Remaining` and `X-HubSpot-RateLimit-Remaining` decrement from two **independent** counters. Burning the burst window does not affect the daily counter. Exhausting the daily counter does not affect the burst window. Rate-limit logic that conflates them will misfire.

**Header availability by version:**

- Headers above apply to all `v3` CRM API endpoints.
- Older v1/v2 endpoints may return `X-HubSpot-RateLimit-Secondly` (deprecated naming) instead of the interval-based headers. Use `X-HubSpot-RateLimit-Daily-Remaining` as the common denominator across versions.

## Rate Limit Tiers by Plan

Portal-level limits. **All apps in the same portal share the same buckets** — private apps and OAuth apps are not isolated from each other.

| Plan | Burst Window | Burst Limit | Daily Quota | Notes |
|---|---|---|---|---|
| Free | 10 seconds | 100 req | 250,000 | Shared across all apps in portal |
| Starter | 10 seconds | 100 req | 250,000 | Same as Free |
| Professional | 10 seconds | 100 req (private app) / 150 req (OAuth) | 500,000 | OAuth apps get higher burst |
| Enterprise | 10 seconds | 100 req (private app) / 150 req (OAuth) | 500,000 | Same burst as Professional unless Ops Hub added |
| Operations Hub Enterprise | 10 seconds | 1,000 req (100 req/s sustained) | 500,000 | 10x burst; sustained 100 req/s rate |
| API add-on (legacy) | 10 seconds | 100 req | 1,000,000 | Effectively doubled daily quota; burst unchanged |

**Auth token endpoint:** separate limit of **10 requests per 10 seconds** applied to `POST /oauth/v1/token`. This limit applies independently of the API call limits above.

**Detect actual tier from response headers:**

```bash
curl -sI "https://api.hubapi.com/crm/v3/objects/contacts?limit=1" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i "X-HubSpot-RateLimit-Max"
# 100  → Free/Starter or Professional/Enterprise private app
# 150  → Professional/Enterprise OAuth app
# 1000 → Operations Hub Enterprise (10s window = 100 req/s sustained)
```

## Batch API Endpoints

Batch endpoints accept up to **100 inputs per request** and consume **1 quota unit** regardless of how many records are returned. A single-record GET call (`/crm/v3/objects/contacts/{id}`) also costs 1 quota unit. The efficiency ratio is 1:100.

### Contacts

| Operation | Method | Endpoint | Max batch size | Notes |
|---|---|---|---|---|
| Read | `POST` | `/crm/v3/objects/contacts/batch/read` | 100 | Accepts `{id}` or `{idProperty, value}` inputs |
| Create | `POST` | `/crm/v3/objects/contacts/batch/create` | 100 | Each input is a `{properties: {}}` object |
| Update | `POST` | `/crm/v3/objects/contacts/batch/update` | 100 | Each input is `{id, properties: {}}` |
| Upsert | `POST` | `/crm/v3/objects/contacts/batch/upsert` | 100 | Match on `idProperty`; creates if not found |
| Archive | `POST` | `/crm/v3/objects/contacts/batch/archive` | 100 | Soft-deletes; `{inputs: [{id}]}` |

### Companies, Deals, Tickets, Products, Line Items

Same URL pattern: replace `contacts` with the object type name. All support `batch/read`, `batch/create`, `batch/update`, `batch/upsert`, `batch/archive`.

| Object type | Base path |
|---|---|
| `companies` | `/crm/v3/objects/companies/batch/...` |
| `deals` | `/crm/v3/objects/deals/batch/...` |
| `tickets` | `/crm/v3/objects/tickets/batch/...` |
| `products` | `/crm/v3/objects/products/batch/...` |
| `line_items` | `/crm/v3/objects/line_items/batch/...` |
| Custom objects | `/crm/v3/objects/{objectTypeId}/batch/...` |

### Batch read request shape

```json
{
  "inputs": [
    { "id": "12345" },
    { "id": "67890" }
  ],
  "properties": ["email", "firstname", "lastname", "hs_lead_status"],
  "propertiesWithHistory": [],
  "idProperty": "hs_object_id"
}
```

`idProperty` is optional. Defaults to `hs_object_id`. Set to `email` or a custom unique identifier property to look up by alternate keys.

### Batch read response shape (200 OK)

```json
{
  "status": "COMPLETE",
  "results": [
    {
      "id": "12345",
      "properties": {
        "email": "alice@example.com",
        "firstname": "Alice",
        "lastname": "Example",
        "hs_lead_status": "OPEN"
      },
      "createdAt": "2024-01-15T10:00:00.000Z",
      "updatedAt": "2024-06-01T14:22:33.000Z",
      "archived": false
    }
  ],
  "errors": [],
  "startedAt": "2024-06-01T14:22:34.000Z",
  "completedAt": "2024-06-01T14:22:34.123Z"
}
```

**Partial failure:** if some IDs in the batch are not found or fail validation, `results` contains the successes and `errors` contains the failures. The overall HTTP status is still `200` for partial success. Always check `errors` array — a 200 response does not guarantee all records were returned.

### Batch create request shape

```json
{
  "inputs": [
    {
      "properties": {
        "email": "bob@example.com",
        "firstname": "Bob",
        "lastname": "Builder"
      }
    }
  ]
}
```

### Batch update request shape

```json
{
  "inputs": [
    {
      "id": "12345",
      "properties": {
        "hs_lead_status": "IN_PROGRESS"
      }
    }
  ]
}
```

### Batch upsert request shape

```json
{
  "inputs": [
    {
      "idProperty": "email",
      "id": "carol@example.com",
      "properties": {
        "firstname": "Carol",
        "hs_lead_status": "OPEN"
      }
    }
  ]
}
```

## 429 Response Shape

```
HTTP/2 429
Retry-After: 10
Content-Type: application/json
X-HubSpot-RateLimit-Daily: 500000
X-HubSpot-RateLimit-Daily-Remaining: 487200
X-HubSpot-RateLimit-Interval-Milliseconds: 10000
X-HubSpot-RateLimit-Max: 100
X-HubSpot-RateLimit-Remaining: 0
```

```json
{
  "status": "error",
  "message": "You have reached your secondly limit.",
  "errorType": "RATE_LIMIT",
  "correlationId": "b5c3f2a1-d4e6-7890-ab12-cd34ef567890",
  "policyName": "SECONDLY",
  "requestId": "b5c3f2a1"
}
```

**`policyName` values:**

| policyName | Meaning | Recovery |
|---|---|---|
| `SECONDLY` | Per-10s burst window exhausted | Wait `Retry-After` seconds (typically 1–30) |
| `DAILY` | 500K/day portal quota exhausted | Wait until midnight UTC; reduce call volume |
| `TEN_SECONDLY` | Alternate spelling of burst limit | Same as `SECONDLY` |

**When `Retry-After` is absent on a 429:** fall back to exponential backoff with full jitter (`Math.random() * min(cap, base * 2^attempt)`). The header is present on burst-limit 429s; it may be absent if HubSpot returns a 429 for other reasons (e.g., concurrent connection limits in some plans).

## Non-Batch API Cost Reference

For estimating quota requirements before implementing a feature:

| Operation | Endpoint | Cost (quota units) |
|---|---|---|
| Get one contact by ID | `GET /crm/v3/objects/contacts/{id}` | 1 |
| Get one contact + associations | `GET /crm/v3/objects/contacts/{id}?associations=deals` | 1 (associations are free in the same call) |
| Search contacts | `POST /crm/v3/objects/contacts/search` | 1 per page |
| Get contact properties | `GET /crm/v3/properties/contacts` | 1 |
| Get 100 contacts (batch read) | `POST /crm/v3/objects/contacts/batch/read` | 1 |
| Create one contact | `POST /crm/v3/objects/contacts` | 1 |
| Create 100 contacts (batch) | `POST /crm/v3/objects/contacts/batch/create` | 1 |
| List all contacts paginated | `GET /crm/v3/objects/contacts?limit=100` per page | 1 per page |
| Get deals for a contact | `GET /crm/v3/associations/contacts/deals/batch/read` | 1 |
| Timeline event | `POST /crm/v3/timeline/events` | 1 per event |
| OAuth token refresh | `POST /oauth/v1/token` | 1 (separate 10 req/10s limit) |

**Quota estimate formula for a contact sync:**

```
calls = ceil(total_contacts / 100)          # using batch read
days_of_quota = 500_000 / calls
```

A 5,000,000 contact sync using batch/read = 50,000 calls. That is 10% of the 500K daily quota. Without batch APIs it would be 5,000,000 calls — 10x the available quota.

## Associations Batch API

Associations (contact ↔ deal, company ↔ contact, etc.) have their own batch endpoints and count against the same quota:

```
POST /crm/v3/associations/{fromObjectType}/{toObjectType}/batch/read
POST /crm/v3/associations/{fromObjectType}/{toObjectType}/batch/create
POST /crm/v3/associations/{fromObjectType}/{toObjectType}/batch/archive
```

Max batch size: 100 inputs. Each call costs 1 quota unit and returns associations for all included IDs.
