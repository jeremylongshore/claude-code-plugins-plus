---
description: Design and implement table partitioning strategies for massive datasets
shortcut: partition
---

# Database Partition Manager

Design, implement, and manage table partitioning strategies for massive datasets with automated partition maintenance, query optimization, and data lifecycle management.

## When to Use This Command

Use `/partition` when you need to:
- Manage tables exceeding 100GB with slow query performance
- Implement time-series data archival strategies (IoT, logs, metrics)
- Optimize queries that filter by date ranges or specific values
- Reduce maintenance window for VACUUM, INDEX, and ANALYZE operations
- Implement efficient data retention policies (delete old partitions)
- Improve parallel query performance across multiple partitions

DON'T use this when:
- Tables are small (<10GB) and perform well
- Queries don't filter by partition key (causes partition pruning failure)
- Application can't be updated to handle partition-aware queries
- Database doesn't support native partitioning (use application-level sharding instead)

## Design Decisions

This command implements **declarative partitioning** because:
- Native database support provides optimal query performance
- Automatic partition pruning reduces query execution time by 90%+
- Constraint exclusion ensures only relevant partitions are scanned
- Partition-wise joins improve multi-table query performance
- Automated partition management reduces operational overhead

**Alternative considered: Application-level sharding**
- Full control over data distribution
- Requires application code changes
- No automatic query optimization
- Recommended for multi-tenant applications with tenant-based isolation

**Alternative considered: Inheritance-based partitioning (legacy)**
- Available in older PostgreSQL versions (<10)
- Manual trigger maintenance required
- No automatic partition pruning
- Recommended only for legacy systems

## Prerequisites

Before running this command:
1. Identify partition key (typically timestamp or category column)
2. Analyze query patterns to ensure they filter by partition key
3. Estimate partition size (target: 10-50GB per partition)
4. Plan partition retention policy (e.g., keep 90 days, archive rest)
5. Test partition migration on development database

## Implementation Process

### Step 1: Analyze Table and Query Patterns
Review table size, query patterns, and identify optimal partition strategy.

### Step 2: Design Partition Schema
Choose partitioning method (range, list, hash) and partition key based on access patterns.

### Step 3: Create Partitioned Table
Convert existing table to partitioned table with minimal downtime using pg_partman or manual migration.

### Step 4: Implement Automated Partition Maintenance
Set up automated partition creation, archival, and cleanup processes.

### Step 5: Optimize Queries for Partition Pruning
Ensure queries include partition key in WHERE clauses for automatic pruning.

## Output Format

The command generates:
- `schema/partitioned_table.sql` - Partitioned table definition
- `maintenance/partition_manager.sql` - Automated partition management functions
- `scripts/partition_maintenance.sh` - Cron job for partition operations
- `migration/convert_to_partitioned.sql` - Zero-downtime migration script
- `monitoring/partition_health.sql` - Partition size and performance monitoring

## Code Examples

### Example 1: PostgreSQL Range Partitioning for Time-Series Data

