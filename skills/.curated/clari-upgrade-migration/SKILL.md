---
name: clari-upgrade-migration
description: 'Handle Clari API version changes and export schema migrations.

  Use when Clari updates their API, export format changes,

  or migrating from v3 to v4 API.

  Trigger with phrases like "upgrade clari", "clari api migration",

  "clari schema change", "clari v4 migration".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- revenue-intelligence
- forecasting
- clari
compatibility: Designed for Claude Code
---
# Clari Upgrade & Migration

## Overview

Handle Clari API changes: version migrations, export schema updates, and Copilot API adoption.

## Prerequisites

- Current and target API/schema versions recorded in change control
- Representative non-production exports and an approved compatibility baseline
- Version-pinned client, warehouse migration, and rollback paths
- Data-owner approval for any field, retention, or analytics semantic change

## Instructions

### Step 1: Check Current API Version

```bash
# v4 is the current version
curl -s -H "apikey: ${CLARI_API_KEY}" \
  https://api.clari.com/v4/export/forecast/list | jq .

# If using v3 (deprecated), migrate to v4
```

### Step 2: Schema Change Detection

```python
def detect_schema_changes(
    current_export: dict, expected_fields: set[str]
) -> dict:
    if not current_export.get("entries"):
        return {"status": "empty", "changes": []}

    actual_fields = set(current_export["entries"][0].keys())
    new_fields = actual_fields - expected_fields
    removed_fields = expected_fields - actual_fields

    return {
        "status": "changed" if new_fields or removed_fields else "compatible",
        "new_fields": list(new_fields),
        "removed_fields": list(removed_fields),
    }

# Track expected schema
EXPECTED_FIELDS = {
    "ownerName", "ownerEmail", "forecastAmount", "quotaAmount",
    "crmTotal", "crmClosed", "adjustmentAmount", "timePeriod"
}
```

### Step 3: Database Schema Migration

```sql
-- Add new columns when Clari adds export fields
ALTER TABLE clari_forecasts ADD COLUMN IF NOT EXISTS new_field_name VARCHAR;

-- Backfill historical data
UPDATE clari_forecasts SET new_field_name = 'default' WHERE new_field_name IS NULL;
```

### Rollback

Keep the previous client version alongside the new one until migration is verified:

```python
# Pin client to specific behavior
client_v4 = ClariClient(ClariConfig(api_key=api_key, base_url="https://api.clari.com/v4"))
```

## Error Handling

| Condition | Response |
|---|---|
| Source removes or renames a field | Block promotion, update the compatibility contract, and revalidate transformations. |
| Backfill produces unexpected values | Stop the migration, preserve the prior certified table, and investigate with redacted samples. |
| New client or endpoint fails | Restore the pinned prior client and record the provider/job evidence. |
| Schema is empty or ambiguous | Do not infer compatibility; obtain an approved source contract or defer the change. |

## Output

Create a migration receipt with source/target versions, detected fields,
compatibility decision, tested transform, backfill counts, validation evidence,
rollback result, and named approver. Keep live credentials and raw forecast
values out of the receipt.

## Examples

Detect a new export field in staging, add it behind a nullable warehouse
migration, compare redacted records with the prior client, and verify the
analytics contract before promotion. If a mandatory field disappears, retain
the previous client and certified dataset while the data owner decides the new
semantic mapping.

## Resources

- [Clari Developer Portal](https://developer.clari.com)
- [Clari Community](https://community.clari.com)

## Next Steps

For CI integration, see `clari-ci-integration`.
