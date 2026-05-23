# HubSpot Product Event Sync — API Reference

Endpoint catalog, request/response shapes, property type enumeration, 207 handling, and the custom event vs custom property decision matrix. Operational patterns (queue, idempotency, DLQ) live in `SKILL.md` and `implementation-guide.md`; this document is the static reference.

## Batch Endpoints

### POST /crm/v3/objects/contacts/batch/update

Update up to 100 contacts by internal HubSpot ID. Requires `crm.objects.contacts.write`.

```
POST https://api.hubapi.com/crm/v3/objects/contacts/batch/update
Authorization: Bearer {token}
Content-Type: application/json
```

**Request body:**

```json
{
  "inputs": [
    {
      "id": "12345",
      "properties": {
        "hs_product_last_active_date": "1715472000000",
        "hs_product_total_sessions": "47"
      }
    },
    {
      "id": "67890",
      "properties": {
        "hs_product_last_active_date": "1715385600000",
        "hs_product_total_sessions": "12"
      }
    }
  ]
}
```

**Notes:**

- `id` is the HubSpot internal numeric contact ID, not email.
- All property values must be strings — even numeric types. HubSpot coerces on ingest.
- Max 100 objects per call. Caller is responsible for chunking.
- Use this endpoint when you already know the HubSpot contact ID. Prefer `batch/upsert` when starting from email.

**Success response (200):**

```json
{
  "status": "COMPLETE",
  "results": [
    {
      "id": "12345",
      "properties": {
        "hs_product_last_active_date": "1715472000000",
        "hs_product_total_sessions": "47",
        "hs_object_id": "12345"
      },
      "createdAt": "2024-01-15T00:00:00.000Z",
      "updatedAt": "2024-05-12T00:00:00.000Z",
      "archived": false
    }
  ],
  "startedAt": "2024-05-12T00:00:00.001Z",
  "completedAt": "2024-05-12T00:00:00.123Z"
}
```

**Partial failure response (207):**

```json
{
  "status": "COMPLETE",
  "results": [
    {
      "id": "12345",
      "properties": { "hs_product_total_sessions": "47" }
    }
  ],
  "errors": [
    {
      "status": "error",
      "category": "OBJECT_NOT_FOUND",
      "message": "No object with ID 67890",
      "context": {
        "id": ["67890"]
      },
      "links": {}
    }
  ],
  "startedAt": "2024-05-12T00:00:00.001Z",
  "completedAt": "2024-05-12T00:00:00.123Z"
}
```

**Critical:** HTTP 207 is returned even when the entire batch partially fails. Your code must inspect `body.errors` on any 2xx response. Never assume 2xx means all records succeeded.

---

### POST /crm/v3/objects/contacts/batch/upsert

Upsert up to 100 contacts by a unique identifier (email is the canonical identifier). Creates the contact if not found; updates if found. Requires `crm.objects.contacts.write`.

```
POST https://api.hubapi.com/crm/v3/objects/contacts/batch/upsert
Authorization: Bearer {token}
Content-Type: application/json
```

**Request body:**

```json
{
  "inputs": [
    {
      "idProperty": "email",
      "id": "alice@acme.com",
      "properties": {
        "hs_product_last_active_date": "1715472000000",
        "hs_product_total_sessions": "47",
        "hs_product_current_plan": "pro"
      }
    },
    {
      "idProperty": "email",
      "id": "bob@newdomain.com",
      "properties": {
        "hs_product_last_active_date": "1715385600000",
        "hs_product_total_sessions": "3"
      }
    }
  ]
}
```

**Notes:**

- `idProperty` can be `email` or any unique custom property defined as a unique identifier on the contact object.
- If the contact does not exist, it is created. If it exists, it is updated.
- This is the correct endpoint when syncing from a product event stream where you know email but not HubSpot ID.
- Max 100 inputs per call.

**Success response (200):** identical structure to `batch/update` 200.

**Partial failure response (207):** identical structure to `batch/update` 207. The `context.id` field will contain the email value (not a numeric ID) for contacts that failed on the upsert path.

---

### POST /crm/v3/properties/contacts

Create a custom property definition. Requires `crm.schemas.contacts.write`.

```
POST https://api.hubapi.com/crm/v3/properties/contacts
Authorization: Bearer {token}
Content-Type: application/json
```

