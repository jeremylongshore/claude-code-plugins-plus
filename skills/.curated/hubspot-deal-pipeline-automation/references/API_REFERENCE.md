# HubSpot Deal Pipeline Automation — API Reference

Endpoint catalog, request/response shapes, deal property reference, search filter syntax, and association types for deal pipeline automation. Operational patterns (loop guard, stale-close logic, quota cache-busting) live in `SKILL.md` and `implementation-guide.md`; this document is the static API reference.

## Authentication

All endpoints require:

```
Authorization: Bearer {private_app_token_or_oauth_access_token}
Content-Type: application/json   (for POST/PATCH)
```

Base URL: `https://api.hubapi.com`

---

## Pipeline Endpoints

### List all deal pipelines

```
GET /crm/v3/pipelines/deals
```

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `includeInactive` | boolean | Include archived pipelines (default `false`) |

**Response (200):**

```json
{
  "results": [
    {
      "id": "12345678",
      "label": "Sales Pipeline",
      "displayOrder": 0,
      "createdAt": "2023-01-15T10:00:00.000Z",
      "updatedAt": "2024-03-20T14:22:00.000Z",
      "archived": false,
      "stages": [
        {
          "id": "appointmentscheduled",
          "label": "Appointment Scheduled",
          "displayOrder": 0,
          "metadata": {
            "isClosed": "false",
            "probability": "0.2"
          },
          "createdAt": "2023-01-15T10:00:00.000Z",
          "updatedAt": "2024-03-20T14:22:00.000Z",
          "archived": false
        },
        {
          "id": "closedwon",
          "label": "Closed Won",
          "displayOrder": 5,
          "metadata": {
            "isClosed": "true",
            "probability": "1.0"
          },
          "createdAt": "2023-01-15T10:00:00.000Z",
          "updatedAt": "2024-03-20T14:22:00.000Z",
          "archived": false
        }
      ]
    }
  ]
}
```

**Key fields:**

| Field | Type | Notes |
|---|---|---|
| `id` | string | Pipeline ID — use in `pipeline` filter on deal search |
| `stages[].id` | string | Stage ID — use in `dealstage` property on deals |
| `stages[].metadata.probability` | string (0–1) | Stage close probability — same value as `hs_deal_stage_probability` |
| `stages[].metadata.isClosed` | string `"true"/"false"` | Whether this stage is terminal |

### Get stages for a specific pipeline

```
GET /crm/v3/pipelines/deals/{pipelineId}/stages
```

Returns `results` array of stage objects — same shape as `stages[]` in the pipeline list response. Use when you only need stage IDs for a known pipeline.

---

## Deal CRUD Endpoints

### Get a single deal

```
GET /crm/v3/objects/deals/{dealId}
```

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `properties` | string (comma-separated) | Property names to return |
| `associations` | string (comma-separated) | Association types to include (e.g., `contacts,companies`) |
| `archived` | boolean | Return archived (deleted) deal (default `false`) |

**Minimal deal response (200):**

```json
{
  "id": "12345678",
  "properties": {
    "createdate": "2024-01-10T08:30:00.000Z",
    "dealname": "Acme Corp — Enterprise License",
    "dealstage": "contractsent",
    "pipeline": "87654321",
    "hs_lastmodifieddate": "2024-03-15T11:00:00.000Z",
    "hs_is_closed": "false",
    "hs_object_id": "12345678",
    "amount": "48000",
    "hs_projected_amount": "38400",
    "hs_deal_stage_probability": "0.80",
    "closedate": "2024-03-31T00:00:00.000Z",
    "hubspot_owner_id": "99887766"
  },
  "createdAt": "2024-01-10T08:30:00.000Z",
  "updatedAt": "2024-03-15T11:00:00.000Z",
  "archived": false
}
```

### Create a deal

```
POST /crm/v3/objects/deals
```

**Minimum viable request body:**

```json
{
  "properties": {
    "dealname": "Acme Corp — Q2 Expansion",
    "dealstage": "appointmentscheduled",
    "pipeline": "12345678",
    "amount": "24000",
    "closedate": "2024-06-30"
  }
}
```

### Update a deal

```
PATCH /crm/v3/objects/deals/{dealId}
```

**Request body:**

