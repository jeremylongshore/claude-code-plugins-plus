# HubSpot Lifecycle and Lists — API Reference

## Lifecycle Stage Enumeration

### Internal enum values (use these in API calls)

| Internal Value | Display Label (default) | Linear Order | Notes |
|---|---|---|---|
| `subscriber` | Subscriber | 1 | Default for new opt-in contacts |
| `lead` | Lead | 2 | |
| `marketingqualifiedlead` | Marketing Qualified Lead | 3 | Abbreviated MQL in UI |
| `salesqualifiedlead` | Sales Qualified Lead | 4 | Abbreviated SQL in UI |
| `opportunity` | Opportunity | 5 | Deal-associated contacts |
| `customer` | Customer | 6 | At least one closed-won deal |
| `evangelist` | Evangelist | 7 | Champions and referrers |
| `other` | Other | lateral | Not part of the linear sequence; can be set at any time |

**Critical:** display labels are portal-configurable. A portal admin can rename "Marketing Qualified Lead" to "Hot Lead." The internal enum values shown above are immutable — always use these in API calls, never display labels.

**How HubSpot handles backward writes:** the `PATCH /crm/v3/objects/contacts/{id}` endpoint accepts any valid internal enum value and applies it regardless of direction. There is no built-in regression guard. The API returns `200 OK` whether the write advances or regresses the stage. The progression guard in `implementation-guide.md` must be applied at the application layer.

### Read the stage enumeration from the API

```bash
curl -s \
  "https://api.hubapi.com/crm/v3/properties/contacts/lifecyclestage" \
  -H "Authorization: Bearer {your-token}" \
  | jq '.options[] | {label, value, displayOrder}'
```

The response includes portal-customized labels. Compare `.value` (immutable) to `.label` (configurable) to build a safe mapping.

---

## Contacts API v3 — Lifecycle Stage Operations

### Read a contact's lifecycle stage

```
GET https://api.hubapi.com/crm/v3/objects/contacts/{contactId}?properties=lifecyclestage
```

**Query parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `properties` | string (comma-separated) | No | Property names to return. Omit for default set. |
| `associations` | string | No | Association types to include |
| `archived` | boolean | No | Include archived contacts. Default: false |

**Response (200):**

```json
{
  "id": "12345",
  "properties": {
    "lifecyclestage": "salesqualifiedlead",
    "hs_object_id": "12345",
    "createdate": "2025-01-15T10:30:00.000Z",
    "lastmodifieddate": "2026-03-22T14:00:00.000Z"
  },
  "createdAt": "2025-01-15T10:30:00.000Z",
  "updatedAt": "2026-03-22T14:00:00.000Z",
  "archived": false
}
```

### Update lifecycle stage (single contact)

```
PATCH https://api.hubapi.com/crm/v3/objects/contacts/{contactId}
Content-Type: application/json
Authorization: Bearer {your-token}
```

**Request body:**

```json
{
  "properties": {
    "lifecyclestage": "customer"
  }
}
```

**Response (200):** same shape as the GET response, with updated property values.

**Error (400) — invalid enum value:**

```json
{
  "status": "error",
  "message": "Property lifecyclestage value unknown_value not found",
  "error": "PROPERTY_VALUE_NOT_FOUND",
  "correlationId": "abc123"
}
```

### Batch update lifecycle stage

```
POST https://api.hubapi.com/crm/v3/objects/contacts/batch/update
Content-Type: application/json
Authorization: Bearer {your-token}
```

**Request body (max 100 inputs per request):**

```json
{
  "inputs": [
    {"id": "12345", "properties": {"lifecyclestage": "customer"}},
    {"id": "67890", "properties": {"lifecyclestage": "opportunity"}}
  ]
}
```

**Response (200):**

```json
{
  "completedAt": "2026-05-11T12:00:00.000Z",
  "results": [
    {"id": "12345", "properties": {"lifecyclestage": "customer"}, ...},
    {"id": "67890", "properties": {"lifecyclestage": "opportunity"}, ...}
  ],
  "status": "COMPLETE"
}
```

**Partial failure (207):** When some inputs fail, the response is `207 Multi-Status`. Check `results` for individual errors.

### Search contacts by lifecycle stage

```
POST https://api.hubapi.com/crm/v3/objects/contacts/search
Content-Type: application/json
Authorization: Bearer {your-token}
```