```sql
-- Create partitioned table for time-series sensor data
CREATE TABLE sensor_readings (
    id BIGSERIAL,
    sensor_id INTEGER NOT NULL,
    reading_value NUMERIC(10,2) NOT NULL,
    reading_time TIMESTAMP NOT NULL,
    metadata JSONB,
    PRIMARY KEY (id, reading_time)
) PARTITION BY RANGE (reading_time);

-- Create indexes on partitioned table (inherited by all partitions)
CREATE INDEX idx_sensor_readings_sensor_id ON sensor_readings (sensor_id);
CREATE INDEX idx_sensor_readings_time ON sensor_readings (reading_time);
CREATE INDEX idx_sensor_readings_metadata ON sensor_readings USING GIN (metadata);

-- Create initial partitions (monthly strategy)
CREATE TABLE sensor_readings_2024_01 PARTITION OF sensor_readings
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE sensor_readings_2024_02 PARTITION OF sensor_readings
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE sensor_readings_2024_03 PARTITION OF sensor_readings
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

-- Create default partition for out-of-range data
CREATE TABLE sensor_readings_default PARTITION OF sensor_readings DEFAULT;

-- Automated partition management function
CREATE OR REPLACE FUNCTION create_monthly_partitions(
    p_table_name TEXT,
    p_months_ahead INTEGER DEFAULT 3
)
RETURNS VOID AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
    v_partition_name TEXT;
    v_sql TEXT;
    v_month INTEGER;
BEGIN
    -- Create partitions for next N months
    FOR v_month IN 1..p_months_ahead LOOP
        v_start_date := DATE_TRUNC('month', CURRENT_DATE + (v_month || ' months')::INTERVAL);
        v_end_date := v_start_date + INTERVAL '1 month';
        v_partition_name := p_table_name || '_' || TO_CHAR(v_start_date, 'YYYY_MM');

        -- Check if partition already exists
        IF NOT EXISTS (
            SELECT 1 FROM pg_class
            WHERE relname = v_partition_name
        ) THEN
            v_sql := FORMAT(
                'CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                v_partition_name,
                p_table_name,
                v_start_date,
                v_end_date
            );

            RAISE NOTICE 'Creating partition: %', v_partition_name;
            EXECUTE v_sql;

            -- Analyze new partition
            EXECUTE FORMAT('ANALYZE %I', v_partition_name);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Automated partition archival and cleanup
CREATE OR REPLACE FUNCTION archive_old_partitions(
    p_table_name TEXT,
    p_retention_months INTEGER DEFAULT 12,
    p_archive_table TEXT DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    v_partition RECORD;
    v_cutoff_date DATE;
    v_sql TEXT;
BEGIN
    v_cutoff_date := DATE_TRUNC('month', CURRENT_DATE - (p_retention_months || ' months')::INTERVAL);

    FOR v_partition IN
        SELECT
            c.relname AS partition_name,
            pg_get_expr(c.relpartbound, c.oid) AS partition_bounds
        FROM pg_class c
        JOIN pg_inherits i ON i.inhrelid = c.oid
        JOIN pg_class p ON p.oid = i.inhparent
        WHERE p.relname = p_table_name
          AND c.relname LIKE p_table_name || '_%'
          AND c.relname != p_table_name || '_default'
        ORDER BY c.relname
    LOOP
        -- Extract partition start date from name
        IF v_partition.partition_name ~ '_\d{4}_\d{2}$' THEN
            DECLARE
                v_partition_date DATE;
            BEGIN
                v_partition_date := TO_DATE(
                    SUBSTRING(v_partition.partition_name FROM '\d{4}_\d{2}$'),
                    'YYYY_MM'
                );

                IF v_partition_date < v_cutoff_date THEN
                    RAISE NOTICE 'Archiving partition: %', v_partition.partition_name;

                    IF p_archive_table IS NOT NULL THEN
                        -- Move data to archive table
                        v_sql := FORMAT(
                            'INSERT INTO %I SELECT * FROM %I',
                            p_archive_table,
                            v_partition.partition_name
                        );
                        EXECUTE v_sql;
                    END IF;

                    -- Detach and drop old partition
                    v_sql := FORMAT(
                        'ALTER TABLE %I DETACH PARTITION %I',
                        p_table_name,
                        v_partition.partition_name
                    );
                    EXECUTE v_sql;

                    v_sql := FORMAT('DROP TABLE %I', v_partition.partition_name);
                    EXECUTE v_sql;

                    RAISE NOTICE 'Dropped partition: %', v_partition.partition_name;
                END IF;
            END;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Partition health monitoring
CREATE OR REPLACE VIEW partition_health AS
SELECT
    schemaname,
    tablename AS partition_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                  pg_relation_size(schemaname||'.'||tablename)) AS index_size,
    n_live_tup AS row_count,
    n_dead_tup AS dead_rows,
    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_row_percent,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE tablename LIKE '%_202%'  -- Filter for partitions
ORDER BY schemaname, tablename;

-- Query to show partition pruning effectiveness
CREATE OR REPLACE FUNCTION explain_partition_pruning(p_query TEXT)
RETURNS TABLE (plan_line TEXT) AS $$
BEGIN
    RETURN QUERY EXECUTE 'EXPLAIN (ANALYZE, BUFFERS) ' || p_query;
END;
$$ LANGUAGE plpgsql;
```