**Request body:**

```json
{
  "name": "hs_product_total_sessions",
  "label": "Total Sessions (Product)",
  "type": "number",
  "fieldType": "number",
  "groupName": "product_signals",
  "description": "Lifetime session count from the product backend",
  "options": []
}
```

**Success response (201):**

```json
{
  "name": "hs_product_total_sessions",
  "label": "Total Sessions (Product)",
  "type": "number",
  "fieldType": "number",
  "groupName": "product_signals",
  "description": "Lifetime session count from the product backend",
  "hubspotDefined": false,
  "hidden": false,
  "options": [],
  "createdAt": "2024-05-12T00:00:00.000Z",
  "updatedAt": "2024-05-12T00:00:00.000Z",
  "archived": false
}
```

**Error: property name already exists (409):**

```json
{
  "status": "error",
  "message": "Property 'hs_product_total_sessions' already exists for objectType 'CONTACT'",
  "error": "PROPERTY_EXISTS",
  "correlationId": "abc-123"
}
```

---

### GET /crm/v3/properties/contacts/{propertyName}

Retrieve a property definition to verify type before writing. Requires `crm.schemas.contacts.read`.

```
GET https://api.hubapi.com/crm/v3/properties/contacts/hs_product_total_sessions
Authorization: Bearer {token}
```

**Response (200):**

```json
{
  "name": "hs_product_total_sessions",
  "label": "Total Sessions (Product)",
  "type": "number",
  "fieldType": "number",
  "groupName": "product_signals",
  "description": "Lifetime session count from the product backend",
  "hubspotDefined": false,
  "options": []
}
```

**Property not found (404):**

```json
{
  "status": "error",
  "message": "Property 'hs_product_total_sessions' not found",
  "error": "PROPERTY_DOESNT_EXIST"
}
```

---

### POST /events/v3/send (Custom Behavioral Events — Enterprise only)

Send a custom behavioral event to the HubSpot timeline. Requires Marketing Hub Enterprise and `crm.objects.contacts.write`. Do not use this endpoint for structured data (counts, timestamps, tier flags) — use custom properties instead.

```
POST https://api.hubapi.com/events/v3/send
Authorization: Bearer {token}
Content-Type: application/json
```

**Request body:**

```json
{
  "eventName": "pe23434470_product_session_started",
  "occurredAt": "2024-05-12T10:00:00.000Z",
  "email": "alice@acme.com",
  "properties": {
    "session_source": "direct",
    "feature_flags": "beta-dashboard"
  }
}
```

**Notes:**

- `eventName` format is `pe{portalId}_{event_slug}` — the portal ID prefix is added when you create the event definition.
- Event definitions must be created in the HubSpot UI or via `POST /events/v3/event-definitions` before events can be sent.
- Properties must match the schema defined for the event.
- This endpoint does not support batch sending — one API call per event. At high throughput, this burns rate budget 100x faster than a batch property update.

---

### POST /crm/v3/timeline/events (Timeline Events)

Attach a timeline event to a CRM record. Available on all tiers (Professional+). Distinct from custom behavioral events — timeline events appear in the activity feed but are not usable in behavioral event reports or list enrollment.

```
POST https://api.hubapi.com/crm/v3/timeline/events
Authorization: Bearer {token}
Content-Type: application/json
```

**Request body:**

```json
{
  "eventTemplateId": "123456",
  "objectType": "CONTACTS",
  "objectId": "12345",
  "tokens": {
    "session_source": "direct",
    "duration_seconds": "342"
  },
  "timestamp": "2024-05-12T10:00:00.000Z",
  "extraData": {
    "raw_payload": "{...}"
  }
}
```

## Property Type Enumeration

| HubSpot type | `fieldType` | Valid values | Notes |
|---|---|---|---|
| `string` | `text`, `textarea`, `phonenumber`, `html` | Any string | Max 65,536 chars. Do not write numbers to this type — they coerce silently and lose numeric semantics |
| `number` | `number` | Numeric string, e.g. `"47"` | All API values are strings; HubSpot stores as float internally |
| `date` | `date` | `"YYYY-MM-DD"` | Midnight UTC on the given date. Do not use Unix timestamps for `date` type |
| `datetime` | `date` | Unix milliseconds as string, e.g. `"1715472000000"` | Use Unix ms for `datetime`; `YYYY-MM-DD` is accepted but loses time precision |
| `bool` | `booleancheckbox` | `"true"` or `"false"` | Always use lowercase string literals |
| `enumeration` | `select`, `radio`, `checkbox` | Internal value matching a defined option | Writing an undefined enum value returns 400 `INVALID_OPTION_VALUE` |