**Request body:**

```json
{
  "filterGroups": [
    {
      "filters": [
        {
          "propertyName": "lifecyclestage",
          "operator": "EQ",
          "value": "customer"
        }
      ]
    }
  ],
  "properties": ["email", "lifecyclestage", "hs_lead_status", "hubspotscore"],
  "limit": 100,
  "after": "0"
}
```

**Filter operators for lifecyclestage:**

| Operator | Meaning |
|---|---|
| `EQ` | Exact match |
| `NEQ` | Not equal |
| `IN` | Value is in a list (pass `values` array, not `value` scalar) |
| `NOT_IN` | Value is not in a list |
| `HAS_PROPERTY` | Property exists (not empty) |
| `NOT_HAS_PROPERTY` | Property is empty |

**Example — contacts who are MQL or SQL:**

```json
{
  "filterGroups": [
    {
      "filters": [
        {
          "propertyName": "lifecyclestage",
          "operator": "IN",
          "values": ["marketingqualifiedlead", "salesqualifiedlead"]
        }
      ]
    }
  ]
}
```

**Pagination:** the search response includes `paging.next.after` — pass this as the `after` parameter in subsequent requests. Returns a maximum of 10,000 results total. For full portal exports, use the Contacts v1 `getAll` endpoint or CRM exports.

---

## Lists API v1 — Endpoints

**Note on versioning:** As of 2026, HubSpot's v3 CRM API does not yet support list read/write operations. The canonical list management surface remains the v1 Contacts Lists API. Monitor [developers.hubspot.com/changelog](https://developers.hubspot.com/changelog) for v3 list support announcements.

### Get a single list

```
GET https://api.hubapi.com/contacts/v1/lists/{listId}
Authorization: Bearer {your-token}
```

**Response (200):**

```json
{
  "listId": 42,
  "name": "2026-Q2 Campaign Segment",
  "listType": "STATIC",
  "dynamic": false,
  "createdAt": 1714000000000,
  "updatedAt": 1746000000000,
  "metaData": {
    "size": 1847,
    "processing": "DONE",
    "lastProcessingStateChangeAt": 1746000000000
  },
  "filters": []
}
```

**`listType` values:** `STATIC` (membership controlled via API) or `DYNAMIC` (membership controlled by filter criteria).

**`metaData.processing` values:**

| Value | Meaning |
|---|---|
| `DONE` | Membership is stable and current |
| `REFRESHING` | Background re-evaluation in progress (after criteria edit) |
| `INITIALIZING` | Newly created list, first evaluation not yet complete |
| `RE_QUEUED_ENABLED` | Scheduled for re-evaluation |

Poll `metaData.processing` until `DONE` before treating membership as authoritative after a criteria change.

### Get all lists

```
GET https://api.hubapi.com/contacts/v1/lists/all/lists/static?count=250&offset=0
GET https://api.hubapi.com/contacts/v1/lists/all/lists/dynamic?count=250&offset=0
Authorization: Bearer {your-token}
```

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `count` | integer | 20 | Lists per page (max 250) |
| `offset` | integer | 0 | Pagination offset |

**Response (200):**

```json
{
  "lists": [...],
  "has-more": true,
  "offset": 250
}
```

### Create a list

```
POST https://api.hubapi.com/contacts/v1/lists
Content-Type: application/json
Authorization: Bearer {your-token}
```

**Static list body:**

```json
{
  "name": "Campaign — Suppression List",
  "dynamic": false
}
```

**Dynamic list body (example: all customers):**

```json
{
  "name": "All Customers — Auto",
  "dynamic": true,
  "filters": [
    [
      {
        "filterFamily": "ContactProperty",
        "withinTimeMode": "PAST",
        "checkPastVersions": false,
        "type": "string",
        "property": "lifecyclestage",
        "operation": "SET_ANY",
        "value": "customer"
      }
    ]
  ]
}
```

**Response (200):**

```json
{
  "listId": 112,
  "name": "Campaign — Suppression List",
  "listType": "STATIC",
  "dynamic": false,
  "createdAt": 1746000000000,
  "updatedAt": 1746000000000,
  "metaData": {"size": 0, "processing": "DONE"}
}
```

### Get all contacts in a list