```bash
#!/bin/bash
# scripts/partition_maintenance.sh - Automated Partition Management

set -euo pipefail

# Configuration
DB_NAME="mydb"
DB_USER="postgres"
DB_HOST="localhost"
RETENTION_MONTHS=12
CREATE_AHEAD_MONTHS=3
LOG_FILE="/var/log/partition_maintenance.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create future partitions
create_partitions() {
    log "Creating partitions for next $CREATE_AHEAD_MONTHS months..."

    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<EOF
        SELECT create_monthly_partitions('sensor_readings', $CREATE_AHEAD_MONTHS);
        SELECT create_monthly_partitions('audit_logs', $CREATE_AHEAD_MONTHS);
        SELECT create_monthly_partitions('user_events', $CREATE_AHEAD_MONTHS);
EOF

    log "Partition creation completed"
}

# Archive and cleanup old partitions
cleanup_partitions() {
    log "Archiving partitions older than $RETENTION_MONTHS months..."

    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<EOF
        SELECT archive_old_partitions('sensor_readings', $RETENTION_MONTHS, 'sensor_readings_archive');
        SELECT archive_old_partitions('audit_logs', $RETENTION_MONTHS, 'audit_logs_archive');
        SELECT archive_old_partitions('user_events', $RETENTION_MONTHS, NULL);  -- No archival, just drop
EOF

    log "Partition cleanup completed"
}

# Analyze partitions for query optimization
analyze_partitions() {
    log "Analyzing partitions..."

    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<EOF
        SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
        FROM pg_tables
        WHERE tablename LIKE '%_202%'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

        -- Analyze all partitions
        DO \$\$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE tablename LIKE '%_202%'
            LOOP
                EXECUTE FORMAT('ANALYZE %I.%I', r.schemaname, r.tablename);
            END LOOP;
        END;
        \$\$;
EOF

    log "Partition analysis completed"
}

# Generate health report
health_report() {
    log "Generating partition health report..."

    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<EOF | tee -a "$LOG_FILE"
        \echo '=== Partition Health Report ==='
        \echo ''

        SELECT * FROM partition_health
        WHERE total_size != '0 bytes'
        ORDER BY partition_name DESC
        LIMIT 20;

        \echo ''
        \echo '=== Partitions Needing VACUUM ==='
        SELECT partition_name, dead_row_percent, row_count, dead_rows
        FROM partition_health
        WHERE dead_row_percent > 10
        ORDER BY dead_row_percent DESC;
EOF

    log "Health report generated"
}

# Main execution
main() {
    log "=== Starting Partition Maintenance ==="

    create_partitions
    cleanup_partitions
    analyze_partitions
    health_report

    log "=== Partition Maintenance Completed ==="
}

main "$@"
```

### Example 2: List Partitioning by Category with Hash Sub-Partitioning

```sql
-- Multi-level partitioning: LIST (by region) → HASH (by customer_id)
CREATE TABLE orders (
    order_id BIGSERIAL,
    customer_id INTEGER NOT NULL,
    region VARCHAR(10) NOT NULL,
    order_date TIMESTAMP NOT NULL,
    total_amount NUMERIC(10,2),
    PRIMARY KEY (order_id, region, customer_id)
) PARTITION BY LIST (region);

-- Create regional partitions
CREATE TABLE orders_us PARTITION OF orders
    FOR VALUES IN ('US', 'CA', 'MX')
    PARTITION BY HASH (customer_id);

CREATE TABLE orders_eu PARTITION OF orders
    FOR VALUES IN ('UK', 'FR', 'DE', 'ES', 'IT')
    PARTITION BY HASH (customer_id);

CREATE TABLE orders_asia PARTITION OF orders
    FOR VALUES IN ('JP', 'CN', 'IN', 'SG')
    PARTITION BY HASH (customer_id);

-- Create hash sub-partitions (4 buckets per region for parallel processing)
CREATE TABLE orders_us_0 PARTITION OF orders_us FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE orders_us_1 PARTITION OF orders_us FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE orders_us_2 PARTITION OF orders_us FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE orders_us_3 PARTITION OF orders_us FOR VALUES WITH (MODULUS 4, REMAINDER 3);

CREATE TABLE orders_eu_0 PARTITION OF orders_eu FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE orders_eu_1 PARTITION OF orders_eu FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE orders_eu_2 PARTITION OF orders_eu FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE orders_eu_3 PARTITION OF orders_eu FOR VALUES WITH (MODULUS 4, REMAINDER 3);

CREATE TABLE orders_asia_0 PARTITION OF orders_asia FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE orders_asia_1 PARTITION OF orders_asia FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE orders_asia_2 PARTITION OF orders_asia FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE orders_asia_3 PARTITION OF orders_asia FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Query optimization with partition-wise join
SET enable_partitionwise_join = on;
SET enable_partitionwise_aggregate = on;

-- Demonstrate partition pruning
EXPLAIN (ANALYZE, BUFFERS)
SELECT customer_id, SUM(total_amount) AS total_spent
FROM orders
WHERE region = 'US'
  AND order_date >= '2024-01-01'
  AND order_date < '2024-02-01'
GROUP BY customer_id
ORDER BY total_spent DESC
LIMIT 100;

-- Output shows only orders_us partitions are scanned (not EU or Asia)
```

