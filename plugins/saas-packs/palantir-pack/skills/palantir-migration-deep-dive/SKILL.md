---
name: palantir-migration-deep-dive
description: |
  Execute major Palantir Foundry migration strategies including data migration,
  API version upgrades, and platform transitions.
  Use when migrating data into Foundry, upgrading between API versions,
  or re-platforming existing integrations.
  Trigger with phrases like "migrate to palantir", "foundry migration",
  "palantir data migration", "foundry replatform".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(node:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, migration, data-migration]
compatible-with: claude-code, codex, openclaw
---

# Palantir Migration Deep Dive

## Overview
Comprehensive guide for migrating data into Foundry, migrating from legacy systems to Foundry-backed architectures, and upgrading between Foundry API versions using the strangler fig pattern.

## Prerequisites
- Source system access and schema documentation
- Foundry enrollment with write access
- Understanding of Foundry data pipeline architecture (`palantir-reference-architecture`)

## Instructions

### Step 1: Migration Assessment
```markdown
## Migration Checklist
- [ ] Source system inventory (tables, volumes, refresh rates)
- [ ] Data classification (PII, confidential, public)
- [ ] Schema mapping: source columns → Foundry dataset columns
- [ ] Volume estimate: rows, GB, growth rate
- [ ] Dependencies: downstream consumers of source data
- [ ] Timeline: parallel run period, cutover date
```

### Step 2: Data Migration — Bulk Import
```python
import foundry, pandas as pd

client = get_foundry_client()

# Read source data (example: PostgreSQL)
df = pd.read_sql("SELECT * FROM orders WHERE year >= 2024", source_conn)

# Upload to Foundry dataset
client.datasets.Dataset.upload(
    dataset_rid="ri.foundry.main.dataset.xxxxx",
    branch_id="master",
    file_path="orders.parquet",
    data=df.to_parquet(),
    content_type="application/x-parquet",
)
print(f"Uploaded {len(df)} rows to Foundry")
```

### Step 3: Incremental Sync (Ongoing)
```python
from datetime import datetime, timedelta

def incremental_sync(client, source_conn, dataset_rid, last_sync):
    """Sync only new/changed rows since last sync."""
    query = f"""
        SELECT * FROM orders 
        WHERE updated_at > '{last_sync.isoformat()}'
        ORDER BY updated_at
    """
    df = pd.read_sql(query, source_conn)
    if df.empty:
        print("No new rows to sync")
        return last_sync

    client.datasets.Dataset.upload(
        dataset_rid=dataset_rid,
        branch_id="master",
        file_path=f"sync_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.parquet",
        data=df.to_parquet(),
    )
    print(f"Synced {len(df)} rows")
    return df["updated_at"].max()
```

### Step 4: Strangler Fig Pattern for API Migration
```python
class DualWriteClient:
    """Write to both legacy and Foundry during migration period."""
    def __init__(self, legacy_client, foundry_client):
        self.legacy = legacy_client
        self.foundry = foundry_client
        self.foundry_enabled = os.environ.get("FOUNDRY_WRITES_ENABLED", "false") == "true"

    def create_order(self, order_data):
        # Always write to legacy (source of truth during migration)
        result = self.legacy.create_order(order_data)

        # Shadow write to Foundry (non-blocking)
        if self.foundry_enabled:
            try:
                self.foundry.ontologies.Action.apply(
                    ontology="my-company",
                    action_type="createOrder",
                    parameters=order_data,
                )
            except Exception as e:
                print(f"Foundry shadow write failed (non-fatal): {e}")

        return result
```

### Step 5: Validation and Cutover
```python
def validate_migration(legacy_conn, foundry_client, ontology, object_type):
    """Compare row counts and checksums between source and Foundry."""
    # Legacy count
    legacy_count = pd.read_sql("SELECT COUNT(*) as c FROM orders", legacy_conn).iloc[0]["c"]

    # Foundry count
    foundry_result = foundry_client.ontologies.OntologyObject.aggregate(
        ontology=ontology, object_type=object_type,
        aggregation=[{"type": "count", "name": "total"}],
    )
    foundry_count = foundry_result.data[0].metrics["total"]

    match = legacy_count == foundry_count
    print(f"Legacy: {legacy_count}, Foundry: {foundry_count}, Match: {match}")
    return match
```

## Output
- Migration assessment checklist completed
- Bulk data import to Foundry datasets
- Incremental sync for ongoing changes
- Dual-write pattern for safe cutover
- Validation comparing source and Foundry counts

## Error Handling
| Migration Risk | Detection | Mitigation |
|---------------|-----------|------------|
| Data loss | Row count mismatch | Run validation before cutover |
| Schema mismatch | Transform errors | Map schemas explicitly |
| Dual-write divergence | Checksum differences | Reconciliation job |
| Rollback needed | Production issues | Keep legacy running during parallel period |

## Resources
- [Foundry Data Integration](https://www.palantir.com/docs/foundry/data-integration/rest-apis/)
- [Foundry Connectors](https://www.palantir.com/docs/foundry/available-connectors/rest-apis)

## Next Steps
For SDK version upgrades, see `palantir-upgrade-migration`.
