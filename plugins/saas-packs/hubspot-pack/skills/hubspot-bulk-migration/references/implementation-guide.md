# HubSpot Bulk Migration — Implementation Guide

Field mapping matrices, ID continuity strategy, association re-linking pipeline, pre-migration dry-run workflow, rollback mitigation, and migration off HubSpot. The Python code for each step lives in `SKILL.md`; this document provides the field reference tables and migration architecture decisions that stay stable across source CRMs.

---

## Field Mapping Matrix

### Salesforce → HubSpot Contacts

| Salesforce Field | HubSpot Property | Type | Transform Required |
|---|---|---|---|
| `Id` | `salesforce_id` (custom) | string | None — store verbatim |
| `Email` | `email` | string | Lowercase + trim |
| `FirstName` | `firstname` | string | None |
| `LastName` | `lastname` | string | None |
| `Phone` | `phone` | string | None (HubSpot accepts any format) |
| `MobilePhone` | `mobilephone` | string | None |
| `Title` | `jobtitle` | string | None |
| `Department` | `department` | string | None |
| `AccountId` | Association only | — | Resolve to company HubSpot ID via company ID map |
| `LeadSource` | `hs_lead_status` | enumeration | Map SF values to HubSpot enum values (see table below) |
| `CreatedDate` | `createdate` | date | `YYYY-MM-DDTHH:MM:SSZ` → epoch ms OR `YYYY-MM-DD` |
| `LastModifiedDate` | — | — | HubSpot manages `lastmodifieddate` internally; do not import |
| `OwnerId` | `hubspot_owner_id` | string | Map SF user ID → HubSpot owner ID (requires owner lookup) |
| `MailingCity` | `city` | string | None |
| `MailingState` | `state` | string | None |
| `MailingCountry` | `country` | string | None |
| `MailingPostalCode` | `zip` | string | None |
| `Description` | `description` | string | None |
| `LinkedIn_URL__c` | `hs_linkedin_url` | string | None |

### Salesforce → HubSpot Companies (Accounts)

| Salesforce Field | HubSpot Property | Type | Transform Required |
|---|---|---|---|
| `Id` | `salesforce_id` (custom) | string | None |
| `Name` | `name` | string | None |
| `Website` | `domain` | string | Strip `http://`, `https://`, trailing `/` |
| `Phone` | `phone` | string | None |
| `BillingCity` | `city` | string | None |
| `BillingState` | `state` | string | None |
| `BillingCountry` | `country` | string | None |
| `BillingPostalCode` | `zip` | string | None |
| `Industry` | `industry` | enumeration | Map SF industry values to HubSpot enum |
| `NumberOfEmployees` | `numberofemployees` | number | Integer string only; strip commas |
| `AnnualRevenue` | `annualrevenue` | number | Numeric only; no `$` or commas |
| `Description` | `description` | string | None |
| `Type` | `type` (custom) | string | Create custom property; SF Account Types don't map 1:1 |

### Salesforce → HubSpot Deals (Opportunities)

| Salesforce Field | HubSpot Property | Type | Transform Required |
|---|---|---|---|
| `Id` | `salesforce_id` (custom) | string | None |
| `Name` | `dealname` | string | None |
| `Amount` | `amount` | number | Numeric only; no `$` |
| `CloseDate` | `closedate` | date | `YYYY-MM-DD` or epoch ms |
| `StageName` | `dealstage` | enumeration | Map SF stage names to HubSpot pipeline stage IDs |
| `Probability` | `hs_deal_stage_probability` | number | Decimal (0.0–1.0); HubSpot sets automatically from stage |
| `Description` | `description` | string | None |
| `OwnerId` | `hubspot_owner_id` | string | Map SF user ID → HubSpot owner ID |
| `AccountId` | Association | — | Resolve to deal→company association |
| `ContactId` | Association | — | Resolve to deal→contact association |

---

### Pipedrive → HubSpot Contacts (Persons)

| Pipedrive Field | HubSpot Property | Type | Transform Required |
|---|---|---|---|
| `id` | `pipedrive_id` (custom) | string | None |
| `email[0].value` | `email` | string | Lowercase + trim |
| `first_name` | `firstname` | string | None |
| `last_name` | `lastname` | string | None |
| `phone[0].value` | `phone` | string | None |
| `job_title` | `jobtitle` | string | None |
| `org_id` | Association only | — | Resolve to company HubSpot ID |
| `add_time` | `createdate` | date | `YYYY-MM-DD HH:MM:SS` → `YYYY-MM-DD` |
| `owner_id.name` | `hubspot_owner_id` | string | Match by email to HubSpot owner |

