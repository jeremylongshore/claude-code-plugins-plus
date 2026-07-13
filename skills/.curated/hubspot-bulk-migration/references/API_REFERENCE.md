# HubSpot Bulk Migration — API Reference

Endpoint catalog, request/response shapes, field validation rules, and rate limit reference for bulk CRM migration. Operational patterns (field mapping, association pipeline, rollback) live in `implementation-guide.md`. This document is the static reference.

## Required Scopes

| Scope | Required for |
|---|---|
| `crm.objects.contacts.write` | Create, upsert, archive contacts |
| `crm.objects.companies.write` | Create, archive companies |
| `crm.objects.deals.write` | Create, archive deals |
| `crm.associations.write` | Create associations between objects |
| `crm.schemas.contacts.write` | Create custom properties on contacts |
| `crm.schemas.companies.write` | Create custom properties on companies |
| `crm.schemas.deals.write` | Create custom properties on deals |

## Batch Create — Contacts / Companies / Deals

```
POST https://api.hubapi.com/crm/v3/objects/{objectType}/batch/create
Authorization: Bearer {token}
Content-Type: application/json
```

`objectType`: `contacts`, `companies`, `deals`, `tickets`, `line_items`

### Request shape

```json
{
  "inputs": [
    {
      "properties": {
        "email": "alice@example.com",
        "firstname": "Alice",
        "lastname": "Smith",
        "phone": "+15555550100",
        "salesforce_id": "003XXXXXXXXXXXXXXXXX"
      }
    }
  ]
}
```

- Maximum **100 inputs per request**.
- All properties must be valid HubSpot property names. Unknown property names cause a `400 INVALID_PROPERTY_NAME` for that record.
- Date values must be epoch milliseconds (integer) or `YYYY-MM-DD` string. `M/D/Y` causes `INVALID_DATE`.

### Response shape (200 OK)

```json
{
  "status": "COMPLETE",
  "results": [
    {
      "id": "12345",
      "properties": {
        "email": "alice@example.com",
        "hs_object_id": "12345",
        "createdate": "2024-01-15T00:00:00.000Z"
      },
      "createdAt": "2024-01-15T00:00:00.000Z",
      "updatedAt": "2024-01-15T00:00:00.000Z",
      "archived": false
    }
  ],
  "startedAt": "2024-01-15T00:00:00.000Z",
  "completedAt": "2024-01-15T00:00:00.100Z"
}
```

### Partial failure (207 Multi-Status)

When some records succeed and others fail, HubSpot returns `207` with per-record status:

```json
{
  "status": "COMPLETE",
  "results": [...],
  "errors": [
    {
      "status": "error",
      "category": "VALIDATION_ERROR",
      "message": "Property 'bad_field' does not exist",
      "context": {
        "propertyName": ["bad_field"]
      },
      "subCategory": "INVALID_PROPERTY_NAME"
    }
  ]
}
```

Always check both `results` and `errors` arrays in batch responses. Records in `errors` were not created.

---

## Batch Upsert — Contacts (dedup by property)

```
POST https://api.hubapi.com/crm/v3/objects/contacts/batch/upsert
Authorization: Bearer {token}
Content-Type: application/json
```

Use upsert instead of create for contacts when email is the dedup key. Records with matching email values are updated; non-matching records are created. Only available for `contacts` at v3.

### Request shape

```json
{
  "inputs": [
    {
      "idProperty": "email",
      "id": "alice@example.com",
      "properties": {
        "email": "alice@example.com",
        "firstname": "Alice",
        "lastname": "Smith",
        "salesforce_id": "003XXXXXXXXXXXXXXXXX"
      }
    }
  ]
}
```

- `idProperty`: the HubSpot property to match on — must be a unique property (email is built-in; custom unique properties are also valid).
- `id`: the value of that property for this record.
- Maximum **100 inputs per request**.
- If `id` is empty or null, HubSpot creates a new record without dedup.

### Dedup behavior

| Scenario | Result |
|---|---|
| Email matches existing contact | Updates existing record's properties |
| Email not found | Creates new contact |
| `id` field empty / null | Always creates new contact (no dedup) |
| Email in wrong case | Case-insensitive match — `ALICE@EXAMPLE.COM` matches `alice@example.com` |
| Email malformed | `400 INVALID_EMAIL_ADDRESS` — entire batch rejected |

---

## Batch Archive (rollback cleanup)

```
POST https://api.hubapi.com/crm/v3/objects/{objectType}/batch/archive
Authorization: Bearer {token}
Content-Type: application/json
```

Soft-deletes records. Archived records are excluded from UI and API list calls but are recoverable from trash for 90 days. No bulk-delete endpoint exists in HubSpot — archive is the only programmatic cleanup path.