**Type coercion table (what HubSpot does silently on type mismatch):**

| Written | Property type | Stored as | Surface error? |
|---|---|---|---|
| `"47"` | `string` | `"47"` | No — looks correct but loses numeric semantics |
| `47` (number literal) | `string` | `"47"` | No — JavaScript clients stringify automatically |
| `"alice@acme.com"` | `number` | `""` (empty) | No — silently drops non-numeric content |
| `"maybe"` | `bool` | `""` (empty) | No |
| `"platinum"` | `enumeration` | 400 error | Yes — `INVALID_OPTION_VALUE` |

## Custom Event vs Custom Property Decision Matrix

| Question | Custom property | Custom behavioral event |
|---|---|---|
| Do you need to filter contacts in lists by this data? | Yes | No — behavioral events cannot be used in standard list enrollment criteria |
| Do you need the signal in a HubSpot workflow trigger? | Yes — works as an enrollment trigger | Partial — only via behavioral event triggers (Enterprise) |
| Do you need the signal visible on the contact timeline? | No — properties are in the sidebar, not timeline | Yes — designed for timeline rendering |
| Do you need the signal in behavioral event reports? | No | Yes |
| What HubSpot tier do you have? | All (Starter+) | Marketing Hub Enterprise only |
| Is this a "state" (current value) or an "action" (occurred once at a time)? | State | Action |
| Rate limit impact? | 100 records per API call (batch/upsert) | 1 event per API call |

**Decision rule:** if your backend event updates a property that answers "what is this contact's current state?" (plan, session count, last active), use a custom property. If the event answers "what did this contact do, and when?" and you need that visible in the timeline or behavioral attribution reports, use a custom behavioral event — but only if you have Marketing Hub Enterprise. If you are on Starter or Professional, custom behavioral events are not available; use timeline events for timeline visibility and custom properties for queryable state.

## 207 Error Category Reference

| `category` | Meaning | Recovery |
|---|---|---|
| `OBJECT_NOT_FOUND` | Contact ID does not exist (on `batch/update`) | Switch to upsert; verify ID source |
| `INVALID_PROPERTY_VALUE` | Value incompatible with property type | Fix upstream; validate type before write |
| `PROPERTY_DOESNT_EXIST` | Property name does not exist | Run `ensureProperty`; check for typos |
| `INVALID_OPTION_VALUE` | Enumeration value not in defined options | Add option or fix mapping |
| `DUPLICATE_VALUE` | Unique property collision | Deduplicate before write; use upsert |
| `MISSING_REQUIRED_PROPERTY` | Required property not provided | Add required field to payload |
| `ASSOCIATION_LIMIT` | Too many associations on record | Check association count before writing |

## Rate Limit Headers

| Header | Description |
|---|---|
| `X-HubSpot-RateLimit-Daily` | Total daily quota |
| `X-HubSpot-RateLimit-Daily-Remaining` | Remaining today — alert below 10% |
| `X-HubSpot-RateLimit-Interval-Milliseconds` | Rolling window size in ms |
| `X-HubSpot-RateLimit-Max` | Max calls in the rolling window |
| `X-HubSpot-RateLimit-Remaining` | Remaining in current window |
| `Retry-After` | Seconds to wait after a 429; always prefer this over computed backoff |

### Effective throughput by tier

| Tier | Burst | Effective batch throughput | Events/minute at 100/batch |
|---|---|---|---|
| Starter | 100 req/10s | 1,000 records/10s | 60,000 contacts/min |
| Professional | 150 req/10s | 1,500 records/10s | 90,000 contacts/min |
| Enterprise | 150 req/10s | 1,500 records/10s | 90,000 contacts/min |

A well-batched integration on Starter tier can sustain 60,000 contact updates per minute before hitting the burst limit. An unbatched integration (one API call per event) hits the same limit at 100 events/minute — 600x worse throughput.