```json
{
  "properties": {
    "dealstage": "closedwon",
    "amount": "48000",
    "closedate": "2024-03-28"
  }
}
```

Returns the updated deal object. Only include properties you are changing — omitting a property does not clear it.

### Batch update deals

```
POST /crm/v3/objects/deals/batch/update
```

Collapses up to 100 individual PATCH calls into one request. Use instead of looping `PATCH` when updating multiple deals — reduces rate-limit pressure by a factor of up to 100.

**Request body:**

```json
{
  "inputs": [
    {
      "id": "11111111",
      "properties": { "dealstage": "closedlost", "hs_closed_lost_reason": "No budget" }
    },
    {
      "id": "22222222",
      "properties": { "dealstage": "closedlost", "hs_closed_lost_reason": "No budget" }
    }
  ]
}
```

**Response (200 — all succeeded) or 207 (partial success):**

```json
{
  "status": "COMPLETE",
  "results": [
    { "id": "11111111", "properties": { "dealstage": "closedlost" }, "updatedAt": "..." }
  ],
  "startedAt": "2024-03-28T09:00:00.000Z",
  "completedAt": "2024-03-28T09:00:00.100Z",
  "errors": []
}
```

On `207 MULTI_STATUS`, `errors[]` contains per-object failures — always check this array even on success responses.

---

## CRM Search

```
POST /crm/v3/objects/deals/search
```

### Request body shape

```json
{
  "filterGroups": [
    {
      "filters": [
        {
          "propertyName": "string",
          "operator": "EQ | NEQ | LT | LTE | GT | GTE | BETWEEN | IN | NOT_IN | HAS_PROPERTY | NOT_HAS_PROPERTY | CONTAINS_TOKEN | NOT_CONTAINS_TOKEN",
          "value": "string",
          "values": ["string"]
        }
      ]
    }
  ],
  "sorts": [
    {
      "propertyName": "string",
      "direction": "ASCENDING | DESCENDING"
    }
  ],
  "query": "optional full-text search string",
  "properties": ["dealname", "amount", "dealstage"],
  "limit": 100,
  "after": "cursor_from_paging.next.after"
}
```

### Filter operator reference

| Operator | Applies to | Notes |
|---|---|---|
| `EQ` | string, number, enum, boolean | Exact match. Boolean: use string `"true"` or `"false"` |
| `NEQ` | string, number, enum | Not equal |
| `LT` / `LTE` | number, date (epoch ms) | Less than / less than or equal |
| `GT` / `GTE` | number, date (epoch ms) | Greater than / greater than or equal |
| `BETWEEN` | number, date | Use `value` for lower bound, `highValue` for upper bound |
| `IN` | string, enum | Match any of `values[]` array |
| `NOT_IN` | string, enum | Match none of `values[]` array |
| `HAS_PROPERTY` | any | Property is set (not null/empty) |
| `NOT_HAS_PROPERTY` | any | Property is null or empty |
| `CONTAINS_TOKEN` | string | Substring match |

**Multiple filters in one `filterGroup` are AND-joined. Multiple `filterGroups` in the array are OR-joined.**

### Date filter pattern (epoch milliseconds)

```json
{
  "propertyName": "createdate",
  "operator": "LT",
  "value": "1704067200000"
}
```

Convert a date to epoch ms in Python:

```python
import datetime
dt = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
epoch_ms = int(dt.timestamp() * 1000)  # → 1704067200000
```

### Pagination

Search results are paginated at `limit` (max 200). The `paging.next.after` cursor from the response body is an opaque string — pass it verbatim to the next request's `after` field. When `paging.next` is absent, you have reached the last page.

**Maximum result set:** 10,000 records per search query. For full-corpus exports beyond 10K, use the Exports API (`POST /crm/v3/exports`) instead.

---

## Deal Properties Reference

### Standard deal properties (HubSpot-defined)