### Request shape

```json
{
  "inputs": [
    { "id": "12345" },
    { "id": "67890" }
  ]
}
```

- Maximum **100 inputs per request**.
- Response: `204 No Content` on success.
- Rate limit: counted against the same 100/10s burst and 500K daily quota.

---

## CSV Import API

For volumes above 10K records per object type, the CSV import API uses HubSpot's internal import pipeline rather than burning API quota call-by-call.

### Start import

```
POST https://api.hubapi.com/crm/v3/imports
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

#### Form fields

| Field | Type | Description |
|---|---|---|
| `files` | file | The CSV file |
| `importRequest` | JSON string | Import configuration (see below) |

#### importRequest shape

```json
{
  "name": "salesforce-contacts-2024-01",
  "files": [
    {
      "fileName": "contacts.csv",
      "fileFormat": "CSV",
      "fileImportPage": {
        "hasHeader": true,
        "columnMappings": [
          {
            "columnName": "Email",
            "propertyName": "email",
            "columnObjectType": "CONTACT"
          },
          {
            "columnName": "First Name",
            "propertyName": "firstname",
            "columnObjectType": "CONTACT"
          },
          {
            "columnName": "Salesforce ID",
            "propertyName": "salesforce_id",
            "columnObjectType": "CONTACT"
          }
        ]
      }
    }
  ]
}
```

#### columnObjectType values

`CONTACT`, `COMPANY`, `DEAL`, `TICKET`, `PRODUCT`, `LINE_ITEM`

#### Response (201 Created)

```json
{
  "id": "9876543",
  "state": "STARTED",
  "optionValues": { "dateFormat": "YEAR_MONTH_DAY" },
  "metadata": {
    "objectType": "CONTACTS",
    "estimatedNumberOfObjects": 5000
  }
}
```

### Poll import status

```
GET https://api.hubapi.com/crm/v3/imports/{importId}
Authorization: Bearer {token}
```

#### State values

| State | Meaning |
|---|---|
| `STARTED` | Import queued |
| `PROCESSING` | Records being created |
| `DONE` | All records processed |
| `FAILED` | Import failed; see `metadata.counters` |
| `CANCELED` | User or API canceled the import |

#### Response (DONE)

```json
{
  "id": "9876543",
  "state": "DONE",
  "metadata": {
    "objectType": "CONTACTS",
    "counters": {
      "TOTAL_ROWS": 5000,
      "CREATED_OBJECTS": 4987,
      "UPDATED_OBJECTS": 10,
      "INVALID_ROWS": 3
    }
  }
}
```

Poll every 30 seconds. `INVALID_ROWS` are rows that failed validation silently — download the import errors file from the HubSpot UI (Contacts → Import → the import name → Download errors) to see which rows failed and why.

---

## Associations v4 API — Batch Create

```
POST https://api.hubapi.com/crm/v4/associations/{fromObjectType}/{toObjectType}/batch/create
Authorization: Bearer {token}
Content-Type: application/json
```

`fromObjectType` / `toObjectType`: `contacts`, `companies`, `deals`, `tickets`

### Request shape

```json
{
  "inputs": [
    {
      "from": { "id": "12345" },
      "to": { "id": "67890" },
      "types": [
        {
          "associationCategory": "HUBSPOT_DEFINED",
          "associationTypeId": 1
        }
      ]
    }
  ]
}
```

- Maximum **100 inputs per request**.
- `id` values are HubSpot internal IDs (from batch create response or upsert response), not source CRM IDs.

### Standard association type IDs (HUBSPOT_DEFINED)

| associationTypeId | Relationship |
|---|---|
| `1` | Contact → Company (primary) |
| `2` | Company → Contact |
| `3` | Deal → Contact |
| `4` | Contact → Deal |
| `5` | Deal → Company (primary) |
| `6` | Company → Deal |
| `279` | Deal → Line Item |
| `280` | Line Item → Deal |

Full catalog: `GET /crm/v4/associations/definitions` (returns all valid type IDs for a portal).

### Response (200 OK)

```json
{
  "completedAt": "2024-01-15T00:00:01.000Z",
  "results": [
    {
      "from": { "id": "12345" },
      "to": [
        {
          "toObjectId": 67890,
          "associationTypes": [
            { "category": "HUBSPOT_DEFINED", "typeId": 1, "label": null }
          ]
        }
      ]
    }
  ]
}
```

---

## Properties API — Schema Validation

### List all properties for an object type

```
GET https://api.hubapi.com/crm/v3/properties/{objectType}
Authorization: Bearer {token}
```

Returns all standard and custom properties with type, fieldType, and allowed options. Use this response to validate source data before import.

#### Property type reference

| HubSpot `type` | HubSpot `fieldType` | Valid values |
|---|---|---|
| `string` | `text`, `textarea` | Any string |
| `number` | `number` | Numeric string (no commas) |
| `date` | `date` | Epoch milliseconds (integer) or `YYYY-MM-DD` |
| `datetime` | `date` | Epoch milliseconds (integer) |
| `enumeration` | `select`, `radio`, `checkbox` | Must be in `options[].value` |
| `bool` | `booleancheckbox` | `"true"` or `"false"` |
| `phone_number` | `phonenumber` | E.164 recommended; `+15555550100` |

#### Date format rules (critical)

| Format | Accepted? | Notes |
|---|---|---|
| `1705276800000` | Yes | Epoch milliseconds (UTC midnight) |
| `2024-01-15` | Yes | ISO 8601 date string |
| `2024-01-15T00:00:00.000Z` | No | ISO 8601 datetime — HubSpot rejects for `date` type |
| `01/15/2024` | No | M/D/Y — silently dropped or 400 |
| `15-01-2024` | No | D-M-Y — rejected |
| `January 15, 2024` | No | Text date — rejected |

#### Enumeration validation

```
GET https://api.hubapi.com/crm/v3/properties/{objectType}/{propertyName}
```

Response includes `options` array with valid `value` strings. Source picklist values not in this list are silently dropped on import — they do not produce a 400 error.

### Create custom property

```
POST https://api.hubapi.com/crm/v3/properties/{objectType}
Authorization: Bearer {token}
Content-Type: application/json
```

```json
{
  "name": "salesforce_id",
  "label": "Salesforce ID",
  "type": "string",
  "fieldType": "text",
  "groupName": "contactinformation",
  "description": "Original Salesforce record ID. Do not modify."
}
```

- `name` must be lowercase with underscores; no spaces or special characters.
- `groupName` must match an existing property group. Default groups: `contactinformation`, `companyinformation`, `dealinformation`.
- `409 CONFLICT` means property already exists — treat as success (idempotent).

---

## Cursor-Based Export (paginate out of HubSpot)

```
GET https://api.hubapi.com/crm/v3/objects/{objectType}
  ?limit=100
  &properties=email,firstname,lastname,salesforce_id
  &after={cursor}