```
GET https://api.hubapi.com/contacts/v1/lists/{listId}/contacts/all
Authorization: Bearer {your-token}
```

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `count` | integer | 20 | Contacts per page (max 100) |
| `vidOffset` | integer | — | Pagination cursor (VID from previous response) |
| `property` | string | (default set) | Request specific properties (repeatable) |

**Response (200):**

```json
{
  "contacts": [
    {
      "vid": 12345,
      "canonical-vid": 12345,
      "properties": {
        "lifecyclestage": {"value": "customer"},
        "email": {"value": "contact@example.com", "versions": [{"value": "contact@example.com"}]}
      }
    }
  ],
  "has-more": true,
  "vid-offset": 12345
}
```

**Note:** the `properties` shape here is the v1 format — each property is an object with a `.value` key and a `.versions` array. This differs from the v3 format where properties are flat key-value pairs.

### Add contacts to a static list

```
POST https://api.hubapi.com/contacts/v1/lists/{listId}/add
Content-Type: application/json
Authorization: Bearer {your-token}
```

**Request body (max 500 vids per request; HubSpot recommends batches of 100):**

```json
{
  "vids": [12345, 67890, 11223]
}
```

**Response (200):**

```json
{
  "updated": [12345, 67890],
  "discarded": [11223]
}
```

`discarded` contains VIDs that were already in the list (not an error — idempotent). `updated` contains VIDs that were newly added.

**Error (400):** If the list is `DYNAMIC`, the add operation is rejected — dynamic list membership is controlled exclusively by filter criteria.

### Remove contacts from a static list

```
POST https://api.hubapi.com/contacts/v1/lists/{listId}/remove
Content-Type: application/json
Authorization: Bearer {your-token}
```

**Request body:**

```json
{
  "vids": [12345, 67890]
}
```

**Response (200):**

```json
{
  "updated": [12345],
  "discarded": [67890]
}
```

`discarded` contains VIDs that were not in the list.

### Delete a list

```
DELETE https://api.hubapi.com/contacts/v1/lists/{listId}
Authorization: Bearer {your-token}
```

**Response (204):** no body. List IDs are not reused after deletion. Any automation referencing the deleted list ID must be updated immediately or it will silently match nothing.

---

## Dynamic List Filter Syntax

Dynamic lists use a nested filter structure: an outer array of filter groups (OR logic between groups) containing an inner array of individual filters (AND logic within a group).

```
filters = [
  [ filter_A AND filter_B ],   ← group 1
  OR
  [ filter_C ]                 ← group 2
]
```

### Filter shape

```json
{
  "filterFamily": "ContactProperty",
  "type": "string",
  "property": "lifecyclestage",
  "operation": "SET_ANY",
  "value": "customer"
}
```

**filterFamily values:**

| Value | Filters on |
|---|---|
| `ContactProperty` | Any contact property |
| `ListMembership` | Membership in another list |
| `PageView` | Specific URL page views |
| `FormSubmission` | Form submission activity |
| `EmailEvent` | Email open/click/bounce |

**operation values for string properties:**

| Operation | Meaning |
|---|---|
| `SET_ANY` | Property equals the value |
| `NOT_IN` | Property does not equal the value |
| `IS_ANY` | Property exists |
| `IS_NOT_ANY` | Property does not exist or is empty |
| `BEGINS_WITH_ANY` | String starts with value |
| `ENDS_WITH_ANY` | String ends with value |
| `CONTAINS` | String contains value |

**Dynamic list filter example — MQL contacts created in the last 30 days:**

```json
{
  "name": "MQL — Last 30 Days",
  "dynamic": true,
  "filters": [
    [
      {
        "filterFamily": "ContactProperty",
        "type": "string",
        "property": "lifecyclestage",
        "operation": "SET_ANY",
        "value": "marketingqualifiedlead"
      },
      {
        "filterFamily": "ContactProperty",
        "type": "datetime",
        "property": "createdate",
        "operation": "EQ",
        "value": "30d",
        "withinTimeMode": "PAST"
      }
    ]
  ]
}
```

---

## Webhook Event Shapes

### contact.propertyChange — lifecyclestage

Fired when a contact's `lifecyclestage` property is updated. Delivered to your registered webhook URL as an HTTP POST.

**Delivery format:** HubSpot batches events and may deliver multiple events in a single POST body (JSON array).