### Pipedrive → HubSpot Companies (Organizations)

| Pipedrive Field | HubSpot Property | Type | Transform Required |
|---|---|---|---|
| `id` | `pipedrive_id` (custom) | string | None |
| `name` | `name` | string | None |
| `address.street` | — | — | Combine into `address` custom property or split |
| `address.city` | `city` | string | None |
| `address.country` | `country` | string | None |
| `owner_id.name` | `hubspot_owner_id` | string | Match by email to HubSpot owner |

### Pipedrive → HubSpot Deals

| Pipedrive Field | HubSpot Property | Type | Transform Required |
|---|---|---|---|
| `id` | `pipedrive_id` (custom) | string | None |
| `title` | `dealname` | string | None |
| `value` | `amount` | number | Numeric |
| `close_time` | `closedate` | date | `YYYY-MM-DD` |
| `stage_id` | `dealstage` | enumeration | Map Pipedrive stage ID → HubSpot pipeline stage internal value |
| `status` | `dealstage` | enumeration | `won` → closed-won stage; `lost` → closed-lost |
| `person_id` | Association | — | deal→contact |
| `org_id` | Association | — | deal→company |

---

### Copper → HubSpot Contacts (People)

| Copper Field | HubSpot Property | Type | Transform Required |
|---|---|---|---|
| `id` | `copper_id` (custom) | string | None |
| `emails[0].email` | `email` | string | Lowercase + trim |
| `first_name` | `firstname` | string | None |
| `last_name` | `lastname` | string | None |
| `phone_numbers[0].number` | `phone` | string | None |
| `title` | `jobtitle` | string | None |
| `company_id` | Association | — | Resolve to company HubSpot ID |

### Copper → HubSpot Companies

| Copper Field | HubSpot Property | Type | Transform Required |
|---|---|---|---|
| `id` | `copper_id` (custom) | string | None |
| `name` | `name` | string | None |
| `website` | `domain` | string | Strip protocol + trailing slash |
| `address.city` | `city` | string | None |

### Copper → HubSpot Opportunities (Deals)

| Copper Field | HubSpot Property | Type | Transform Required |
|---|---|---|---|
| `id` | `copper_id` (custom) | string | None |
| `name` | `dealname` | string | None |
| `monetary_value` | `amount` | number | Numeric |
| `close_date` | `closedate` | date | Unix timestamp → `YYYY-MM-DD` |
| `pipeline_stage_id` | `dealstage` | enumeration | Map Copper stage ID → HubSpot pipeline stage |
| `company_id` | Association | — | deal→company |
| `primary_contact_id` | Association | — | deal→contact |

---

## ID Continuity Strategy

The goal is to never lose the source CRM's record ID. Cross-system joins, audit trails, integration rollbacks, and support tickets all depend on being able to say "HubSpot contact 12345 was Salesforce contact 003XXXXXXXXXXXXXXXXX."

### Architecture

```
Source CRM Record
  └── source_id: "003XXXXXXXXXXXXXXXXX"
                                    ┌──────────────────────────────┐
  HubSpot Contact ─────────────────▶│ salesforce_id: "003XXXXXX..." │
    hs_object_id: "12345"           └──────────────────────────────┘
                                    
migration_id_map.json
  "003XXXXXXXXXXXXXXXXX": "12345"   ← persisted per-batch for rollback
```

### Custom property naming convention

| Source CRM | Property name | Label |
|---|---|---|
| Salesforce | `salesforce_id` | Salesforce ID |
| Pipedrive | `pipedrive_id` | Pipedrive ID |
| Copper | `copper_id` | Copper ID |
| Generic | `source_crm_id` | Source CRM ID |

Use exactly one naming convention per migration run. Do not use `external_id` — that name collides with HubSpot's sync partner integrations.

### When source records have no stable ID

Some CSV exports replace IDs with display names. Build a derived key before migration:

