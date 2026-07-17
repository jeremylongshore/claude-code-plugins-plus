# Warehouse Upsert Patterns (BigQuery / Snowflake / Postgres)

Extracted from SKILL.md § 5. The upsert key is always `id` — HubSpot's immutable
object ID. Never composite on mutable fields like email or name; those can change
and cause phantom duplicates. All three patterns use a staging-table approach:
load new rows into a temp table, then merge into production.

```python
import pandas as pd
import pyarrow as pa

def build_contacts_dataframe(records: list[dict], properties: list[str]) -> pd.DataFrame:
    """
    Normalize HubSpot search API results into a flat DataFrame.

    Key transformations:
    - All timestamps parsed as UTC (avoids timezone-at-load inconsistency)
    - Nested properties dict flattened to columns
    - Missing properties filled with None (not 0 or empty string)
    - _synced_at appended so warehouse always has the load timestamp
    """
    rows = []
    for r in records:
        row = {"id": r["id"]}
        props = r.get("properties", {})
        for p in properties:
            val = props.get(p)
            # HubSpot timestamps are Unix ms UTC — parse explicitly
            if val and p.endswith("date") and val.isdigit():
                row[p] = pd.to_datetime(int(val), unit="ms", utc=True)
            else:
                row[p] = val
        row["_synced_at"] = pd.Timestamp.utcnow()
        rows.append(row)

    return pd.DataFrame(rows)
```

**BigQuery — MERGE upsert**

```python
from google.cloud import bigquery

def upsert_to_bigquery(
    df: pd.DataFrame,
    project: str,
    dataset: str,
    table: str,
    bq_client: bigquery.Client,
) -> int:
    staging_table = f"{project}.{dataset}.{table}_staging"
    target_table  = f"{project}.{dataset}.{table}"

    # Write staging
    job = bq_client.load_table_from_dataframe(df, staging_table,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"))
    job.result()

    # MERGE into target — upsert on id
    merge_sql = f"""
    MERGE `{target_table}` T
    USING `{staging_table}` S
      ON T.id = S.id
    WHEN MATCHED THEN
      UPDATE SET {', '.join(f'T.{c} = S.{c}' for c in df.columns if c != 'id')}
    WHEN NOT MATCHED THEN
      INSERT ({', '.join(df.columns)})
      VALUES ({', '.join(f'S.{c}' for c in df.columns)})
    """
    bq_client.query(merge_sql).result()
    return len(df)
```

**Snowflake — MERGE upsert**

```python
import snowflake.connector

def upsert_to_snowflake(
    df: pd.DataFrame,
    conn: snowflake.connector.SnowflakeConnection,
    schema: str,
    table: str,
) -> int:
    staging = f"{schema}.{table}_staging"
    target  = f"{schema}.{table}"
    cursor  = conn.cursor()

    # Write staging via CSV upload + COPY INTO
    cursor.execute(f"CREATE OR REPLACE TEMP TABLE {staging} LIKE {target}")
    success, nchunks, nrows, _ = snowflake.connector.pandas_tools.write_pandas(
        conn, df, f"{table}_staging", schema=schema, auto_create_table=False
    )

    set_cols  = ", ".join(f"t.{c} = s.{c}" for c in df.columns if c != "id")
    ins_cols  = ", ".join(df.columns)
    ins_vals  = ", ".join(f"s.{c}" for c in df.columns)

    cursor.execute(f"""
        MERGE INTO {target} t
        USING {staging} s ON t.id = s.id
        WHEN MATCHED THEN UPDATE SET {set_cols}
        WHEN NOT MATCHED THEN INSERT ({ins_cols}) VALUES ({ins_vals})
    """)
    return nrows
```

**Postgres — INSERT ... ON CONFLICT upsert**

```python
import psycopg2
from psycopg2.extras import execute_values

def upsert_to_postgres(
    df: pd.DataFrame,
    conn: psycopg2.extensions.connection,
    schema: str,
    table: str,
) -> int:
    cols     = list(df.columns)
    set_expr = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "id")
    sql = f"""
        INSERT INTO {schema}.{table} ({', '.join(cols)})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET {set_expr}
    """
    rows = [tuple(r) for r in df.itertuples(index=False, name=None)]
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)
