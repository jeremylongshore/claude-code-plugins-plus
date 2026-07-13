# HubSpot Contact Deduplication — API Reference

Endpoint catalog, request/response shapes, search filter syntax, property uniqueness enforcement, and error codes for contact deduplication. Operational patterns (winner selection, fuzzy matching, rate-limit pipeline) live in `SKILL.md`; this document is the static reference.

---

## Merge Endpoint

```
POST https://api.hubapi.com/crm/v3/objects/contacts/merge
Authorization: Bearer {your-token}
Content-Type: application/json
```

### Request shape

```json
{
  "primaryObjectId": "101",
  "objectIdToMerge": "202"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `primaryObjectId` | string | yes | The contact whose ID survives after merge. Activities, notes, and properties on both records are moved to this contact. |
| `objectIdToMerge` | string | yes | The contact to be absorbed. After a successful merge this record is deleted and returns 404 on future reads. |

Both values must be HubSpot internal numeric IDs (the `hs_object_id` property), not email addresses or external reference IDs.

### Response shape (200 OK)

The response body is the merged contact record in standard CRM object format. The ID matches `primaryObjectId`.

```json
{
  "id": "101",
  "properties": {
    "email": "jane.doe@example.com",
    "firstname": "Jane",
    "lastname": "Doe",
    "createdate": "2023-01-15T09:00:00.000Z",
    "lastmodifieddate": "2024-06-01T14:32:10.000Z",
    "lifecyclestage": "customer",
    "hs_object_id": "101"
  },
  "createdAt": "2023-01-15T09:00:00.000Z",
  "updatedAt": "2024-06-01T14:32:10.000Z",
  "archived": false
}
```

### Property conflict resolution

HubSpot resolves property conflicts between the primary and secondary contact using the **most recently updated value wins** rule, applied per-property. There is no per-property override in the merge request body.

Exceptions that behave differently:

| Property | Merge behavior |
|---|---|
| `hs_email_optout` | Most recently updated wins — verify post-merge and patch if wrong |
| `hs_email_hard_bounce_reason_enum` | Retained from the record where it is set; not overwritten by a null |
| `email` | Primary's email is the canonical email after merge |
| `hs_additional_emails` | All unique emails from both records are combined into this field |
| Associations (deals, companies, tickets) | Re-parented to primary automatically for standard object types |
| Custom object associations | Not guaranteed to transfer; must be audited and re-parented manually |

### Merge error codes

| HTTP | `category` / `message` | Meaning | Resolution |
|---|---|---|---|
| 400 | `CONTACT_ALREADY_MERGED` | Secondary ID no longer exists as a standalone contact | Re-fetch the secondary ID; it may have a `hs_merged_object_ids` property pointing to the surviving primary |
| 400 | `INVALID_OBJECT_TYPE` | One or both IDs belong to a different CRM object type | Verify object type by reading the ID via `/crm/v3/objects/contacts/{id}` — a 404 means it is a different type |
| 400 | `SAME_OBJECT_MERGE` | Both IDs are identical | Remove self-merge pairs from your candidate list |
| 404 | `OBJECT_NOT_FOUND` | One ID was deleted since discovery | Re-fetch before merging; skip if deleted |
| 409 | `MERGE_IN_PROGRESS` | A concurrent merge is already running for this contact | Retry after 30 seconds |
| 429 | — | Burst or daily rate limit exceeded | Honor `Retry-After`; check `X-HubSpot-RateLimit-Daily-Remaining` |
| 500 | `INTERNAL_ERROR` | Transient platform fault | Retry with exponential back-off; log `X-HubSpot-Correlation-Id` header for HubSpot support |

---

## Contact Search Endpoint

```
POST https://api.hubapi.com/crm/v3/objects/contacts/search
Authorization: Bearer {your-token}
Content-Type: application/json
```

### Full request shape

```json
{
  "filterGroups": [
    {
      "filters": [
        {
          "propertyName": "email",
          "operator": "EQ",
          "value": "jane.doe@example.com"
        }
      ]
    }
  ],
  "properties": [
    "email",
    "firstname",
    "lastname",
    "phone",
    "hs_object_id",
    "createdate",
    "lastmodifieddate",
    "lifecyclestage",
    "hs_email_optout",
    "hs_email_hard_bounce_reason_enum",
    "hs_legal_basis"
  ],
  "sorts": [
    {
      "propertyName": "createdate",
      "direction": "ASCENDING"
    }
  ],
  "limit": 100,
  "after": "100"
}
```

### Filter operators

| Operator | Applies to | Description |
|---|---|---|
| `EQ` | string, number, enum | Exact match (case-insensitive for string properties) |
| `NEQ` | string, number, enum | Not equal |
| `CONTAINS_TOKEN` | string | Substring match — used for partial email/name search |
| `NOT_CONTAINS_TOKEN` | string | Inverse substring match |
| `HAS_PROPERTY` | any | Record has a non-null value for this property |
| `NOT_HAS_PROPERTY` | any | Property is null or empty |
| `GT` | number, date | Greater than |
| `GTE` | number, date | Greater than or equal |
| `LT` | number, date | Less than |
| `LTE` | number, date | Less than or equal |
| `IN` | string, enum | Value is one of the provided list (up to 100 values) |
| `NOT_IN` | string, enum | Value is not in the provided list |
| `BETWEEN` | number, date | Value falls between `highValue` and `value` (inclusive) |

### FilterGroup logic

Multiple filters within a single `filterGroup` are ANDed. Multiple `filterGroups` in the array are ORed. This enables both "email = X AND phone = Y" (one group with two filters) and "email = X OR email = Y" (two groups with one filter each).

```json
{
  "filterGroups": [
    {
      "filters": [
        { "propertyName": "email", "operator": "EQ", "value": "jane@example.com" },
        { "propertyName": "lifecyclestage", "operator": "EQ", "value": "customer" }
      ]
    },
    {
      "filters": [
        { "propertyName": "phone", "operator": "EQ", "value": "+15128675309" }
      ]
    }
  ]
}
```

This returns contacts where (email = jane@example.com AND lifecyclestage = customer) OR (phone = +15128675309).

### Search response shape

```json
{
  "total": 3,
  "results": [
    {
      "id": "101",
      "properties": {
        "email": "jane.doe@example.com",
        "firstname": "Jane",
        "lastname": "Doe",
        "createdate": "2023-01-15T09:00:00.000Z",
        "lastmodifieddate": "2024-06-01T14:32:10.000Z",
        "lifecyclestage": "customer",
        "hs_email_optout": "false",
        "hs_object_id": "101"
      },
      "createdAt": "2023-01-15T09:00:00.000Z",
      "updatedAt": "2024-06-01T14:32:10.000Z",
      "archived": false
    }
  ],
  "paging": {
    "next": {
      "after": "100",
      "link": "https://api.hubapi.com/crm/v3/objects/contacts/search?after=100"
    }
  }
}
```

Pagination uses cursor-based `after` values, not page numbers. The `paging.next` block is absent when there are no more results. Maximum `limit` per call is `200`; however the search API caps results at `10,000` contacts per query across all pages. For full-portal scans, use multiple bounded queries (date range, lifecycle stage slices) or the batch read approach.

### Search limitations relevant to dedup

- Maximum of 3 filter groups per request
- Maximum of 3 filters per filter group
- Results capped at 10,000 per query (use pagination + bounded date ranges to scan full catalog)
- Search index is not real-time; newly created contacts may not appear for up to 1 minute
- `CONTAINS_TOKEN` operator does not support fuzzy/approximate matching — normalization must be applied in your code before searching

---

## Batch Read Endpoint

```
POST https://api.hubapi.com/crm/v3/objects/contacts/batch/read
Authorization: Bearer {your-token}
Content-Type: application/json
```

Use this to pre-fetch all candidate properties for a set of known IDs before running winner selection and compliance checks. More efficient than individual GET calls.

### Request shape

```json
{
  "inputs": [
    { "id": "101" },
    { "id": "202" },
    { "id": "303" }
  ],
  "properties": [
    "email",
    "phone",
    "firstname",
    "lastname",
    "createdate",
    "lastmodifieddate",
    "lifecyclestage",
    "hs_email_optout",
    "hs_email_optout_date",
    "hs_email_hard_bounce_reason_enum",
    "hs_legal_basis",
    "hs_additional_emails"
  ]
}
```

| Field | Limit |
|---|---|
| `inputs` array length | 100 IDs per call |
| `properties` array length | No hard limit; very large sets affect response size |

### Response shape (207 Multi-Status)

```json
{
  "status": "COMPLETE",
  "results": [
    {
      "id": "101",
      "properties": { "email": "jane.doe@example.com", "createdate": "...", ... },
      "createdAt": "...",
      "updatedAt": "...",
      "archived": false
    },
    {
      "id": "202",
      "properties": { ... },
      ...
    }
  ],
  "errors": []
}
```

When one ID in the batch does not exist, it appears in the `errors` array with category `OBJECT_NOT_FOUND` — the rest of the batch still returns successfully. Always check `errors` before assuming all IDs resolved.

---

## Email Uniqueness Enforcement

HubSpot enforces email uniqueness at the property level using the `email` property and the `hs_additional_emails` multi-value property. The enforcement rules:

- Creating a contact with an email address that already exists on another contact: HubSpot returns `409 CONFLICT` with `CONTACT_EXISTS` and includes the existing contact ID in the response body.
- Updating a contact's email to a value already owned by another contact: same `409 CONFLICT` behavior.
- After a merge, both contacts' email addresses appear in `hs_additional_emails` on the surviving primary. The primary's original `email` property is preserved as the canonical email.

**The uniqueness check is on the raw email string, not normalized email.** `john@gmail.com` and `j.o.h.n@gmail.com` are treated as distinct by HubSpot's uniqueness enforcement even though Gmail delivers them to the same inbox. Your dedup logic must normalize before comparing.

### Finding a contact by email uniqueness

```bash
# HubSpot returns 409 with existing contact ID if email is taken
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://api.hubapi.com/crm/v3/objects/contacts" \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"email": "jane.doe@example.com"}}'
# 409 → contact exists; body contains {"status":"error","category":"CONFLICT","message":"Contact already exists. Existing ID: 101"}