```json
[
  {
    "eventId": 1746000000001,
    "subscriptionId": 99001,
    "portalId": 1234567,
    "appId": 456789,
    "occurredAt": 1746000000000,
    "subscriptionType": "contact.propertyChange",
    "attemptNumber": 0,
    "objectId": 12345,
    "propertyName": "lifecyclestage",
    "propertyValue": "customer",
    "changeSource": "CRM_UI",
    "changeFlag": "UPDATED"
  }
]
```

**Key fields:**

| Field | Type | Description |
|---|---|---|
| `eventId` | integer | Unique per event — use as idempotency key |
| `subscriptionId` | integer | Which webhook subscription fired |
| `portalId` | integer | HubSpot portal (hub) ID |
| `occurredAt` | epoch ms | When the property was changed |
| `attemptNumber` | integer | Always `0` — HubSpot does not retry on failure |
| `objectId` | integer | Contact VID that changed |
| `propertyName` | string | `lifecyclestage` |
| `propertyValue` | string | New property value (the internal enum value, not the display label) |
| `changeSource` | string | `CRM_UI`, `IMPORT`, `API`, `AUTOMATION_PLATFORM`, etc. |

**`changeFlag` values:**

| Value | Meaning |
|---|---|
| `UPDATED` | Property was changed (most common) |
| `CREATED` | Property was set for the first time |
| `DELETED` | Property was cleared |

### contact.creation

Fired when a new contact is created.

```json
[
  {
    "eventId": 1746000000002,
    "subscriptionType": "contact.creation",
    "objectId": 99999,
    "portalId": 1234567,
    "occurredAt": 1746000000000,
    "attemptNumber": 0
  }
]
```

### contact.deletion

Fired when a contact is deleted. After this event, any static list membership referencing `objectId` is orphaned.

```json
[
  {
    "eventId": 1746000000003,
    "subscriptionType": "contact.deletion",
    "objectId": 12345,
    "portalId": 1234567,
    "occurredAt": 1746000000000,
    "attemptNumber": 0
  }
]
```

Subscribe to `contact.deletion` to trigger immediate orphan removal from static lists rather than relying on the weekly sweep.

---

## Webhook Signature Validation

HubSpot signs webhook payloads with your app's client secret. Always validate before processing.

**Signature v3 (recommended):**

HubSpot computes:

```
HMAC-SHA256(clientSecret, method + uri + requestBody + timestamp)
```

Headers:

- `X-HubSpot-Signature-v3`: hex digest
- `X-HubSpot-Request-Timestamp`: Unix ms timestamp of delivery

Reject if the timestamp is more than 5 minutes old (replay protection).

```python
import hmac, hashlib, time

def verify_v3_signature(
    client_secret: str,
    method: str,
    uri: str,
    body: bytes,
    signature_header: str,
    timestamp_header: str,
) -> bool:
    ts_ms = int(timestamp_header)
    if abs(time.time() * 1000 - ts_ms) > 300_000:
        return False  # replay window exceeded
    source = f"{method}{uri}{body.decode('utf-8')}{timestamp_header}"
    computed = hmac.new(client_secret.encode(), source.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header, computed)
```

---

## Rate Limits

| Limit | Value | Scope |
|---|---|---|
| API calls per 10 seconds | 100 | Per private app |
| Daily API calls | 500,000 | Per portal |
| Search requests per minute | 4 | Per portal |
| Batch size (contacts update) | 100 | Per request |
| Batch size (list add/remove) | 500 (recommended: 100) | Per request |
| Webhook subscriptions per app | 25 | Per public app |

The `Retry-After` response header contains the number of seconds to wait before retrying after a `429`. For search endpoints, `X-HubSpot-RateLimit-Remaining` and `X-HubSpot-RateLimit-Reset` are present in the response headers.

---

## Required OAuth Scopes

| Scope | Required for |
|---|---|
| `crm.objects.contacts.read` | Reading contact properties and lifecycle stage |
| `crm.objects.contacts.write` | Updating lifecycle stage via PATCH |
| `crm.lists.read` | Reading list metadata and membership |
| `crm.lists.write` | Creating lists, adding/removing members |
| `crm.schemas.contacts.read` | Reading property definitions (lifecycle stage enum) |

Private app tokens inherit the scopes selected during app creation. OAuth tokens inherit scopes from the authorization scope list.
