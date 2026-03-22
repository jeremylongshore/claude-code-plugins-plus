---
name: databricks-data-handling
description: |
  Implement Delta Lake data management patterns including GDPR, PII handling, and data lifecycle.
  Use when implementing data retention, handling GDPR requests,
  or managing data lifecycle in Delta Lake.
  Trigger with phrases like "databricks GDPR", "databricks PII",
  "databricks data retention", "databricks data lifecycle", "delete user data".
allowed-tools: Read, Write, Edit, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, databricks-data]

---
# Databricks Data Handling

## Overview
Implement GDPR compliance, PII masking, data retention, and row-level security in Delta Lake with Unity Catalog. Covers data classification tagging, right-to-deletion workflows, automated retention enforcement, column-level masking functions, and subject access request (SAR) reporting.

## Prerequisites
- Unity Catalog enabled
- Understanding of data classification requirements (GDPR, CCPA, HIPAA)
- Admin access for tags and masking functions

## Instructions

### Step 1: Classify and Tag Data
Use Unity Catalog tags to classify tables and columns for automated compliance enforcement.

```sql
-- Tag tables with classification and retention
ALTER TABLE prod_catalog.silver.customers
SET TAGS ('data_classification' = 'PII', 'retention_days' = '730');

ALTER TABLE prod_catalog.silver.orders
SET TAGS ('data_classification' = 'CONFIDENTIAL', 'retention_days' = '365');

ALTER TABLE prod_catalog.gold.metrics
SET TAGS ('data_classification' = 'INTERNAL', 'retention_days' = '1825');

-- Tag PII columns
ALTER TABLE prod_catalog.silver.customers
ALTER COLUMN email SET TAGS ('pii_type' = 'email');

ALTER TABLE prod_catalog.silver.customers
ALTER COLUMN phone SET TAGS ('pii_type' = 'phone');

ALTER TABLE prod_catalog.silver.customers
ALTER COLUMN full_name SET TAGS ('pii_type' = 'name');
```

### Step 2: GDPR Right-to-Deletion
Delete all user data across PII-tagged tables with audit logging.

```python
from pyspark.sql import SparkSession
from datetime import datetime

spark = SparkSession.builder.getOrCreate()

class GDPRHandler:
    """Handle GDPR deletion requests across all PII-tagged tables."""

    def __init__(self, catalog: str):
        self.catalog = catalog

    def find_pii_tables(self) -> list[str]:
        """Find all tables tagged as PII."""
        result = spark.sql(f"""
            SELECT table_catalog, table_schema, table_name
            FROM {self.catalog}.information_schema.table_tags
            WHERE tag_name = 'data_classification' AND tag_value = 'PII'
        """).collect()
        return [f"{r.table_catalog}.{r.table_schema}.{r.table_name}" for r in result]

    def process_deletion(self, user_id: str, request_id: str, dry_run: bool = True) -> dict:
        """Delete user data from all PII tables. Returns audit record."""
        pii_tables = self.find_pii_tables()
        audit = {
            "request_id": request_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "dry_run": dry_run,
            "tables_processed": [],
        }

        for table in pii_tables:
            # Check if table has a user_id-like column
            cols = [c.name for c in spark.table(table).schema]
            user_col = next((c for c in cols if c in ("user_id", "customer_id", "account_id")), None)

            if not user_col:
                continue

            count = spark.sql(
                f"SELECT COUNT(*) AS cnt FROM {table} WHERE {user_col} = '{user_id}'"
            ).first().cnt

            if count > 0 and not dry_run:
                spark.sql(f"DELETE FROM {table} WHERE {user_col} = '{user_id}'")

            audit["tables_processed"].append({
                "table": table,
                "column": user_col,
                "rows_affected": count,
                "action": "DELETED" if not dry_run else "WOULD_DELETE",
            })

        # Log audit record
        if not dry_run:
            spark.createDataFrame([audit]).write.mode("append").saveAsTable(
                f"{self.catalog}.compliance.gdpr_audit_log"
            )

        return audit

# Usage
gdpr = GDPRHandler("prod_catalog")
# Always dry-run first
report = gdpr.process_deletion("user-12345", "GDPR-2024-001", dry_run=True)
for t in report["tables_processed"]:
    print(f"  {t['table']}: {t['rows_affected']} rows {t['action']}")
```

### Step 3: Automated Data Retention
```python
class RetentionEnforcer:
    """Delete data older than retention policy set via table tags."""

    def __init__(self, catalog: str):
        self.catalog = catalog

    def enforce(self, dry_run: bool = True) -> list[dict]:
        """Process all tables with retention_days tag."""
        tagged = spark.sql(f"""
            SELECT table_catalog, table_schema, table_name, tag_value AS retention_days
            FROM {self.catalog}.information_schema.table_tags
            WHERE tag_name = 'retention_days'
        """).collect()

        results = []
        for row in tagged:
            table = f"{row.table_catalog}.{row.table_schema}.{row.table_name}"
            retention_days = int(row.retention_days)

            # Find date column (prefer created_at, event_date, order_date)
            cols = [c.name for c in spark.table(table).schema]
            date_col = next(
                (c for c in cols if c in ("created_at", "event_date", "order_date", "timestamp")),
                None,
            )
            if not date_col:
                continue

            expired = spark.sql(f"""
                SELECT COUNT(*) AS cnt FROM {table}
                WHERE {date_col} < current_timestamp() - INTERVAL {retention_days} DAYS
            """).first().cnt

            if expired > 0 and not dry_run:
                spark.sql(f"""
                    DELETE FROM {table}
                    WHERE {date_col} < current_timestamp() - INTERVAL {retention_days} DAYS
                """)
                # Clean up deleted files
                spark.sql(f"VACUUM {table} RETAIN 168 HOURS")

            results.append({
                "table": table, "retention_days": retention_days,
                "expired_rows": expired, "action": "DELETED" if not dry_run else "WOULD_DELETE",
            })

        return results

# Schedule as a daily Databricks job
enforcer = RetentionEnforcer("prod_catalog")
for r in enforcer.enforce(dry_run=True):
    print(f"  {r['table']}: {r['expired_rows']} rows > {r['retention_days']} days {r['action']}")
```