```python
# scripts/partition_migration.py - Zero-downtime partition migration
import psycopg2
from psycopg2 import sql
import logging
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PartitionMigrator:
    """Migrate existing table to partitioned table with minimal downtime."""

    def __init__(self, connection_string: str):
        self.conn_string = connection_string

    def connect(self):
        return psycopg2.connect(self.conn_string)

    def migrate_to_partitioned(
        self,
        table_name: str,
        partition_column: str,
        partition_type: str = 'RANGE',
        partition_interval: str = 'MONTHLY'
    ):
        """
        Migrate table to partitioned table with zero downtime.

        Strategy:
        1. Create new partitioned table
        2. Copy existing data in batches
        3. Rename tables atomically
        4. Update application to use new table
        """
        conn = self.connect()
        conn.autocommit = False

        try:
            with conn.cursor() as cur:
                # Step 1: Create new partitioned table
                logger.info(f"Creating partitioned table {table_name}_new...")

                cur.execute(f"""
                    CREATE TABLE {table_name}_new (
                        LIKE {table_name} INCLUDING ALL
                    ) PARTITION BY {partition_type} ({partition_column});
                """)

                # Step 2: Create initial partitions based on existing data
                logger.info("Creating initial partitions...")

                if partition_interval == 'MONTHLY':
                    cur.execute(f"""
                        SELECT
                            DATE_TRUNC('month', MIN({partition_column})) AS min_date,
                            DATE_TRUNC('month', MAX({partition_column})) AS max_date
                        FROM {table_name};
                    """)

                    min_date, max_date = cur.fetchone()
                    logger.info(f"Data range: {min_date} to {max_date}")

                    current_date = min_date
                    while current_date <= max_date:
                        next_date = current_date + timedelta(days=32)
                        next_date = next_date.replace(day=1)  # First day of next month

                        partition_name = f"{table_name}_{current_date.strftime('%Y_%m')}"

                        cur.execute(sql.SQL("""
                            CREATE TABLE {} PARTITION OF {} FOR VALUES FROM (%s) TO (%s);
                        """).format(
                            sql.Identifier(partition_name),
                            sql.Identifier(f"{table_name}_new")
                        ), (current_date, next_date))

                        logger.info(f"Created partition: {partition_name}")
                        current_date = next_date

                # Step 3: Copy data in batches
                logger.info("Copying data in batches...")

                batch_size = 10000
                offset = 0

                while True:
                    cur.execute(f"""
                        INSERT INTO {table_name}_new
                        SELECT * FROM {table_name}
                        ORDER BY {partition_column}
                        LIMIT {batch_size} OFFSET {offset};
                    """)

                    rows_copied = cur.rowcount
                    if rows_copied == 0:
                        break

                    offset += batch_size
                    logger.info(f"Copied {offset} rows...")

                    # Commit each batch to avoid long-running transactions
                    conn.commit()

                # Step 4: Verify row counts
                logger.info("Verifying row counts...")

                cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                original_count = cur.fetchone()[0]

                cur.execute(f"SELECT COUNT(*) FROM {table_name}_new;")
                new_count = cur.fetchone()[0]

                if original_count != new_count:
                    raise Exception(
                        f"Row count mismatch! Original: {original_count}, New: {new_count}"
                    )

                logger.info(f"Row count verified: {original_count} rows")

                # Step 5: Rename tables atomically
                logger.info("Renaming tables...")

                cur.execute(f"""
                    BEGIN;
                    ALTER TABLE {table_name} RENAME TO {table_name}_old;
                    ALTER TABLE {table_name}_new RENAME TO {table_name};
                    COMMIT;
                """)

                logger.info("Migration completed successfully!")
                logger.info(f"Old table preserved as {table_name}_old")

            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            conn.close()

    def verify_partition_pruning(self, query: str):
        """Test if query benefits from partition pruning."""
        conn = self.connect()

        try:
            with conn.cursor() as cur:
                cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
                plan = cur.fetchone()[0][0]

                # Extract partition pruning info
                pruned = self._count_pruned_partitions(plan)

                logger.info(f"Partition pruning analysis:")
                logger.info(f"  Total partitions: {pruned['total']}")
                logger.info(f"  Scanned partitions: {pruned['scanned']}")
                logger.info(f"  Pruned partitions: {pruned['pruned']}")
                logger.info(f"  Pruning effectiveness: {pruned['effectiveness']:.1f}%")

                return pruned

        finally:
            conn.close()

    def _count_pruned_partitions(self, plan: dict) -> dict:
        """Recursively count partitions in explain plan."""
        total = 0
        scanned = 0

        def traverse(node):
            nonlocal total, scanned

            if 'Relation Name' in node and '_202' in node['Relation Name']:
                total += 1
                if 'Plans' in node or node.get('Actual Rows', 0) > 0:
                    scanned += 1

            if 'Plans' in node:
                for child in node['Plans']:
                    traverse(child)

        traverse(plan['Plan'])

        pruned = total - scanned
        effectiveness = (pruned / total * 100) if total > 0 else 0

        return {
            'total': total,
            'scanned': scanned,
            'pruned': pruned,
            'effectiveness': effectiveness
        }

# Usage
if __name__ == "__main__":
    migrator = PartitionMigrator(
        "postgresql://user:password@localhost/mydb"
    )

    # Migrate sensor_readings table
    migrator.migrate_to_partitioned(
        table_name='sensor_readings',
        partition_column='reading_time',
        partition_type='RANGE',
        partition_interval='MONTHLY'
    )

    # Verify partition pruning works
    test_query = """
        SELECT * FROM sensor_readings
        WHERE reading_time >= '2024-10-01'
          AND reading_time < '2024-11-01'
        LIMIT 1000;
    """

    migrator.verify_partition_pruning(test_query)
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "No partition of relation ... found for row" | Data outside partition ranges | Create default partition or extend partition range |
| "Partition constraint violated" | Invalid data for partition | Fix data or adjust partition bounds |
| "Cannot create partition of temporary table" | Partitioning temp tables unsupported | Use regular tables or application-level sharding |
| "Too many partitions (>1000)" | Excessive partition count | Increase partition interval (daily → weekly → monthly) |
| "Constraint exclusion not working" | Query doesn't filter by partition key | Rewrite query to include partition key in WHERE clause |

## Configuration Options

**Partition Planning**
- `partition_type`: RANGE (dates), LIST (categories), HASH (distribution)
- `partition_interval`: DAILY, WEEKLY, MONTHLY, YEARLY
- `retention_policy`: How long to keep old partitions
- `partition_size_target`: Target 10-50GB per partition

**Query Optimization**
- `enable_partition_pruning = on`: Enable automatic partition elimination
- `constraint_exclusion = partition`: Enable constraint-based pruning
- `enable_partitionwise_join = on`: Join matching partitions directly
- `enable_partitionwise_aggregate = on`: Aggregate per-partition then combine

## Best Practices

DO:
- Always include partition key in WHERE clauses for pruning
- Target 10-50GB per partition (not too large, not too small)
- Use RANGE partitioning for time-series data
- Use LIST partitioning for categorical data (regions, types)
- Use HASH partitioning for even distribution without natural key
- Automate partition creation 3+ months ahead
- Monitor partition sizes and adjust strategy if needed

DON'T:
- Create thousands of tiny partitions (overhead > benefit)
- Partition tables < 10GB (overhead not justified)
- Use partition key that changes over time
- Query without partition key filter (scans all partitions)
- Forget to analyze partitions after bulk inserts
- Mix partition strategies without clear reason

## Performance Considerations

- Partition pruning can reduce query time by 90%+ on large tables
- Each partition adds ~8KB overhead in PostgreSQL catalogs
- INSERT performance unchanged for single-row inserts
- Bulk INSERT benefits from partition-wise parallelism
- VACUUM and ANALYZE run faster on smaller partitions
- Index creation can be parallelized across partitions

## Related Commands

- `/database-migration-manager` - Schema migrations with partition support
- `/database-backup-automator` - Per-partition backup strategies
- `/database-index-advisor` - Optimize indexes for partitioned tables
- `/sql-query-optimizer` - Ensure queries leverage partition pruning

## Version History

- v1.0.0 (2024-10): Initial implementation with PostgreSQL declarative partitioning
- Planned v1.1.0: Add MySQL partitioning support and automated partition rebalancing