| Property Name | Type | Description |
|---|---|---|
| `dealname` | string | Deal display name |
| `dealstage` | enumeration | Stage ID (from pipeline stages) |
| `pipeline` | enumeration | Pipeline ID |
| `amount` | number | Rep-entered deal value — canonical for quota |
| `hs_projected_amount` | number | `amount × hs_deal_stage_probability` — use for weighted pipeline |
| `hs_deal_stage_probability` | number | Current stage probability (0–1); changes when stage changes |
| `closedate` | date | Expected close date (ISO 8601 or epoch ms) |
| `hs_is_closed` | boolean (string) | `"true"` if stage `isClosed` is true |
| `hs_is_closed_won` | boolean (string) | `"true"` for Closed Won stage only |
| `createdate` | datetime | When the deal was created (auto-set, read-only) |
| `hs_lastmodifieddate` | datetime | Last property change timestamp (auto-set, read-only) |
| `hubspot_owner_id` | enumeration | HubSpot user ID of the deal owner |
| `hs_object_id` | string | Deal ID (same as `id` in response) |
| `hs_closed_lost_reason` | string | Free-text or picklist reason for Closed Lost |
| `num_associated_contacts` | number | Count of associated contacts (read-only rollup) |

### Forecast-specific properties

| Property Name | Use | Warning |
|---|---|---|
| `amount` | Quota credit, CRM pipeline value | Only correct source for quota; reps enter this |
| `hs_projected_amount` | Probability-weighted forecast | Computed by HubSpot at stage change time — can drift if `amount` is updated without a stage change |
| `hs_deal_stage_probability` | Multiplier for weighted pipeline | Reflects the stage's static probability, not rep conviction |
| `hs_arr_amount` | ARR field (Sales Hub Enterprise) | Only present on Enterprise portals with ARR tracking enabled |
| `hs_mrr_amount` | MRR field (Sales Hub Enterprise) | Same — not on Starter/Professional |

**Forecast reconciliation rule:** if `abs(hs_projected_amount - (amount × hs_deal_stage_probability)) / amount > 0.05`, `hs_projected_amount` is stale. Force a recalculation by patching `dealstage` to the same current stage — HubSpot recomputes on any stage write.

### Enumerate custom deal properties

```bash
curl -s "https://api.hubapi.com/crm/v3/properties/deals" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" | \
  jq '[.results[] | select(.hubspotDefined == false) | {name, label, type, fieldType, groupName, archived}]'
```

Properties with `"archived": true` are soft-deleted — they no longer appear on deal records but their historical values remain. A dashboard filter on an archived property returns zero results with no error.

---

## Associations API v4

### Link a deal to another object

```
PUT /crm/v4/objects/deals/{dealId}/associations/{toObjectType}/{toObjectId}/{associationType}
```

| Segment | Value |
|---|---|
| `toObjectType` | `contacts`, `companies`, `tickets`, `deals`, `line_items` |
| `associationType` | numeric or label (see table below) |

**Common deal association types:**

| From | To | Type ID | Label |
|---|---|---|---|
| `deals` | `contacts` | `3` | deal to contact |
| `deals` | `companies` | `5` | deal to company |
| `deals` | `deals` | `5` | deal to deal (cross-reference for duplicates) |
| `deals` | `tickets` | `16` | deal to ticket |
| `deals` | `line_items` | `19` | deal to line item |

**Create a deal-to-deal cross-reference link:**

```bash
curl -s -X PUT \
  "https://api.hubapi.com/crm/v4/objects/deals/${DEAL_A}/associations/deals/${DEAL_B}/5" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" | \
  jq '{fromObjectId, toObjectId, associationTypes}'
```

### List associations for a deal

```
GET /crm/v3/objects/deals/{dealId}/associations/{toObjectType}
```

Returns `results[]` with `{id, type}` objects. Use `id` to fetch the associated object.

---

## Rate Limit Reference

| Tier | Burst | Daily |
|---|---|---|
| Starter | 100 req/10s | 250,000 |
| Professional | 150 req/10s | 500,000 |
| Enterprise | 150 req/10s | 500,000 |

**Search is rate-limited separately:** `POST /search` endpoints share the same burst quota but search calls are heavier — HubSpot recommends no more than 4 concurrent search requests.

**Batch endpoints are not free:** each object in a batch read/update counts as one API call against the rate limit. A batch update with 100 deals consumes 100 of your burst quota, the same as 100 individual PATCHes. The benefit is latency (one round trip) not quota savings.

**Rate limit response headers:**

| Header | Meaning |
|---|---|
| `X-HubSpot-RateLimit-Daily-Remaining` | Calls left today |
| `X-HubSpot-RateLimit-Remaining` | Calls left in current 10s window |
| `Retry-After` | Seconds to wait on 429 |
