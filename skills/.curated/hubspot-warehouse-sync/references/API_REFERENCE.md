# HubSpot Warehouse Sync — API Reference

Endpoint catalog, request/response shapes, cursor pagination contracts, CDC field semantics, rate-limit headers, and association batch format for data warehouse extraction. Operational patterns (token bucket, backfill loop, upsert strategies) live in `SKILL.md` and `implementation-guide.md`; this document is the static reference.

---

## Contacts Search API

### Endpoint

```
POST https://api.hubapi.com/crm/v3/objects/contacts/search
Content-Type: application/json
Authorization: Bearer {token}
```

### Request shape

```json
{
  "limit": 100,
  "after": "cursor_string_from_previous_paging_next",
  "properties": ["email", "firstname", "lastname", "hs_lastmodifieddate", "lifecyclestage"],
  "filterGroups": [
    {
      "filters": [
        {
          "propertyName": "hs_lastmodifieddate",
          "operator": "GT",
          "value": "1700000000000"
        }
      ]
    }
  ],
  "sorts": [
    {
      "propertyName": "hs_lastmodifieddate",
      "direction": "ASCENDING"
    }
  ]
}
```

**Key constraints:**

- `limit`: max 100 per page
- Maximum 10,000 records returned per search query (across all pages). For tables > 10K records, slice by `hs_lastmodifieddate` range (e.g., 30-day windows)
- `after` cursor is opaque and valid for approximately 7 days. Stale cursors return `400 INVALID_OFFSET`
- Filter values for timestamp properties must be Unix milliseconds as a **string**, not an integer
- Up to 3 `filterGroups` supported; filters within a group are AND-combined; groups are OR-combined

### Response shape

```json
{
  "total": 54231,
  "results": [
    {
      "id": "123",
      "properties": {
        "email": "alice@example.com",
        "firstname": "Alice",
        "lastname": "Smith",
        "hs_lastmodifieddate": "2024-11-15T18:23:00.000Z",
        "lifecyclestage": "customer",
        "hs_createdate": "2023-06-01T10:00:00.000Z"
      },
      "createdAt": "2023-06-01T10:00:00.000Z",
      "updatedAt": "2024-11-15T18:23:00.000Z",
      "archived": false
    }
  ],
  "paging": {
    "next": {
      "after": "NTY3ODk",
      "link": "https://api.hubapi.com/crm/v3/objects/contacts/search?after=NTY3ODk"
    }
  }
}
```

**Pagination contract:**

- If `paging.next` is absent, this is the final page
- The `after` value in `paging.next` is a base64-encoded offset — treat as opaque
- Do not attempt to construct or modify cursor values
- Requesting beyond the 10,000-record limit returns an empty `results` array (not an error)

### Operator reference

| Operator | Meaning | Timestamp use |
|---|---|---|
| `EQ` | Equals | exact ms match |
| `NEQ` | Not equals | — |
| `LT` | Less than | before this ms |
| `GT` | Greater than | after this ms (standard CDC filter) |
| `GTE` | Greater than or equal | — |
| `LTE` | Less than or equal | window ceiling |
| `BETWEEN` | Between two values | range slice for >10K backfill |
| `HAS_PROPERTY` | Property exists and is not null | — |

---

## Contacts Batch Read API

Use this to fetch full property payloads for a known list of contact IDs — more efficient than individual GETs when you already have the ID list from a search or webhook delivery.

### Endpoint

```
POST https://api.hubapi.com/crm/v3/objects/contacts/batch/read
Content-Type: application/json
Authorization: Bearer {token}
```

### Request shape

```json
{
  "properties": ["email", "firstname", "lastname", "hs_lastmodifieddate"],
  "propertiesWithHistory": [],
  "inputs": [
    {"id": "123"},
    {"id": "456"},
    {"id": "789"}
  ]
}
```

**Constraints:**

- Max 100 IDs per request
- `propertiesWithHistory` returns all historical values for those properties — can make payloads very large; use sparingly or not at all for warehouse loads

### Response shape

```json
{
  "status": "COMPLETE",
  "results": [
    {
      "id": "123",
      "properties": {
        "email": "alice@example.com",
        "hs_lastmodifieddate": "2024-11-15T18:23:00.000Z"
      },
      "createdAt": "2023-06-01T10:00:00.000Z",
      "updatedAt": "2024-11-15T18:23:00.000Z",
      "archived": false
    }
  ],
  "startedAt": "2024-11-15T18:23:01.000Z",
  "completedAt": "2024-11-15T18:23:01.050Z"
}
```