```python
import hashlib

def derive_stable_id(row: dict, key_fields: list[str]) -> str:
    """
    Create a deterministic ID from key fields when the source has no stable ID.
    Example: hash email + company name for contacts.
    """
    key = "|".join(str(row.get(f, "")).strip().lower() for f in key_fields)
    return "derived_" + hashlib.sha256(key.encode()).hexdigest()[:16]

# For a CSV export without row IDs:
# contact_id = derive_stable_id(row, ["Email", "FirstName", "LastName"])
```

---

## Association Re-Linking Pipeline

The two-pass pipeline is mandatory. Importing all object types first and trying to create associations in the same pass fails because the "to" object's HubSpot ID is not yet known.

### Import order

```
Pass 1: Companies   (no dependencies)
Pass 2: Contacts    (depends on company IDs for association pass)
Pass 3: Deals       (depends on contact and company IDs)
Pass 4: Contact → Company associations
Pass 5: Deal → Contact associations
Pass 6: Deal → Company associations
```

### ID map files per pass

| Pass | ID map file | Key | Value |
|---|---|---|---|
| 1 | `company_id_map.json` | source company ID | HubSpot company ID |
| 2 | `contact_id_map.json` | source contact ID | HubSpot contact ID |
| 3 | `deal_id_map.json` | source deal ID | HubSpot deal ID |

### Association lookup table

| Association | fromObjectType | toObjectType | typeId |
|---|---|---|---|
| Contact → Company | `contacts` | `companies` | `1` |
| Deal → Contact | `deals` | `contacts` | `3` |
| Deal → Company | `deals` | `companies` | `5` |

### Building the source association file

Before running Pass 4–6, build a list of source-level associations from your export. For Salesforce, the `AccountId` field on Contact records is the Contact→Company join.

```python
import csv

def extract_sf_contact_company_assocs(contacts_csv: str) -> list[dict]:
    """Extract contact→company associations from Salesforce Contact export."""
    assocs = []
    with open(contacts_csv) as f:
        for row in csv.DictReader(f):
            contact_id = row.get("Id", "")
            account_id = row.get("AccountId", "")
            if contact_id and account_id:
                assocs.append({
                    "from_source_id": contact_id,   # contact
                    "to_source_id": account_id,      # company
                })
    return assocs

def extract_sf_deal_contact_assocs(opportunities_csv: str, contact_roles_csv: str) -> list[dict]:
    """
    Salesforce Opportunities don't have a direct ContactId.
    Use OpportunityContactRole export: OpportunityId, ContactId, IsPrimary.
    """
    assocs = []
    with open(contact_roles_csv) as f:
        for row in csv.DictReader(f):
            if row.get("IsPrimary", "").lower() == "true":
                assocs.append({
                    "from_source_id": row["OpportunityId"],   # deal
                    "to_source_id": row["ContactId"],          # contact
                })
    return assocs
```

### Skipped associations

When an ID in the association list has no entry in the ID map, the association is skipped. This happens when:

- The source record failed validation and was not imported
- The source record was a duplicate and was not imported (upsert merged it)
- The ID map file is incomplete (partial run)

Log all skipped associations to a file for manual review:

```python
def relink_with_logging(
    source_associations, from_id_map, to_id_map,
    from_type, to_type, type_id,
    skipped_log_path="skipped_associations.jsonl"
):
    skipped = []
    valid = []
    for assoc in source_associations:
        from_hs = from_id_map.get(assoc["from_source_id"])
        to_hs = to_id_map.get(assoc["to_source_id"])
        if not from_hs or not to_hs:
            skipped.append({**assoc, "reason": "ID not in map", "from_hs": from_hs, "to_hs": to_hs})
        else:
            valid.append({**assoc, "from_hs": from_hs, "to_hs": to_hs})
    # Write skipped log
    with open(skipped_log_path, "a") as f:
        for s in skipped:
            f.write(json.dumps(s) + "\n")
    print(f"  {len(valid)} valid associations, {len(skipped)} skipped → {skipped_log_path}")
    return valid
```

---

## Pre-Migration Dry-Run Workflow

Run the dry-run for every object type before writing a single record. The workflow catches all six failure modes at validation time rather than at import time.

```
1. Pull HubSpot property schema for contacts, companies, deals
2. Load field mapping for source CRM
3. For each source record:
   a. Map source fields to HubSpot property names
   b. Validate each field against schema type rules
   c. Check enumeration values against allowed options
   d. Check date fields for ISO 8601 compliance
   e. Check required fields (email for contacts if using upsert)
4. Write error report
5. Assert error_count == 0 before proceeding
```