### Step 4: Column-Level PII Masking
```sql
-- Create masking functions for different PII types
CREATE OR REPLACE FUNCTION prod_catalog.compliance.mask_email(val STRING)
  RETURN IF(IS_ACCOUNT_GROUP_MEMBER('pii-readers'), val,
            CONCAT(LEFT(val, 1), '***@', SUBSTRING_INDEX(val, '@', -1)));

CREATE OR REPLACE FUNCTION prod_catalog.compliance.mask_phone(val STRING)
  RETURN IF(IS_ACCOUNT_GROUP_MEMBER('pii-readers'), val,
            CONCAT('***-***-', RIGHT(val, 4)));

CREATE OR REPLACE FUNCTION prod_catalog.compliance.mask_name(val STRING)
  RETURN IF(IS_ACCOUNT_GROUP_MEMBER('pii-readers'), val,
            CONCAT(LEFT(val, 1), REPEAT('*', LENGTH(val) - 1)));

-- Apply masks to columns
ALTER TABLE prod_catalog.silver.customers
  ALTER COLUMN email SET MASK prod_catalog.compliance.mask_email;

ALTER TABLE prod_catalog.silver.customers
  ALTER COLUMN phone SET MASK prod_catalog.compliance.mask_phone;

ALTER TABLE prod_catalog.silver.customers
  ALTER COLUMN full_name SET MASK prod_catalog.compliance.mask_name;

-- Test: non-privileged users see masked data
-- email: j***@company.com
-- phone: ***-***-1234
-- name: J****
```

### Step 5: Row-Level Security
```sql
-- Restrict data access by department/region
CREATE OR REPLACE FUNCTION prod_catalog.compliance.region_filter(region STRING)
  RETURN IF(IS_ACCOUNT_GROUP_MEMBER('global-admins'), true,
            region IN (SELECT allowed_region
                       FROM prod_catalog.compliance.user_region_access
                       WHERE user_email = current_user()));

ALTER TABLE prod_catalog.gold.sales
  SET ROW FILTER prod_catalog.compliance.region_filter ON (region);

-- Analysts only see data for their assigned regions
```

### Step 6: Subject Access Request (SAR)
```python
def generate_sar_report(catalog: str, user_id: str) -> dict:
    """Generate a GDPR Subject Access Request report."""
    gdpr = GDPRHandler(catalog)
    pii_tables = gdpr.find_pii_tables()

    report = {"user_id": user_id, "generated_at": datetime.utcnow().isoformat(), "data": {}}

    for table in pii_tables:
        cols = [c.name for c in spark.table(table).schema]
        user_col = next((c for c in cols if c in ("user_id", "customer_id")), None)
        if not user_col:
            continue

        rows = spark.sql(f"SELECT * FROM {table} WHERE {user_col} = '{user_id}'").toPandas()
        if not rows.empty:
            report["data"][table] = rows.to_dict(orient="records")

    return report

# Generate and export
sar = generate_sar_report("prod_catalog", "user-12345")
print(f"Found data in {len(sar['data'])} tables")
```

## Output
- Data classification tags on tables and PII columns
- GDPR deletion workflow with dry-run and audit logging
- Automated retention enforcement via tagged policies
- Column masking functions for email, phone, name
- Row-level security restricting access by region/department
- SAR report generation for compliance requests

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `VACUUM` fails | Retention below 7 days | Set minimum `RETAIN 168 HOURS` |
| `DELETE` times out | Very large table | Partition deletes across multiple runs |
| Mask function error | Column type mismatch | Ensure mask function signature matches column type |
| Missing `user_id` column | Non-standard schema | Maintain a table-to-user-column mapping |
| Row filter performance | Complex subquery | Materialize user permissions as a small lookup table |

## Examples

### Quick Compliance Check
```sql
-- Find all PII-tagged tables and their masking status
SELECT t.table_name, t.tag_value AS classification,
       COUNT(c.column_name) AS masked_columns
FROM prod_catalog.information_schema.table_tags t
LEFT JOIN prod_catalog.information_schema.column_tags c
    ON t.table_name = c.table_name AND c.tag_name = 'pii_type'
WHERE t.tag_name = 'data_classification' AND t.tag_value = 'PII'
GROUP BY t.table_name, t.tag_value;
```

## Resources
- [Row and Column Filters](https://docs.databricks.com/aws/en/data-governance/unity-catalog/row-and-column-filters)
- [Unity Catalog Tags](https://docs.databricks.com/aws/en/data-governance/unity-catalog/tags)
- [Delta Lake DELETE](https://docs.databricks.com/aws/en/delta/delta-update)
- [VACUUM](https://docs.databricks.com/aws/en/sql/language-manual/delta-vacuum)

## Next Steps
For enterprise RBAC, see `databricks-enterprise-rbac`.
