---
name: hubspot-bulk-migration
description: |
  Bulk-migrate CRM data into HubSpot from Salesforce, Pipedrive, or Copper — or export
  off HubSpot — with field mapping, ID continuity, association re-linking, dedup safety,
  rate-limit budgeting, and rollback mitigation across 100K+ record datasets. Use when
  migrating any source CRM to HubSpot, recovering from a failed import with duplicate or
  unlinked records, or exporting out of HubSpot before switching platforms. Trigger with
  "hubspot bulk migration", "salesforce to hubspot", "pipedrive to hubspot", "copper to
  hubspot", "migrate off hubspot", "hubspot import dedup", "hubspot association relink",
  "hubspot field mapping", "hubspot id continuity".
allowed-tools: Read, Bash(curl:*), Bash(jq:*), Bash(python3:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
tags:
  - hubspot
  - migration
  - data-engineering
  - salesforce
  - import
---

# HubSpot Bulk Migration

## Overview

Move CRM data into HubSpot from Salesforce, Pipedrive, or Copper — or extract it back out — without losing cross-system IDs, breaking associations, or flooding the portal with duplicates. This is not a data-mapping worksheet. It is the code, sequencing, and guardrails your migration runs at 2am against 150K records when the daily API quota is finite, HubSpot has no bulk-delete API, and a bad import leaves permanent junk that requires a support ticket to remove.

The six production failures this skill addresses:

1. **ID continuity loss** — source CRM IDs are not preserved in HubSpot. Fix: create a custom `source_crm_id` property on every object type before the first record lands, and write the source ID into it during import.
2. **Association re-creation failure** — contacts, companies, and deals in the source are associated; batch-importing them independently creates records without associations unless a second pass re-links them after all IDs are known. Fix: import in order (companies → contacts → deals), then re-link in three association passes.
3. **Import dedup missing existing records** — HubSpot's batch upsert deduplicates contacts by email, but only when email matches exactly. Missing or differently-formatted emails create duplicates. Fix: normalize email to lowercase + trimmed before every import; use `batch/upsert` not `batch/create` for contacts.
4. **Field type mismatch** — source date fields in `M/D/Y` format fail HubSpot's ISO 8601 validation; multi-picklist values not in HubSpot's allowed enumeration are silently dropped. Fix: run a pre-migration dry-run that validates every field against HubSpot's property schema before writing a single record.
5. **Rate limit exhaustion** — 100K contacts at 100/batch equals 1,000 API calls; association re-linking doubles that. Combined with retries, a naive migration burns the 500K daily quota before finishing. Fix: budget calls per run, sleep between burst windows, and use the CSV import API for volumes above 10K.
6. **Rollback impossibility** — HubSpot has no bulk-delete API. Fix: maintain a local `source_id → hubspot_id` mapping file throughout the migration so `batch/archive` calls are programmable.

**Auth:** set `HUBSPOT_ACCESS_TOKEN` environment variable to a private app token with CRM write scopes. For token caching, rotation, and multi-portal routing see the `hubspot-auth` skill in this pack.

## Prerequisites

- HubSpot private app token with scopes: `crm.objects.contacts.write`, `crm.objects.companies.write`, `crm.objects.deals.write`, `crm.associations.write`, `crm.schemas.contacts.write`
- Python 3.10+ (`pip install requests`)
- Source CRM data exported to CSV or available via API
- `HUBSPOT_ACCESS_TOKEN` set in environment

## Instructions

### Step 1: Create custom properties for ID continuity

Before importing a single record, create a custom property on every object type to store the source CRM's record ID. Treat `409 CONFLICT` as success — property creation is idempotent.

```python
import os, requests

TOKEN = os.environ["HUBSPOT_ACCESS_TOKEN"]
BASE  = "https://api.hubapi.com"
HDRS  = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def create_source_id_property(object_type: str, source_crm: str) -> None:
    prop_name = f"{source_crm}_id"
    payload = {
        "name": prop_name,
        "label": f"{source_crm.title()} ID",
        "type": "string",
        "fieldType": "text",
        "groupName": f"{object_type}information",
        "description": f"Original {source_crm.title()} record ID. Do not modify.",
    }
    resp = requests.post(f"{BASE}/crm/v3/properties/{object_type}", headers=HDRS, json=payload)
    if resp.status_code not in (200, 201, 409):
        resp.raise_for_status()

for obj in ["contacts", "companies", "deals"]:
    create_source_id_property(obj, "salesforce")  # or "pipedrive", "copper"
```

### Step 2: Validate field types (dry-run before any writes)

Pull HubSpot's property schema and validate every field in your source CSV before touching the API. Catches date format mismatches and invalid enum values upfront.

```python
import csv, json, re
from datetime import datetime

def get_property_schema(object_type: str) -> dict:
    resp = requests.get(f"{BASE}/crm/v3/properties/{object_type}", headers=HDRS)
    resp.raise_for_status()
    return {p["name"]: p for p in resp.json()["results"]}

def validate_record(record: dict, schema: dict) -> list[str]:
    errors = []
    for field, value in record.items():
        if not value or field not in schema:
            continue
        prop = schema[field]
        if prop.get("type") == "date":
            try:
                datetime.strptime(str(value), "%Y-%m-%d")
            except ValueError:
                errors.append(f"{field}='{value}' must be YYYY-MM-DD")
        if prop.get("type") == "enumeration":
            allowed = {o["value"] for o in prop.get("options", [])}
            if allowed and str(value) not in allowed:
                errors.append(f"{field}='{value}' not in allowed values: {sorted(allowed)}")
    return errors
```

Full dry-run driver and field-by-field transform helpers in [implementation-guide.md](references/implementation-guide.md).

### Step 3: Rate-budgeted batch import — contacts first, companies second, deals third

Import in dependency order. Track the `source_id → hubspot_id` mapping per batch. Save the map to disk after every batch — a mid-run crash leaves a complete map for the records that did land.

```python
import time, json

def batch_import(records, object_type, source_id_field, batch_size=100):
    """Import records and return {source_id: hubspot_id} mapping."""
    endpoint = "upsert" if object_type == "contacts" else "create"
    url = f"{BASE}/crm/v3/objects/{object_type}/batch/{endpoint}"
    id_map, errors = {}, []
    batches = [records[i:i+batch_size] for i in range(0, len(records), batch_size)]

    for n, batch in enumerate(batches, 1):
        if endpoint == "upsert":
            payload = {"inputs": [{"idProperty": "email", "id": r.get("email",""), "properties": r} for r in batch]}
        else:
            payload = {"inputs": [{"properties": r} for r in batch]}

        resp = requests.post(url, headers=HDRS, json=payload)
        daily_left = int(resp.headers.get("X-HubSpot-RateLimit-Daily-Remaining", 500_000))
        if resp.status_code == 429:
            time.sleep(int(resp.headers.get("Retry-After", 10)))
            resp = requests.post(url, headers=HDRS, json=payload)
        if resp.status_code not in (200, 201, 207):
            errors.append({"batch": n, "status": resp.status_code})
            continue
        # Daily quota guard — 500K is the Professional/Enterprise daily limit
        if daily_left < 10_000:
            raise RuntimeError(f"Daily quota critical: {daily_left} remaining. Resume tomorrow.")
        for result_item, orig in zip(resp.json().get("results", []), batch):
            src_id = orig.get(source_id_field, "")
            hs_id  = result_item.get("id", "")
            if src_id and hs_id:
                id_map[src_id] = hs_id
        print(f"  Batch {n}/{len(batches)}: {len(batch)} records, daily_left={daily_left}")
        time.sleep(0.12)   # stay below 90 req/10s burst ceiling

    return id_map, errors

def save_id_map(id_map: dict, path: str) -> None:
    existing = {}
    try:
        with open(path) as f: existing = json.load(f)
    except FileNotFoundError: pass
    existing.update(id_map)
    with open(path, "w") as f: json.dump(existing, f, indent=2)
```

### Step 4: Re-link associations (two-pass — after all objects are imported)

```python
def relink_associations(source_assocs, from_id_map, to_id_map,
                         from_type, to_type, type_id, batch_size=100):
    """Re-create associations using v4 API. Returns {linked, skipped, errors}."""
    url = f"{BASE}/crm/v4/associations/{from_type}/{to_type}/batch/create"
    linked = skipped = 0
    errors = []
    batches = [source_assocs[i:i+batch_size] for i in range(0, len(source_assocs), batch_size)]
    for batch in batches:
        inputs = []
        for a in batch:
            fhs = from_id_map.get(a["from_source_id"])
            ths = to_id_map.get(a["to_source_id"])
            if not fhs or not ths:
                skipped += 1; continue
            inputs.append({"from": {"id": fhs}, "to": {"id": ths},
                            "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": type_id}]})
        if not inputs: continue
        resp = requests.post(url, headers=HDRS, json={"inputs": inputs})
        if resp.status_code == 429:
            time.sleep(int(resp.headers.get("Retry-After", 10)))
            resp = requests.post(url, headers=HDRS, json={"inputs": inputs})
        if resp.status_code not in (200, 201, 207):
            errors.append({"status": resp.status_code, "body": resp.text[:200]})
        else:
            linked += len(inputs)
        time.sleep(0.12)
    return {"linked": linked, "skipped": skipped, "errors": errors}

# Standard association type IDs — full table in API_REFERENCE.md
CONTACT_TO_COMPANY, DEAL_TO_CONTACT, DEAL_TO_COMPANY = 1, 3, 5
```

### Step 5: Rollback using ID map

```python
def rollback_migration(id_map_path: str, object_type: str, dry_run: bool = True) -> dict:
    """Archive all records created during migration. Always dry_run=True first."""
    with open(id_map_path) as f:
        id_map = json.load(f)
    hubspot_ids = list(id_map.values())
    archived, errors = 0, []
    for i in range(0, len(hubspot_ids), 100):
        batch = hubspot_ids[i:i+100]
        if dry_run:
            print(f"Would archive: {batch[:3]}...")
            archived += len(batch); continue
        resp = requests.post(f"{BASE}/crm/v3/objects/{object_type}/batch/archive",
                             headers=HDRS, json={"inputs": [{"id": hid} for hid in batch]})
        if resp.status_code == 204:
            archived += len(batch)
        else:
            errors.append({"status": resp.status_code})
        time.sleep(0.12)
    return {"archived": archived, "errors": errors, "dry_run": dry_run}
```

## Error Handling

| HTTP Status | Error | Root Cause | Action |
|---|---|---|---|
| `400` | `INVALID_PROPERTY_NAME` | Field name not in HubSpot schema | Run dry-run; remap source fields to valid HubSpot property names |
| `400` | `INVALID_ENUMERATION_PROPERTY_VALUE` | Picklist value not in allowed options | Pull `GET /crm/v3/properties` and remap; drop unmappable values |
| `400` | `INVALID_DATE` | Date not in `YYYY-MM-DD` or epoch ms | Run `convert_date()` helper (see implementation-guide.md) before import |
| `400` | `REQUIRED_PROPERTY_MISSING` | Upsert `idProperty` value is empty | Normalize email; route no-email contacts to separate `batch/create` call |
| `207` | Partial batch success | Some records succeeded, some failed | Parse both `results[]` and `errors[]`; re-queue failed records |
| `409` | `DUPLICATE_PROPERTY` | Custom property already exists | Treat as success — property creation is idempotent |
| `429` | `RATE_LIMIT` | Burst (100/10s) or daily (500K) quota | Respect `Retry-After`; switch to CSV import API for daily budget relief |
| `500` | HubSpot internal error | Transient portal error | Retry up to 3 times with 2× backoff, 30s cap |
| `503` | `SERVICE_UNAVAILABLE` | HubSpot maintenance | Back off 60s and retry; check status.hubspot.com |

## Examples

### Full Salesforce → HubSpot migration

```python
# 1. Create ID properties
for obj in ["contacts", "companies", "deals"]:
    create_source_id_property(obj, "salesforce")

# 2. Import companies first
import csv
company_rows = [{"salesforce_id": r["Id"], "name": r["Name"],
                  "domain": r.get("Website","").replace("https://","").rstrip("/")}
                for r in csv.DictReader(open("sf_accounts.csv"))]
company_map, _ = batch_import(company_rows, "companies", "salesforce_id")
save_id_map(company_map, "company_id_map.json")

# 3. Import contacts (upsert by email for dedup)
contact_rows = [{"salesforce_id": r["Id"],
                  "email": r.get("Email","").strip().lower(),
                  "firstname": r.get("FirstName",""), "lastname": r.get("LastName","")}
                for r in csv.DictReader(open("sf_contacts.csv"))]
contact_map, _ = batch_import(contact_rows, "contacts", "salesforce_id")
save_id_map(contact_map, "contact_id_map.json")

# 4. Re-link contact → company
source_assocs = [{"from_source_id": r["Id"], "to_source_id": r["AccountId"]}
                 for r in csv.DictReader(open("sf_contacts.csv")) if r.get("AccountId")]
print(relink_associations(source_assocs, contact_map, company_map,
                           "contacts", "companies", CONTACT_TO_COMPANY))
```

### Verify source IDs landed

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/contacts?properties=email,salesforce_id&limit=5" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" | \
  jq '.results[] | {id, email: .properties.email, sf_id: .properties.salesforce_id}'
```

### Rollback (dry run first, always)

```python
print(rollback_migration("contact_id_map.json", "contacts", dry_run=True))
# Confirm output, then:
# rollback_migration("contact_id_map.json", "contacts", dry_run=False)
```

## Output

- Custom source-CRM ID properties (`salesforce_id`, `pipedrive_id`, or `copper_id`) created on contacts, companies, and deals before first write
- Pre-migration validation report with 0 errors before any API calls
- `source_id → hubspot_id` mapping files written per-batch for rollback coverage
- Records imported in dependency order: companies → contacts → deals
- Associations re-linked via v4 API in three post-import passes
- Contacts deduped by normalized email via upsert
- Rollback script scoped to migration ID maps

## Resources

- [HubSpot CRM Objects API](https://developers.hubspot.com/docs/reference/api/crm/objects/contacts)
- [HubSpot Associations v4 API](https://developers.hubspot.com/docs/reference/api/crm/associations)
- [HubSpot CSV Import API](https://developers.hubspot.com/docs/reference/api/crm/imports)
- [HubSpot Properties API](https://developers.hubspot.com/docs/reference/api/crm/properties)
- [HubSpot Rate Limits](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [API_REFERENCE.md](references/API_REFERENCE.md) — batch create/upsert shapes, CSV import API, association batch create, property validation rules, rate limit headers
- [implementation-guide.md](references/implementation-guide.md) — field mapping matrix (Salesforce/Pipedrive/Copper), date conversion helpers, association pipeline details, dry-run workflow, rollback strategy, export-off-HubSpot sequence