**Error shape (partial success):** If some IDs are not found, HubSpot returns `status: "COMPLETE"` with only the found records. Missing records are silently dropped, not included in an error array. Always reconcile returned ID count against input ID count.

---

## Contacts Scroll / List API (full table scan alternative)

For simple full-table scans without filter criteria, the list endpoint is more efficient than search because it does not require the search index.

```
GET https://api.hubapi.com/crm/v3/objects/contacts
  ?limit=100
  &after={cursor}
  &properties=email,firstname,lastname,hs_lastmodifieddate
  &archived=false
Authorization: Bearer {token}
```

**When to prefer this over search:**

- Initial full backfill with no date filter (avoids 10K search limit)
- No filter criteria needed

**When to use search instead:**

- Incremental CDC (requires `hs_lastmodifieddate GT` filter)
- Any filter or sort other than default object order

---

## Properties Enumeration API (schema sync)

### Endpoint

```
GET https://api.hubapi.com/crm/v3/properties/contacts
Authorization: Bearer {token}
```

Available for any object type: substitute `contacts` with `companies`, `deals`, `tickets`, `line_items`, or any custom object's API name.

### Response shape

```json
{
  "results": [
    {
      "name": "email",
      "label": "Email",
      "type": "string",
      "fieldType": "text",
      "description": "Contact's email address",
      "groupName": "contactinformation",
      "options": [],
      "displayOrder": -1,
      "calculated": false,
      "externalOptions": false,
      "hasUniqueValue": true,
      "hidden": false,
      "hubspotDefined": true,
      "showCurrencySymbol": false,
      "formField": true,
      "createdAt": "2020-01-01T00:00:00.000Z",
      "updatedAt": "2020-01-01T00:00:00.000Z",
      "archived": false
    },
    {
      "name": "custom_tier",
      "label": "Customer Tier",
      "type": "enumeration",
      "fieldType": "select",
      "options": [
        {"label": "Gold", "value": "gold", "displayOrder": 0},
        {"label": "Silver", "value": "silver", "displayOrder": 1}
      ],
      "hubspotDefined": false
    }
  ]
}
```

### HubSpot → warehouse type mapping

| HubSpot `type` | Recommended warehouse type | Notes |
|---|---|---|
| `string` | `TEXT` / `VARCHAR` | — |
| `number` | `FLOAT64` / `FLOAT` / `NUMERIC(18,4)` | Use NUMERIC for monetary fields |
| `date` | `DATE` | HubSpot `date` properties store midnight UTC in ms |
| `datetime` | `TIMESTAMP WITH TIME ZONE` / `TIMESTAMPTZ` | Parse as UTC explicitly |
| `bool` | `BOOLEAN` | HubSpot returns `"true"` / `"false"` as strings; coerce on load |
| `enumeration` | `TEXT` | Store the machine value (e.g., `"gold"`), not the label |
| `phone_number` | `TEXT` | Include country code prefix; do not cast to numeric |
| `json` | `TEXT` / `JSON` / `JSONB` | Use `JSONB` in Postgres for query access; TEXT in BigQuery |

---

## Association Batch Read API (v4)

### Endpoint

```
POST https://api.hubapi.com/crm/v4/associations/{fromObjectType}/{toObjectType}/batch/read
Content-Type: application/json
Authorization: Bearer {token}
```

Valid `fromObjectType` / `toObjectType` values: `contacts`, `companies`, `deals`, `tickets`, `line_items`, and custom object API names.

### Request shape

```json
{
  "inputs": [
    {"id": "123"},
    {"id": "456"}
  ]
}
```

**Constraints:**

- Max 100 IDs per request (not 1,000 — the v4 batch limit is 100)
- One call per `fromObjectType`/`toObjectType` pair; you cannot batch contacts→deals and contacts→companies in one call

### Response shape

```json
{
  "status": "COMPLETE",
  "results": [
    {
      "from": {"id": "123"},
      "to": [
        {
          "toObjectId": 987,
          "associationTypes": [
            {
              "category": "HUBSPOT_DEFINED",
              "typeId": 4,
              "label": null
            }
          ]
        }
      ]
    },
    {
      "from": {"id": "456"},
      "to": []
    }
  ]
}
```

**Important:** contacts with no associations for the requested type are included in `results` with an empty `to` array. They are not absent from the response. This makes it safe to use the result for computing deleted associations: any `toObjectId` in the warehouse that is not in the current `to` array has been deleted.

### Association type IDs (HubSpot-defined)