### Date conversion helper

```python
from datetime import datetime, timezone

def convert_date(value: str, source_format: str = "auto") -> str:
    """
    Convert a date string to YYYY-MM-DD for HubSpot.
    source_format: 'auto' tries common formats; or pass strptime format string.
    Returns empty string if conversion fails (log and drop rather than import bad data).
    """
    if not value or str(value).strip() in ("", "None", "null", "N/A"):
        return ""
    
    formats_to_try = [
        "%Y-%m-%d",           # ISO 8601 — already correct
        "%Y-%m-%dT%H:%M:%SZ", # ISO datetime
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%m/%d/%Y",           # M/D/Y — common US export format
        "%m/%d/%y",           # M/D/YY
        "%d/%m/%Y",           # D/M/Y — European
        "%Y/%m/%d",
    ]
    if source_format != "auto":
        formats_to_try = [source_format] + formats_to_try

    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(str(value).strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Try Unix timestamp (Copper uses these)
    try:
        ts = int(value)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass
    
    return ""  # Drop — log caller should record this field/value pair

def convert_date_to_epoch_ms(value: str) -> int | None:
    """Convert to epoch milliseconds for HubSpot datetime properties."""
    date_str = convert_date(value)
    if not date_str:
        return None
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)
```

### Enumeration mapping examples

HubSpot's built-in enumeration values differ from Salesforce and Pipedrive's. Map before import — do not pass source values directly.

#### Salesforce LeadSource → HubSpot hs_lead_status

| Salesforce LeadSource | HubSpot hs_lead_status |
|---|---|
| `Web` | `NEW` |
| `Phone Inquiry` | `NEW` |
| `Partner Referral` | `OPEN` |
| `Purchased List` | `OPEN` |
| `Other` | `OPEN` |
| `Internal` | `CONNECTED` |

Note: `hs_lead_status` is a different property from lead source. The HubSpot equivalent of Salesforce `LeadSource` is `hs_analytics_source`. Check your portal's property settings — custom picklists may differ.

#### Salesforce Opportunity StageName → HubSpot dealstage

HubSpot deal stages are defined per pipeline and use internal value strings (not display names). Pull your pipeline's stage IDs first:

```bash
curl -s "https://api.hubapi.com/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" | \
  jq '.results[] | {pipelineId: .id, label: .label, stages: [.stages[] | {label: .label, internalValue: .id}]}'
```

Map Salesforce stage names to the `internalValue` from your pipeline's response — not the stage label. The internal value is a UUID-style string like `appointmentscheduled` or `b81b3d5d-e3df-4fa2-b0ec-`.

---

## Rollback Mitigation Strategy

HubSpot has no bulk-delete API. Archive (soft-delete) is the only programmatic cleanup path and requires knowing the HubSpot IDs. The `migration_id_map.json` file is the recovery instrument.

### Why the ID map is load-bearing

Without the ID map, rollback requires:

1. Exporting all contacts from HubSpot after the migration
2. Filtering to records where `salesforce_id` matches the migration run
3. Extracting HubSpot IDs from that export
4. Running batch archive calls

With the ID map, step 1–3 are skipped. The map is written per-batch, not at end-of-run, so a partial run (e.g., crash after 50K of 100K records) still has a complete map for the records that did land.

### ID map structure

```json
{
  "003XXXXXXXXXXXXXXXXX": "12345",
  "003YYYYYYYYYYYYYYYYY": "12346",
  "003ZZZZZZZZZZZZZZZZZ": "12347"
}
```

### Rollback procedure

```
1. Verify dry_run=True rollback output matches expected count
2. Pause all integrations that read from HubSpot (webhooks, Zapier, etc.)
3. Run rollback_migration("contact_id_map.json", "contacts", dry_run=False)
4. Run rollback_migration("company_id_map.json", "companies", dry_run=False)
5. Run rollback_migration("deal_id_map.json", "deals", dry_run=False)
6. Wait 5 minutes (HubSpot's index update lag)
7. Verify record counts match pre-migration baseline
8. Re-enable integrations
```

### Rollback limitations

- Archive is soft-delete — records are recoverable from HubSpot trash for 90 days.
- If the failed migration overwrote existing records (upsert matched email and updated properties), rollback cannot restore the original values. The solution: export existing contacts before migration and store the snapshot. On rollback, re-import the snapshot.
- Properties created during migration (e.g., `salesforce_id`) are not removed by archive — they must be deleted via `DELETE /crm/v3/properties/{objectType}/{propertyName}` after confirming all records are cleaned up.

