# HubSpot Webhook Handlers — API Reference

Endpoint catalog, signature algorithm, event payload shapes, subscription management, and retry behavior spec. Operational patterns (dedup, async ACK, DLQ, ordering) live in `SKILL.md` and `implementation-guide.md`; this document is the static reference.

## Signature Verification Algorithm

HubSpot v3 webhook signatures use HMAC-SHA256. The exact computation:

```
signature = HMAC-SHA256(
  key   = clientSecret,
  input = httpMethod + requestUri + rawRequestBody + requestTimestamp
)
```

### Inputs

| Input | Source | Notes |
|---|---|---|
| `clientSecret` | Settings → App → Client Secret | The app's OAuth client secret — NOT the access token |
| `httpMethod` | HTTP verb, uppercase | Always `POST` for webhook deliveries |
| `requestUri` | Full URL including `https://` scheme, host, path, and query string | Must match exactly what HubSpot sent — include port if non-standard |
| `rawRequestBody` | Raw bytes of the HTTP body | Must be the original bytes; re-serialized JSON will not match |
| `requestTimestamp` | Value of `X-HubSpot-Request-Timestamp` header | Milliseconds since epoch as a string; concatenate without separators |

### Concatenation format

```
{httpMethod}{requestUri}{rawRequestBody}{requestTimestamp}
```

No separators between components. Example with a minimal payload:

```
POST
https://hooks.example.com/webhooks/hubspot
[{"eventId":12345}]
1715430210000
```

Concatenated: `POSThttps://hooks.example.com/webhooks/hubspot[{"eventId":12345}]1715430210000`

### Output

The resulting HMAC-SHA256 digest encoded as a lowercase hex string. This must match the value of `X-HubSpot-Signature-v3` using a constant-time comparison.

### Timestamp tolerance

Reject any request where `|serverTime - requestTimestamp| > 300,000 ms` (5 minutes). This prevents replay attacks where a valid signature is captured and redelivered later.

### Request headers on every webhook delivery

| Header | Value |
|---|---|
| `X-HubSpot-Signature-v3` | HMAC-SHA256 hex digest (lowercase) |
| `X-HubSpot-Request-Timestamp` | Unix timestamp in milliseconds |
| `Content-Type` | `application/json` |

### Common signature mismatch causes

| Cause | Symptom | Fix |
|---|---|---|
| Using `express.json()` instead of `express.raw()` | Mismatch on all requests | Switch to `express.raw()` on webhook route |
| Proxy strips `X-HubSpot-Signature-v3` | Header absent (403) | Configure ALB/nginx/Cloudflare to forward all `X-HubSpot-*` headers |
| Using access token instead of client secret | Mismatch on all requests | `HUBSPOT_CLIENT_SECRET` must be the app secret, not `pat-na1-...` |
| Protocol or port mismatch in URI | Mismatch | Use `req.protocol + '://' + req.get('host') + req.originalUrl` |
| Query string stripped by framework | Mismatch when subscriptions carry query params | Use `req.originalUrl`, not `req.path` |

## Webhook Subscription Endpoint

### Create a subscription

```
POST https://api.hubapi.com/webhooks/v3/{appId}/subscriptions
Authorization: Bearer {accessToken}
Content-Type: application/json
```

Request body:

```json
{
  "eventType": "contact.propertyChange",
  "propertyName": "lifecyclestage",
  "active": true
}
```

`propertyName` is required only for `*.propertyChange` event types; omit for creation, deletion, and merge types.

Response (201 Created):

```json
{
  "id": 1234567,
  "createdAt": "2024-01-15T10:00:00.000Z",
  "updatedAt": "2024-01-15T10:00:00.000Z",
  "active": true,
  "eventType": "contact.propertyChange",
  "propertyName": "lifecyclestage"
}
```

### List subscriptions

```
GET https://api.hubapi.com/webhooks/v3/{appId}/subscriptions
```

Response:

```json
{
  "results": [
    {
      "id": 1234567,
      "active": true,
      "eventType": "contact.propertyChange",
      "propertyName": "lifecyclestage"
    }
  ]
}
```

### Update a subscription

```
PATCH https://api.hubapi.com/webhooks/v3/{appId}/subscriptions/{subscriptionId}
```

Body: `{ "active": false }` to pause delivery without deleting the subscription.

### Delete a subscription

```
DELETE https://api.hubapi.com/webhooks/v3/{appId}/subscriptions/{subscriptionId}
```

### App webhook settings (target URL and max concurrency)

```
PUT https://api.hubapi.com/webhooks/v3/{appId}/settings
```

Request body:

```json
{
  "targetUrl": "https://hooks.example.com/webhooks/hubspot",
  "throttling": {
    "period": "SECONDLY",
    "maxConcurrentRequests": 10
  }
}
```

`maxConcurrentRequests`: 1–100. HubSpot will not exceed this many simultaneous in-flight deliveries to your endpoint.

## Event Types

