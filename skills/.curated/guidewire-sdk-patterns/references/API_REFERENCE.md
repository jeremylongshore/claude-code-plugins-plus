# Guidewire Cloud API — SDK Reference

Endpoint shapes, request/response patterns, and edge-case behaviors that informed the patterns in `SKILL.md`. Operational layer code lives in the SKILL; this is the static reference.

## Cloud API request envelope

Every mutation (POST/PATCH/PUT) wraps the payload in a `data.attributes` object. PATCH and PUT additionally carry `data.checksum`.

```json
POST /pc/rest/v1/accounts
Content-Type: application/json
Authorization: Bearer [token]
Idempotency-Key: 5f9d6f8e-7c3a-4b2e-9c1d-1e2f3a4b5c6d

{
  "data": {
    "attributes": {
      "accountHolderContact": { "displayName": "ACME Corp" },
      "primaryLanguage": { "code": "en_US" },
      "primaryLocation": { "addressLine1": "1 Market St", "city": "San Francisco", "state": { "code": "CA" } }
    }
  }
}
```

## Response envelope

All Cloud API responses use this shape; sibling skills depend on it:

```json
{
  "count": 1,
  "data": [
    {
      "attributes": { "...": "..." },
      "checksum": "abc123",
      "links": { "self": { "href": "/pc/rest/v1/accounts/pc:8001" } }
    }
  ],
  "links": { "next": { "href": "/pc/rest/v1/accounts?pageSize=100&offsetToken=..." } }
}
```

`checksum` is opaque; treat it as a string and pass it back unchanged. `links.next` may be absent (terminator) or present with a query string already containing `offsetToken` — do not parse it, just GET it.

## Error response shape

```json
{
  "userMessage": "Account number must be unique",
  "errors": [
    {
      "type": "rule-violation",
      "message": "An account with number A000001 already exists",
      "attributes": { "field": "accountNumber", "violatedRule": "AccountNumberUniqueness" }
    }
  ]
}
```

Common `errors[].type` values worth pattern-matching:

| Type | When | Treat as |
|---|---|---|
| `invalid-attribute` | field validation (format, range, required) | client error; do not retry; surface to user |
| `rule-violation` | Gosu business rule rejected the payload | client error; surface `userMessage` and `errors[].attributes.violatedRule` |
| `unauthorized` | scope or role missing | not retryable; raise to ops |
| `rate-limited` | quota exhaustion | retry per `Retry-After` header |
| `entity-conflict` | optimistic lock failure | retry the GET-then-mutate cycle, not the bare PATCH |

## Pagination

Cloud API uses opaque `offsetToken` cursor pagination. Page numbers do not exist. Pass `pageSize` (max 100 for most endpoints; check per-endpoint limits in the API ref) and follow `links.next` until absent.

```
GET /pc/rest/v1/accounts?pageSize=100
→ links.next.href = "/pc/rest/v1/accounts?pageSize=100&offsetToken=eyJ...AB"
GET /pc/rest/v1/accounts?pageSize=100&offsetToken=eyJ...AB
→ links.next.href = "/pc/rest/v1/accounts?pageSize=100&offsetToken=eyJ...CD"
GET /pc/rest/v1/accounts?pageSize=100&offsetToken=eyJ...CD
→ (no links.next) — end of stream
```

Do not assume the cursor is a stable identifier you can resume from later — it can expire.

## Idempotency-Key behavior

| Behavior | Detail |
|---|---|
| Header name | `Idempotency-Key` |
| Format | client-generated UUIDv4 (no server validation, but use UUIDs to avoid collisions across services) |
| Window | 24 hours; replays inside the window return the original response (`200`/`201`), not `409` |
| Scope | per-endpoint, per-tenant; the same key on a different endpoint creates a new resource |
| Required vs optional | optional but strongly recommended for any non-GET that can be retried |

A client must generate the key **once per logical operation** and reuse it across HTTP attempts. Generating per attempt defeats deduplication.

## Rate limiting

Per-tenant quotas are configured in GCC; defaults vary by tenant tier. The relevant response signals:

| Signal | Meaning |
|---|---|
| `429 Too Many Requests` | quota exceeded; back off per `Retry-After` |
| `Retry-After: 30` | wait 30 seconds before retry |
| `Retry-After: Wed, 21 Oct 2026 07:28:00 GMT` | wait until that absolute time (HTTP-date format) |
| Sustained 429s after honouring header | another integration shares the tenant quota; coordinate with tenant admin |

There is no published `X-RateLimit-Remaining` header on Cloud API as of `202503` — clients must self-pace via token-bucket if the quota is tight, not rely on a remaining-budget header.

## Included entities (N+1 elimination)

Use the `included` query parameter to inline related entities in one round-trip rather than N+1 follow-ups.

```
GET /pc/rest/v1/policies/pc:8001?included=lines,coverages,producerCodes
```

The response embeds the related entities under `included` keyed by id. Reduces request count and tenant-quota burn for fetch-heavy operations.

## Batch endpoint

For bulk inserts/updates, the `/composite/v1/composite` endpoint accepts an array of operations as a single request. Use for migration backfills and large CSV ingests; do not use for low-latency synchronous workflows (the batch is processed serially server-side).

```http
POST /composite/v1/composite
{
  "requests": [
    { "method": "POST", "uri": "/cc/rest/v1/claims", "body": { "data": { "attributes": { "...": "..." } } } },
    { "method": "POST", "uri": "/cc/rest/v1/claims", "body": { "data": { "attributes": { "...": "..." } } } }
  ]
}
```

Per-sub-request `Idempotency-Key` is supported. Failures in one sub-request do not roll back the others — read each `responses[].status` independently.

## HTTP/2 and connection pooling

Cloud API supports HTTP/2; reuse connections rather than establishing per-request. Most language `fetch` implementations pool by default; under load, monitor connection establishment count to verify pooling is active. For high-rps integrations, the per-connection request multiplexing of HTTP/2 cuts auth-token-side latency by 30–50% versus HTTP/1.1.

## Related references

- `references/implementation-guide.md` — extended walkthrough with worked examples
- Sibling `guidewire-install-auth/references/API_REFERENCE.md` — auth endpoint, JWT structure, status code matrix
- Sibling `guidewire-observability-and-incident-response` — interpreting these signals in production dashboards