Authorization: Bearer {token}
```

- `limit`: 1–100. 100 is the maximum per request.
- `after`: cursor value from `paging.next.after` in the previous response. Omit for first page.
- `properties`: comma-separated list of property names to include in response.

### Response (200 OK)

```json
{
  "results": [
    {
      "id": "12345",
      "properties": {
        "email": "alice@example.com",
        "firstname": "Alice",
        "salesforce_id": "003XXXXXXXXXXXXXXXXX",
        "createdate": "2024-01-15T00:00:00.000Z"
      }
    }
  ],
  "paging": {
    "next": {
      "after": "NTI1Cg%3D%3D",
      "link": "https://api.hubapi.com/crm/v3/objects/contacts?after=NTI1Cg%3D%3D&limit=100"
    }
  }
}
```

When `paging.next` is absent, you have retrieved all records.

---

## Rate Limit Headers

HubSpot returns these headers on every response. Monitor them throughout a migration run.

| Header | Meaning |
|---|---|
| `X-HubSpot-RateLimit-Daily` | Total daily quota (500K for Professional/Enterprise) |
| `X-HubSpot-RateLimit-Daily-Remaining` | Remaining calls today |
| `X-HubSpot-RateLimit-Interval-Milliseconds` | Rolling window (10,000ms) |
| `X-HubSpot-RateLimit-Max` | Max calls in window (100 for most tiers) |
| `X-HubSpot-RateLimit-Remaining` | Remaining in current window |
| `Retry-After` | Seconds to wait before retrying (on 429) |

### Daily quota consumption estimate for 100K contacts

| Operation | Calls | Daily quota consumed |
|---|---|---|
| Property schema validation | 3 (contacts, companies, deals) | 0.001% |
| Create 100K contacts (100/batch) | 1,000 | 0.2% |
| Create 50K companies (100/batch) | 500 | 0.1% |
| Create 80K deals (100/batch) | 800 | 0.16% |
| Re-link 100K contact→company assocs | 1,000 | 0.2% |
| Re-link 80K deal→contact assocs | 800 | 0.16% |
| Export all contacts for verification | 1,000 | 0.2% |
| **Total** | **~5,100** | **~1%** |

A full 100K-record migration comfortably fits within the 500K daily quota via the batch API. The risk is retries on 429s or 500s inflating call counts. The CSV import API does not consume API quota for the import itself — only the status polling calls count.
