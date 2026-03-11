# Databricks Data Handling - Implementation Details

## Data Classification and Tagging

```sql
-- Tag tables
ALTER TABLE catalog.schema.customers SET TAGS ('data_classification' = 'PII', 'retention_days' = '365');
ALTER TABLE catalog.schema.orders SET TAGS ('data_classification' = 'CONFIDENTIAL', 'retention_days' = '2555');

-- Tag columns
ALTER TABLE catalog.schema.customers ALTER COLUMN email SET TAGS ('pii' = 'true', 'pii_type' = 'email');
ALTER TABLE catalog.schema.customers ALTER COLUMN phone SET TAGS ('pii' = 'true', 'pii_type' = 'phone');

-- Query classified data
SELECT table_catalog, table_schema, table_name, tag_name, tag_value
FROM system.information_schema.table_tags WHERE tag_name = 'data_classification';
```

## GDPR Right to Deletion

```python
class GDPRHandler:
    def process_deletion_request(self, user_id, request_id, dry_run=True):
        report = {"request_id": request_id, "user_id": user_id, "tables_processed": [], "total_rows_deleted": 0}
        pii_tables = self._get_pii_tables()

        for table_info in pii_tables:
            table_name = f"{table_info['catalog']}.{table_info['schema']}.{table_info['table']}"
            user_column = self._get_user_column(table_name)
            if not user_column: continue

            row_count = self.spark.sql(f"SELECT COUNT(*) FROM {table_name} WHERE {user_column} = '{user_id}'").first()[0]
            if row_count > 0:
                if not dry_run:
                    self.spark.sql(f"DELETE FROM {table_name} WHERE {user_column} = '{user_id}'")
                    self._log_deletion(request_id, table_name, user_id, row_count)
                report["tables_processed"].append({"table": table_name, "rows_to_delete": row_count, "deleted": not dry_run})
                report["total_rows_deleted"] += row_count
        return report
```

## Data Retention Policies

```python
class DataRetentionManager:
    def apply_retention_policies(self, dry_run=True):
        tables = self.spark.sql(f"""
            SELECT table_catalog, table_schema, table_name, CAST(tag_value AS INT) as retention_days
            FROM {self.catalog}.information_schema.table_tags WHERE tag_name = 'retention_days'
        """).collect()

        for table in tables:
            full_name = f"{table.table_catalog}.{table.table_schema}.{table.table_name}"
            cutoff_date = datetime.now() - timedelta(days=table.retention_days)
            date_col = self._get_date_column(full_name)
            if not date_col: continue

            count = self.spark.sql(f"SELECT COUNT(*) FROM {full_name} WHERE {date_col} < '{cutoff_date:%Y-%m-%d}'").first()[0]
            if not dry_run and count > 0:
                self.spark.sql(f"DELETE FROM {full_name} WHERE {date_col} < '{cutoff_date:%Y-%m-%d}'")

    def vacuum_tables(self, retention_hours=168):
        tables = self.spark.sql(f"SELECT * FROM {self.catalog}.information_schema.tables WHERE table_type = 'MANAGED'").collect()
        for table in tables:
            self.spark.sql(f"VACUUM {full_name} RETAIN {retention_hours} HOURS")
```

## PII Masking and Anonymization

```python
class PIIMasker:
    @staticmethod
    def mask_email(df, column):
        return df.withColumn(column, concat(substring(col(column), 1, 1), lit("***@***."), regexp_replace(col(column), r".*\.(\w+)$", "$1")))

    @staticmethod
    def mask_phone(df, column):
        return df.withColumn(column, regexp_replace(col(column), r"(\d{3})-(\d{4})$", "***-****"))

    @staticmethod
    def hash_identifier(df, column, salt=""):
        return df.withColumn(column, sha2(concat(col(column), lit(salt)), 256))

    @staticmethod
    def create_masked_view(spark, source_table, view_name, masking_rules):
        df = spark.table(source_table)
        for column, mask_type in masking_rules.items():
            if mask_type == "email": df = PIIMasker.mask_email(df, column)
            elif mask_type == "phone": df = PIIMasker.mask_phone(df, column)
            elif mask_type == "hash": df = PIIMasker.hash_identifier(df, column)
            elif mask_type == "redact": df = df.withColumn(column, lit("[REDACTED]"))
        df.createOrReplaceTempView(view_name)

# Usage
PIIMasker.create_masked_view(spark, "prod_catalog.customers.users", "masked_users",
    {"email": "email", "phone": "phone", "full_name": "name", "ssn": "redact"})
```

## Row-Level Security

```sql
-- Row filter function
CREATE OR REPLACE FUNCTION catalog.security.region_filter(region STRING)
RETURNS BOOLEAN
RETURN (IS_ACCOUNT_GROUP_MEMBER('data-admins') OR region = current_user_attribute('region'));

ALTER TABLE catalog.schema.sales SET ROW FILTER catalog.security.region_filter ON (region);

-- Column masking
CREATE OR REPLACE FUNCTION catalog.security.mask_salary(salary DECIMAL)
RETURNS DECIMAL
RETURN CASE WHEN IS_ACCOUNT_GROUP_MEMBER('hr-team') THEN salary ELSE NULL END;

ALTER TABLE catalog.schema.employees ALTER COLUMN salary SET MASK catalog.security.mask_salary;
```

## Subject Access Request

```python
def generate_sar_report(spark, user_id):
    pii_tables = get_pii_tables(spark)
    report = {"user_id": user_id, "data": {}}
    for table in pii_tables:
        user_col = get_user_column(table)
        if user_col:
            data = spark.sql(f"SELECT * FROM {table} WHERE {user_col} = '{user_id}'").toPandas().to_dict('records')
            report["data"][table] = data
    return report
```