# Extract the existing ID from a 409 response
curl -s -X POST "https://api.hubapi.com/crm/v3/objects/contacts" \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"email": "jane.doe@example.com"}}' \
  | jq -r '.message | capture("Existing ID: (?P<id>[0-9]+)") | .id'
```

---

## Association Re-Parenting Endpoint

```
PUT https://api.hubapi.com/crm/v4/objects/contacts/{primaryId}/associations/{toObjectType}/{toObjectId}
Authorization: Bearer {your-token}
Content-Type: application/json
```

Used to manually create an association that did not transfer during a merge.

### Request body

```json
[
  {
    "associationCategory": "HUBSPOT_DEFINED",
    "associationTypeId": 1
  }
]
```

### Association type IDs (contact-to-object, common)

| Object type | Association type ID | Direction |
|---|---|---|
| `companies` | 1 | contact → company (primary) |
| `deals` | 3 | contact → deal |
| `tickets` | 15 | contact → ticket |
| `calls` | 193 | contact → call |
| `emails` | 197 | contact → email activity |
| `notes` | 201 | contact → note |
| `tasks` | 204 | contact → task |
| `meetings` | 200 | contact → meeting |

For custom objects and non-standard association types, retrieve the catalog via:

```
GET https://api.hubapi.com/crm/v4/associations/contacts/{toObjectType}/labels
```

---

## Rate Limit Reference

| Limit type | Value |
|---|---|
| Burst (Professional) | 100 requests / 10 seconds |
| Burst (Enterprise) | 150 requests / 10 seconds |
| Daily (Professional) | 500,000 requests |
| Daily (Enterprise) | 500,000 requests (higher limits available on request) |
| Batch read max inputs | 100 IDs per call |
| Merge API | Counts as one request per call; no batch merge endpoint |

### Rate limit response headers

| Header | Description |
|---|---|
| `X-HubSpot-RateLimit-Remaining` | Requests remaining in current 10-second window |
| `X-HubSpot-RateLimit-Daily-Remaining` | Requests remaining today (resets midnight UTC) |
| `X-HubSpot-RateLimit-Interval-Milliseconds` | Window size in milliseconds (10000) |
| `X-HubSpot-RateLimit-Max` | Max requests per window |
| `Retry-After` | Seconds to wait before retrying after a 429 |
| `X-HubSpot-Correlation-Id` | Request trace ID — include in support tickets for 500 errors |

---

## Properties Relevant to Deduplication

| Property name | Type | Notes |
|---|---|---|
| `email` | string | Canonical email; unique-enforced by HubSpot |
| `hs_additional_emails` | multi-value string | All known email aliases; populated by merge |
| `phone` | string | Primary phone; not unique-enforced; normalize to E.164 before comparing |
| `firstname` | string | First name |
| `lastname` | string | Last name |
| `hs_object_id` | string | Internal numeric ID — use this, not email, in merge calls |
| `createdate` | datetime | Contact creation timestamp — use for primary selection |
| `lastmodifieddate` | datetime | Last property update — used by HubSpot's conflict resolution |
| `lifecyclestage` | enum | subscriber / lead / marketingqualifiedlead / salesqualifiedlead / opportunity / customer / evangelist |
| `hs_email_optout` | boolean string | "true" / "false" — verify and patch post-merge |
| `hs_email_optout_date` | datetime | When the contact opted out |
| `hs_email_hard_bounce_reason_enum` | enum | Set if email hard-bounced; non-null means contact should not be emailed |
| `hs_legal_basis` | enum | GDPR legal basis; presence requires careful merge handling |
| `hs_merged_object_ids` | multi-value string | IDs of contacts that have been merged into this one; useful for dedup audit |