| Event Type | Trigger | `propertyName` Required |
|---|---|---|
| `contact.creation` | A new contact is created | No |
| `contact.deletion` | A contact is permanently deleted | No |
| `contact.propertyChange` | A contact property is updated | Yes |
| `contact.merge` | Two contact records are merged | No |
| `company.creation` | A new company is created | No |
| `company.deletion` | A company is permanently deleted | No |
| `company.propertyChange` | A company property is updated | Yes |
| `deal.creation` | A new deal is created | No |
| `deal.deletion` | A deal is permanently deleted | No |
| `deal.propertyChange` | A deal property is updated | Yes |

List-membership changes do not have a dedicated event type. Approximate using `contact.propertyChange` on `hs_all_contact_vids` or subscribe to workflow enrollment events.

## Event Object Shape

Each webhook delivery is a JSON array of event objects. Maximum 100 events per delivery.

### Base fields (all event types)

```json
{
  "eventId": 12345678901234,
  "subscriptionId": 1234567,
  "portalId": 987654321,
  "appId": 11111111,
  "occurredAt": 1715430210000,
  "subscriptionType": "contact.propertyChange",
  "attemptNumber": 0,
  "objectId": 551
}
```

| Field | Type | Description |
|---|---|---|
| `eventId` | `number` | Unique event identifier. Use as the dedup key in Redis. |
| `subscriptionId` | `number` | ID of the subscription that triggered delivery |
| `portalId` | `number` | HubSpot portal (account) ID |
| `appId` | `number` | Your app ID |
| `occurredAt` | `number` | Unix timestamp in milliseconds when the change occurred — use for ordering guards |
| `subscriptionType` | `string` | One of the event types listed above |
| `attemptNumber` | `number` | 0 on first delivery; increments on retry |
| `objectId` | `number` | CRM object ID (contact ID, company ID, deal ID, etc.) |

### Additional fields for `contact.propertyChange` / `company.propertyChange` / `deal.propertyChange`

```json
{
  "propertyName": "lifecyclestage",
  "propertyValue": "customer",
  "changeSource": "AUTOMATION_PLATFORM",
  "changeFlag": "UPDATED"
}
```

| Field | Type | Description |
|---|---|---|
| `propertyName` | `string` | The property that changed |
| `propertyValue` | `string` | New value after the change |
| `changeSource` | `string` | What caused the change (see below) |
| `changeFlag` | `string` | `UPDATED`, `CREATED`, or `DELETED` |

### `changeSource` values

| Value | Meaning |
|---|---|
| `CRM_UI` | Changed manually in HubSpot UI |
| `API` | Changed via HubSpot API |
| `IMPORT` | Changed via bulk import |
| `FORM` | Changed via HubSpot form submission |
| `INTEGRATION` | Changed by a connected integration |
| `AUTOMATION_PLATFORM` | Changed by a HubSpot workflow |
| `SALES` | Changed in Sales Hub |
| `EMAIL` | Changed via email interaction |
| `ANALYTICS` | Changed by analytics/tracking |

### Additional fields for `contact.merge`

```json
{
  "mergedObjectIds": [551, 552],
  "primaryObjectId": 551
}
```

### Additional fields for `contact.deletion`

```json
{
  "gdprDeleteType": "HARD_DELETE"
}
```

## Retry Behavior

| Parameter | Value |
|---|---|
| Delivery timeout | 5 seconds — HubSpot closes the connection if no response within 5s |
| Retry trigger | Non-200 response OR connection timeout |
| Retry window | Up to 3 days from first delivery attempt |
| Retry schedule | Exponential backoff (exact intervals not published by HubSpot) |
| `attemptNumber` header | Increments on each retry attempt; visible in event object |
| Max events per delivery | 100 events per HTTP request |
| Replay API | Does not exist — events lost after 3-day retry window expire permanently |

### What triggers a retry

- HTTP response code other than 200 (including 201, 202, 204 — only 200 is ACK)
- TCP connection timeout before response
- Response body never fully sent
- TLS handshake failure

### What does NOT trigger a retry

- 200 response received (even if you immediately crash after sending it)
- Events delivered to an inactive subscription (they are silently dropped)

## Delivery Guarantees

| Guarantee | Value |
|---|---|
| Ordering | Delivery order, NOT chronological. `occurredAt` in the event is the source of truth for ordering. |
| Deduplication | None. At-least-once delivery. Same `eventId` may arrive multiple times. |
| Batching | Events for the same object may be batched with other objects' events in the same delivery. |
| Subscription isolation | Each active subscription delivers independently; a single CRM change may trigger deliveries for multiple subscriptions. |

## Subscription Scopes Required

| Event Type | Required Scope |
|---|---|
| `contact.*` | `crm.objects.contacts.read` |
| `company.*` | `crm.objects.companies.read` |
| `deal.*` | `crm.objects.deals.read` |
| List membership (approximated) | `crm.lists.read` |
| Webhook management API | `webhooks.read`, `webhooks.write` |

## Error Responses from Subscription Management API

| Status | Error | Meaning |
|---|---|---|
| 400 | `INVALID_PROPERTY` | `propertyName` does not exist on the object type |
| 400 | `SUBSCRIPTION_EXISTS` | A subscription for this event type + property already exists |
| 403 | `MISSING_SCOPES` | App lacks the required scope for this event type |
| 404 | `NOT_FOUND` | App ID or subscription ID does not exist |
| 409 | `CONFLICT` | Concurrent subscription creation conflict; retry |