| typeId | Meaning |
|---|---|
| 1 | Contact → Company (primary company) |
| 2 | Company → Contact |
| 3 | Company → Deal |
| 4 | Contact → Deal |
| 5 | Deal → Contact |
| 6 | Deal → Company |
| 279 | Company → Ticket |
| 280 | Ticket → Company |

Custom association labels have category `USER_DEFINED` and typeId assigned at creation time.

---

## CDC Fields

### `hs_lastmodifieddate`

- **Type:** `datetime` (Unix milliseconds, UTC)
- **Updated when:** any property on the record is created or changed
- **Not updated when:** an association is added or removed; the record is archived; a task or note is added to the contact's timeline
- **Use for:** incremental property CDC poll
- **Format in API response:** ISO 8601 string `"2024-11-15T18:23:00.000Z"` in the `properties` dict; Unix ms string in filter values

### `hs_createdate`

- **Type:** `datetime` (Unix milliseconds, UTC)
- **Immutable after creation** — safe to use as a partition key in warehouse tables
- **Use for:** initial backfill range slicing (slide a 30-day window from earliest `hs_createdate` to now)

### `createdate` vs `hs_createdate`

HubSpot exposes two creation timestamp properties with overlapping semantics:

- `hs_createdate` — the canonical system creation time; use this
- `createdate` — legacy alias; same value on most records but can diverge on migrated data

Always request `hs_createdate` explicitly; do not assume `createdAt` in the response envelope matches any stored property.

### Timestamps in association objects

Association records do not carry a creation timestamp in the batch read response. There is no `created_at` field on an association. The only way to detect association changes is to compare the current batch read result against the warehouse snapshot.

---

## Rate Limit Headers

HubSpot returns these on every successful response and on 429 responses:

| Header | Value |
|---|---|
| `X-HubSpot-RateLimit-Daily` | Declared daily quota for the account tier |
| `X-HubSpot-RateLimit-Daily-Remaining` | Calls remaining today (resets at midnight UTC) |
| `X-HubSpot-RateLimit-Interval-Milliseconds` | Rolling window size in milliseconds (10,000 = 10s) |
| `X-HubSpot-RateLimit-Max` | Max calls allowed in the rolling window |
| `X-HubSpot-RateLimit-Remaining` | Calls remaining in the current window |
| `Retry-After` | Seconds to wait before retrying (present on 429 responses only) |

### Rate limits by account tier

| Tier | Calls per 10s window | Daily limit |
|---|---|---|
| Free | 100 | 250,000 |
| Starter | 100 | 250,000 |
| Professional | 150 | 500,000 |
| Enterprise | 150 | 500,000 |
| Private app OAuth | 100 per portal | varies |

**Backfill math:** 2M contacts at 100 records/call = 20,000 search calls. At 100 calls/10s, that is 2,000 seconds of pure extraction time (33 minutes). At 150 calls/10s it is 1,333 seconds (22 minutes). Either way you burn the entire daily quota of a Professional or Enterprise account before any other integration makes a single call. Set `daily_budget` well below the account limit (400K for a 500K account) to leave headroom.

---

## Scrolling the Full Contacts Table (search API range-slice pattern)

When the contact count exceeds 10,000, the search API's built-in 10K limit requires a range-slice strategy. Slice on `hs_createdate` using overlapping 30-day windows:

```
Window 1: hs_createdate GTE 0          AND hs_createdate LT  {30d_ms}
Window 2: hs_createdate GTE {30d_ms}   AND hs_createdate LT  {60d_ms}
...continue until now
```

Use a 1-minute overlap on each window boundary (`GTE window_start - 60_000`) to avoid missing records created within the same millisecond as a boundary. The upsert key (`id`) in the warehouse load handles the resulting duplicates safely.

```bash
# Compute 30-day window boundaries in Unix ms
python3 -c "
import datetime
start = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
now   = datetime.datetime.now(tz=datetime.timezone.utc)
delta = datetime.timedelta(days=30)
t = start
while t < now:
    ms_from = int(t.timestamp() * 1000)
    ms_to   = int((t + delta).timestamp() * 1000)
    print(ms_from, ms_to)
    t += delta
"
```

---

## Archived Records

By default, search and list endpoints exclude archived (soft-deleted) contacts. To include them:

```json
{
  "filterGroups": [],
  "archived": true
}
```

Or on the list endpoint: `?archived=true`.

Archived contacts still have a valid `id` and all properties. They are flagged by `"archived": true` in the response envelope. The warehouse schema should include an `archived` boolean column and a `archived_at` timestamp (set from `archivedAt` in the response envelope) so analysts can filter them without a JOIN.