### Pre-migration snapshot for safe upsert rollback

```python
def snapshot_existing_contacts(properties: list[str], snapshot_path: str = "pre_migration_snapshot.jsonl") -> int:
    """
    Export all existing contacts before migration.
    Enables full property rollback if upsert overwrites existing records.
    """
    records = export_all_records("contacts", properties)
    with open(snapshot_path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"Snapshot: {len(records)} contacts → {snapshot_path}")
    return len(records)

# Run before any import
snapshot_existing_contacts(
    properties=["email", "firstname", "lastname", "phone", "jobtitle", "company",
                "hs_lead_status", "createdate"],
    snapshot_path="pre_migration_snapshot.jsonl"
)
```

---

## Migrating Off HubSpot

Export all records, associations, and activity history before switching to a new CRM.

### Export sequence

```
1. Export contacts with all properties
2. Export companies with all properties
3. Export deals with all properties
4. Export associations (contact→company, deal→contact, deal→company)
5. Export notes and engagements (calls, emails, meetings)
```

### Export contacts with all custom properties

```python
def get_all_property_names(object_type: str) -> list[str]:
    """Returns all property names for an object type."""
    resp = requests.get(f"{BASE}/crm/v3/properties/{object_type}", headers=HEADERS)
    resp.raise_for_status()
    return [p["name"] for p in resp.json()["results"]]

# Get all property names
contact_props = get_all_property_names("contacts")
# Export all contacts with all properties
all_contacts = export_all_records("contacts", contact_props)
```

### Export associations

```python
def export_associations(from_type: str, to_type: str) -> list[dict]:
    """Export all associations between two object types."""
    # Get all from-object IDs first
    from_ids = [r["id"] for r in export_all_records(from_type, ["hs_object_id"])]
    
    # Batch association read: 100 IDs per call
    url = f"{BASE}/crm/v4/associations/{from_type}/{to_type}/batch/read"
    all_assocs = []
    for i in range(0, len(from_ids), 100):
        batch = from_ids[i:i+100]
        resp = requests.post(url, headers=HEADERS,
                             json={"inputs": [{"id": fid} for fid in batch]})
        if resp.status_code == 200:
            for result in resp.json().get("results", []):
                for to_obj in result.get("to", []):
                    all_assocs.append({
                        "from_id": result["from"]["id"],
                        "to_id": to_obj["toObjectId"],
                        "type_id": to_obj["associationTypes"][0]["typeId"]
                    })
        time.sleep(0.12)
    return all_assocs
```

### Write export to CSV

```python
def write_export_csv(records: list[dict], path: str) -> None:
    if not records:
        return
    # Flatten nested properties dict
    flat = []
    for r in records:
        row = {"hs_object_id": r["id"]}
        row.update(r.get("properties", {}))
        flat.append(row)
    fieldnames = list(flat[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flat)
    print(f"Exported {len(flat)} records → {path}")
```

---

## Migration Run Checklist

Run through this checklist before executing any write operations.

```
Pre-migration
[ ] Source data exported to CSV (one file per object type)
[ ] Custom source_crm_id properties created in HubSpot
[ ] Pre-migration contact snapshot taken (for upsert rollback)
[ ] Dry-run validation passed with 0 errors
[ ] Rate limit budget calculated (total batches × 2 for retries)
[ ] ID map files initialized (empty JSON files with write permission)
[ ] All integrations paused (Zapier, webhooks, Salesforce sync)

During migration
[ ] Companies imported — company_id_map.json saved
[ ] Contacts imported (upsert) — contact_id_map.json saved
[ ] Deals imported — deal_id_map.json saved
[ ] Contact → Company associations re-linked
[ ] Deal → Contact associations re-linked
[ ] Deal → Company associations re-linked
[ ] Skipped associations logged to skipped_associations.jsonl

Post-migration
[ ] Record counts verified (source total vs HubSpot total)
[ ] Sample records spot-checked (5–10 records per object type)
[ ] Associations verified on 5–10 records
[ ] Source CRM IDs verified on 5–10 records
[ ] Daily quota consumed checked (should be < 50%)
[ ] Integrations re-enabled
[ ] Migration ID maps archived to secure storage (retention: 1 year)
```
