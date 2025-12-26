---
name: index-advisor
description: >
  Analyze query patterns and recommend optimal database indexes
shortcut: inde
---
# Database Index Advisor

Analyze query workloads, identify missing indexes, detect unused indexes, and recommend optimal indexing strategies with automated index impact analysis and maintenance scheduling for production databases.

## When to Use This Command

Use `/index-advisor` when you need to:
- Optimize slow queries with proper indexing strategies
- Analyze database workload for missing index opportunities
- Identify and remove unused indexes consuming storage and write performance
- Design composite indexes for multi-column query patterns
- Implement covering indexes to eliminate table lookups
- Monitor index bloat and schedule maintenance (REINDEX, VACUUM)

DON'T use this when:
- Database is small (<1GB) with minimal query load
- All queries are simple primary key lookups
- You're looking for application-level query issues (use query optimizer instead)
- Database doesn't support custom indexes (some managed databases)

## Design Decisions

This command implements **workload-based index analysis** because:
- Real query patterns reveal actual index opportunities
- EXPLAIN ANALYZE provides accurate index impact estimates
- Unused index detection prevents unnecessary write overhead
- Composite index recommendations reduce total index count
- Covering indexes eliminate expensive table lookups (3-10x speedup)

**Alternative considered: Static schema analysis**
- Only analyzes table structure, not query patterns
- Can't estimate real-world performance impact
- May recommend indexes that won't be used
- Recommended only for initial schema design

**Alternative considered: Manual EXPLAIN analysis**
- Requires deep SQL expertise for every query
- Time-consuming and error-prone
- No systematic unused index detection
- Recommended only for ad-hoc optimization

## Prerequisites

Before running this command:
1. Access to database query logs or slow query log
2. Permission to run EXPLAIN ANALYZE on queries
3. Monitoring of database storage and I/O metrics
4. Understanding of application query patterns
5. Maintenance window for index creation (for large tables)

## Implementation Process

### Step 1: Collect Query Workload Data
Capture real production queries from logs or pg_stat_statements.

### Step 2: Analyze Query Execution Plans
Run EXPLAIN ANALYZE to identify sequential scans and suboptimal query plans.

### Step 3: Generate Index Recommendations
Identify missing indexes, composite index opportunities, and covering indexes.

### Step 4: Simulate Index Impact
Estimate query performance improvements with hypothetical indexes.

### Step 5: Implement and Monitor Indexes
Create recommended indexes and track query performance improvements.

## Output Format

The command generates:
- `analysis/missing_indexes.sql` - CREATE INDEX statements for missing indexes
- `analysis/unused_indexes.sql` - DROP INDEX statements for unused indexes
- `reports/index_impact_report.html` - Visual impact analysis with before/after metrics
- `monitoring/index_health.sql` - Queries to monitor index bloat and usage
- `maintenance/reindex_schedule.sh` - Automated index maintenance script

## Code Examples

### Example 1: PostgreSQL Index Advisor with pg_stat_statements

```sql
-- Enable pg_stat_statements extension for query tracking
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Configure extended statistics
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET pg_stat_statements.max = 10000;
SELECT pg_reload_conf();

-- View most expensive queries without proper indexes
CREATE OR REPLACE VIEW slow_queries_needing_indexes AS
SELECT
    queryid,
    LEFT(query, 100) AS query_snippet,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time,
    ROUND((100.0 * total_exec_time / SUM(total_exec_time) OVER ()), 2) AS pct_total_time
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
  AND mean_exec_time > 100  -- Queries averaging >100ms
ORDER BY total_exec_time DESC
LIMIT 50;

-- Identify missing indexes by analyzing sequential scans
CREATE OR REPLACE VIEW tables_needing_indexes AS
SELECT
    schemaname,
    tablename,
    seq_scan AS sequential_scans,
    seq_tup_read AS rows_read_sequentially,
    idx_scan AS index_scans,
    idx_tup_fetch AS rows_fetched_via_index,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    CASE
        WHEN seq_scan > 0 THEN ROUND(100.0 * seq_scan / (seq_scan + COALESCE(idx_scan, 0)), 2)
        ELSE 0
    END AS pct_sequential_scans
FROM pg_stat_user_tables
WHERE seq_scan > 1000  -- Tables with >1000 sequential scans
  AND seq_tup_read > 10000  -- Reading >10k rows sequentially
ORDER BY seq_tup_read DESC;

-- Detect unused indexes consuming storage
CREATE OR REPLACE VIEW unused_indexes AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    pg_get_indexdef(indexrelid) AS index_definition
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- Never used
  AND indexname NOT LIKE '%_pkey'  -- Exclude primary keys
  AND indexname NOT LIKE '%_unique%'  -- Exclude unique constraints
ORDER BY pg_relation_size(indexrelid) DESC;

-- Analyze index bloat and recommend REINDEX
CREATE OR REPLACE VIEW index_bloat_analysis AS
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    pg_size_pretty(pg_relation_size(tablename::regclass)) AS table_size,
    ROUND(100.0 * pg_relation_size(indexrelid) / NULLIF(pg_relation_size(tablename::regclass), 0), 2) AS index_to_table_ratio,
    CASE
        WHEN pg_relation_size(indexrelid) > pg_relation_size(tablename::regclass) * 0.3
        THEN 'High bloat - consider REINDEX'
        WHEN pg_relation_size(indexrelid) > pg_relation_size(tablename::regclass) * 0.15
        THEN 'Moderate bloat - monitor'
        ELSE 'Healthy'
    END AS bloat_status
FROM pg_stat_user_indexes
WHERE pg_relation_size(indexrelid) > 100 * 1024 * 1024  -- >100MB
ORDER BY pg_relation_size(indexrelid) DESC;
```

```python
# scripts/index_advisor.py - Comprehensive Index Analysis Tool
import psycopg2
from psycopg2.extras import DictCursor
import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IndexRecommendation:
    """Represents an index recommendation with impact analysis."""
    table_name: str
    recommended_index: str
    reason: str
    affected_queries: List[str]
    estimated_speedup: str
    storage_cost_mb: float
    priority: str  # 'high', 'medium', 'low'

    def to_dict(self) -> dict:
        return asdict(self)

class PostgreSQLIndexAdvisor:
    """Analyze queries and recommend optimal indexes."""

    def __init__(self, connection_string: str):
        self.conn_string = connection_string

    def connect(self):
        return psycopg2.connect(self.conn_string, cursor_factory=DictCursor)

    def analyze_slow_queries(self, min_duration_ms: int = 100) -> List[Dict]:
        """Identify slow queries from pg_stat_statements."""
        conn = self.connect()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        queryid,
                        LEFT(query, 200) AS query,
                        calls,
                        ROUND(total_exec_time::numeric, 2) AS total_time_ms,
                        ROUND(mean_exec_time::numeric, 2) AS mean_time_ms,
                        ROUND(max_exec_time::numeric, 2) AS max_time_ms
                    FROM pg_stat_statements
                    WHERE mean_exec_time > %s
                      AND query NOT LIKE '%%pg_stat%%'
                      AND query NOT LIKE '%%information_schema%%'
                    ORDER BY total_exec_time DESC
                    LIMIT 100;
                """, (min_duration_ms,))

                return [dict(row) for row in cur.fetchall()]

        finally:
            conn.close()

    def extract_where_columns(self, query: str) -> List[Tuple[str, str]]:
        """Extract table and column names from WHERE clauses."""
        columns = []

        # Pattern: WHERE table.column = value
        where_pattern = r'WHERE\s+(\w+)\.(\w+)\s*[=<>]'
        matches = re.finditer(where_pattern, query, re.IGNORECASE)

        for match in matches:
            table = match.group(1)
            column = match.group(2)
            columns.append((table, column))

        # Pattern: JOIN table ON t1.col = t2.col
        join_pattern = r'JOIN\s+(\w+)\s+\w+\s+ON\s+\w+\.(\w+)\s*=\s*\w+\.\w+'
        matches = re.finditer(join_pattern, query, re.IGNORECASE)

        for match in matches:
            table = match.group(1)
            column = match.group(2)
            columns.append((table, column))

        return columns

    def check_existing_indexes(self, table: str, column: str) -> bool:
        """Check if index exists for table.column."""
        conn = self.connect()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) > 0 AS has_index
                    FROM pg_indexes
                    WHERE tablename = %s
                      AND indexdef LIKE %s;
                """, (table, f'%{column}%'))

                result = cur.fetchone()
                return result['has_index'] if result else False

        finally:
            conn.close()

    def generate_recommendations(self) -> List[IndexRecommendation]:
        """Generate comprehensive index recommendations."""
        recommendations = []

        # Get slow queries
        slow_queries = self.analyze_slow_queries()
        logger.info(f"Analyzing {len(slow_queries)} slow queries...")

        # Track columns needing indexes
        column_usage = defaultdict(lambda: {'count': 0, 'queries': [], 'total_time': 0})

        for query_info in slow_queries:
            query = query_info['query']
            total_time = float(query_info['total_time_ms'])

            # Extract WHERE/JOIN columns
            columns = self.extract_where_columns(query)

            for table, column in columns:
                # Check if index exists
                if not self.check_existing_indexes(table, column):
                    key = f"{table}.{column}"
                    column_usage[key]['count'] += 1
                    column_usage[key]['queries'].append(query[:100])
                    column_usage[key]['total_time'] += total_time

        # Generate recommendations
        for key, usage in column_usage.items():
            table, column = key.split('.')

            # Estimate speedup based on query count and time
            if usage['total_time'] > 10000:  # >10 seconds total
                priority = 'high'
                speedup = '5-10x faster'
            elif usage['total_time'] > 1000:  # >1 second total
                priority = 'medium'
                speedup = '3-5x faster'
            else:
                priority = 'low'
                speedup = '2-3x faster'

            # Estimate storage cost (rough approximation)
            storage_cost = self.estimate_index_size(table)

            recommendation = IndexRecommendation(
                table_name=table,
                recommended_index=f"CREATE INDEX idx_{table}_{column} ON {table}({column});",
                reason=f"Used in {usage['count']} slow queries totaling {usage['total_time']:.0f}ms",
                affected_queries=usage['queries'][:5],  # Top 5 queries
                estimated_speedup=speedup,
                storage_cost_mb=storage_cost,
                priority=priority
            )

            recommendations.append(recommendation)

        # Sort by priority and total time
        recommendations.sort(
            key=lambda r: (
                {'high': 0, 'medium': 1, 'low': 2}[r.priority],
                -sum(1 for _ in r.affected_queries)
            )
        )

        return recommendations

    def estimate_index_size(self, table: str) -> float:
        """Estimate index size in MB based on table size."""
        conn = self.connect()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT pg_relation_size(%s) / (1024.0 * 1024.0) AS size_mb
                    FROM pg_class
                    WHERE relname = %s;
                """, (table, table))

                result = cur.fetchone()
                if result:
                    # Index typically 20-30% of table size
                    return round(result['size_mb'] * 0.25, 2)
                return 10.0  # Default estimate

        except Exception as e:
            logger.warning(f"Could not estimate size for {table}: {e}")
            return 10.0
        finally:
            conn.close()

    def find_unused_indexes(self) -> List[Dict]:
        """Identify indexes that are never used."""
        conn = self.connect()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
                        pg_get_indexdef(indexrelid) AS definition
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0
                      AND indexname NOT LIKE '%_pkey'
                      AND indexname NOT LIKE '%_unique%'
                      AND pg_relation_size(indexrelid) > 1024 * 1024  -- >1MB
                    ORDER BY pg_relation_size(indexrelid) DESC;
                """)

                return [dict(row) for row in cur.fetchall()]

        finally:
            conn.close()

    def generate_report(self):
        """Generate comprehensive index analysis report."""
        logger.info("=== Index Analysis Report ===\n")

        # Recommendations
        recommendations = self.generate_recommendations()

        if recommendations:
            logger.info(f"Found {len(recommendations)} index recommendations:\n")

            for i, rec in enumerate(recommendations, 1):
                logger.info(f"{i}. [{rec.priority.upper()}] {rec.table_name}")
                logger.info(f"   Recommendation: {rec.recommended_index}")
                logger.info(f"   Reason: {rec.reason}")
                logger.info(f"   Expected speedup: {rec.estimated_speedup}")
                logger.info(f"   Storage cost: ~{rec.storage_cost_mb}MB")
                logger.info(f"   Affected queries: {len(rec.affected_queries)}")
                logger.info("")

        # Unused indexes
        unused = self.find_unused_indexes()

        if unused:
            logger.info(f"\n=== Unused Indexes ({len(unused)}) ===\n")

            for idx in unused:
                logger.info(f"DROP INDEX {idx['schemaname']}.{idx['indexname']};")
                logger.info(f"  -- Table: {idx['tablename']}, Size: {idx['index_size']}")

        logger.info("\n=== Summary ===")
        logger.info(f"Missing indexes: {len(recommendations)}")
        logger.info(f"Unused indexes: {len(unused)}")
        logger.info(f"Potential storage savings: {sum(self._parse_size(idx['index_size']) for idx in unused):.2f}MB")

    def _parse_size(self, size_str: str) -> float:
        """Parse PostgreSQL pg_size_pretty output to MB."""
        if 'GB' in size_str:
            return float(size_str.replace(' GB', '').replace('GB', '')) * 1024
        elif 'MB' in size_str:
            return float(size_str.replace(' MB', '').replace('MB', ''))
        elif 'KB' in size_str:
            return float(size_str.replace(' KB', '').replace('KB', '')) / 1024
        return 0.0

# Usage
if __name__ == "__main__":
    advisor = PostgreSQLIndexAdvisor(
        "postgresql://user:password@localhost:5432/mydb"
    )

    advisor.generate_report()
```

### Example 2: MySQL Index Advisor with Performance Schema

```sql
-- Enable performance schema for query analysis
UPDATE performance_schema.setup_instruments
SET ENABLED = 'YES', TIMED = 'YES'
WHERE NAME LIKE 'statement/%';

UPDATE performance_schema.setup_consumers
SET ENABLED = 'YES'
WHERE NAME LIKE '%statements%';

-- Identify slow queries needing indexes
CREATE OR REPLACE VIEW slow_queries_analysis AS
SELECT
    DIGEST_TEXT AS query,
    COUNT_STAR AS executions,
    ROUND(AVG_TIMER_WAIT / 1000000000, 2) AS avg_time_ms,
    ROUND(MAX_TIMER_WAIT / 1000000000, 2) AS max_time_ms,
    ROUND(SUM_TIMER_WAIT / 1000000000, 2) AS total_time_ms,
    SUM_ROWS_EXAMINED AS total_rows_examined,
    SUM_ROWS_SENT AS total_rows_sent,
    ROUND(SUM_ROWS_EXAMINED / COUNT_STAR, 0) AS avg_rows_examined
FROM performance_schema.events_statements_summary_by_digest
WHERE DIGEST_TEXT IS NOT NULL
  AND SCHEMA_NAME NOT IN ('mysql', 'performance_schema', 'information_schema')
  AND AVG_TIMER_WAIT > 100000000  -- >100ms average
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 50;

-- Find tables with full table scans
SELECT
    object_schema AS database_name,
    object_name AS table_name,
    count_read AS select_count,
    count_fetch AS rows_fetched,
    ROUND(count_fetch / NULLIF(count_read, 0), 2) AS avg_rows_per_select
FROM performance_schema.table_io_waits_summary_by_table
WHERE object_schema NOT IN ('mysql', 'performance_schema', 'information_schema')
  AND count_read > 1000
ORDER BY count_fetch DESC;

-- Identify duplicate indexes
SELECT
    t1.TABLE_SCHEMA AS database_name,
    t1.TABLE_NAME AS table_name,
    t1.INDEX_NAME AS index1,
    t2.INDEX_NAME AS index2,
    GROUP_CONCAT(t1.COLUMN_NAME ORDER BY t1.SEQ_IN_INDEX) AS columns
FROM information_schema.STATISTICS t1
JOIN information_schema.STATISTICS t2
    ON t1.TABLE_SCHEMA = t2.TABLE_SCHEMA
    AND t1.TABLE_NAME = t2.TABLE_NAME
    AND t1.INDEX_NAME < t2.INDEX_NAME
    AND t1.COLUMN_NAME = t2.COLUMN_NAME
    AND t1.SEQ_IN_INDEX = t2.SEQ_IN_INDEX
WHERE t1.TABLE_SCHEMA NOT IN ('mysql', 'performance_schema', 'information_schema')
GROUP BY t1.TABLE_SCHEMA, t1.TABLE_NAME, t1.INDEX_NAME, t2.INDEX_NAME
HAVING COUNT(*) = (
    SELECT COUNT(*)
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = t1.TABLE_SCHEMA
      AND TABLE_NAME = t1.TABLE_NAME
      AND INDEX_NAME = t1.INDEX_NAME
);
```

```javascript
// scripts/mysql-index-advisor.js
const mysql = require('mysql2/promise');

class MySQLIndexAdvisor {
    constructor(config) {
        this.pool = mysql.createPool({
            host: config.host,
            user: config.user,
            password: config.password,
            database: config.database,
            waitForConnections: true,
            connectionLimit: 10
        });
    }

    async analyzeTableIndexes(tableName) {
        const [rows] = await this.pool.query(`
            SELECT
                COLUMN_NAME,
                CARDINALITY,
                INDEX_NAME,
                SEQ_IN_INDEX,
                NON_UNIQUE
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = ?
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        `, [tableName]);

        return rows;
    }

    async findMissingIndexes() {
        // Analyze slow queries from performance schema
        const [slowQueries] = await this.pool.query(`
            SELECT
                DIGEST_TEXT AS query,
                COUNT_STAR AS executions,
                ROUND(AVG_TIMER_WAIT / 1000000000, 2) AS avg_time_ms,
                SUM_ROWS_EXAMINED AS total_rows_examined
            FROM performance_schema.events_statements_summary_by_digest
            WHERE AVG_TIMER_WAIT > 100000000
              AND SCHEMA_NAME = DATABASE()
            ORDER BY AVG_TIMER_WAIT DESC
            LIMIT 20
        `);

        const recommendations = [];

        for (const query of slowQueries) {
            // Extract WHERE conditions
            const whereMatch = query.query.match(/WHERE\s+(\w+)\s*[=<>]/i);

            if (whereMatch) {
                const column = whereMatch[1];

                recommendations.push({
                    table: 'unknown',  // Extract from query
                    column: column,
                    query: query.query.substring(0, 100),
                    avgTime: query.avg_time_ms,
                    recommendation: `CREATE INDEX idx_${column} ON table_name(${column});`
                });
            }
        }

        return recommendations;
    }

    async generateReport() {
        console.log('=== MySQL Index Analysis Report ===\n');

        const recommendations = await this.findMissingIndexes();

        console.log(`Found ${recommendations.length} potential index improvements:\n`);

        recommendations.forEach((rec, i) => {
            console.log(`${i + 1}. ${rec.recommendation}`);
            console.log(`   Average query time: ${rec.avgTime}ms`);
            console.log(`   Query: ${rec.query}...`);
            console.log('');
        });
    }
}

// Usage
(async () => {
    const advisor = new MySQLIndexAdvisor({
        host: 'localhost',
        user: 'root',
        password: 'password',
        database: 'mydb'
    });

    await advisor.generateReport();
})();
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Index too large" | Index exceeds max key length | Use partial index or hash index for long columns |
| "Duplicate key violation" | Creating unique index on non-unique data | Check for duplicates before creating unique index |
| "Out of disk space" | Index creation requires temporary storage | Free up disk space or use CONCURRENTLY option |
| "Lock timeout" | Index creation blocking queries | Use CREATE INDEX CONCURRENTLY (PostgreSQL) or ALGORITHM=INPLACE (MySQL) |
| "Statistics out of date" | Old cardinality estimates | Run ANALYZE (PostgreSQL) or ANALYZE TABLE (MySQL) |

## Configuration Options

**Index Types**
- **B-Tree**: Default, good for equality and range queries
- **Hash**: Fast equality lookups (PostgreSQL 10+)
- **GIN/GiST**: Full-text search and JSON queries
- **BRIN**: Block range indexes for very large sequential tables

**Index Options**
- `CONCURRENTLY`: Create without blocking writes (PostgreSQL)
- `ALGORITHM=INPLACE`: Online index creation (MySQL)
- `INCLUDE` columns: Covering index (PostgreSQL 11+)
- `WHERE` clause: Partial index for filtered queries

## Best Practices

DO:
- Create indexes on foreign key columns
- Use composite indexes for multi-column WHERE clauses
- Order composite index columns by selectivity (most selective first)
- Use covering indexes to avoid table lookups
- Create indexes CONCURRENTLY in production
- Monitor index usage with pg_stat_user_indexes

DON'T:
- Create indexes on every column "just in case"
- Index low-cardinality columns (boolean, enum with few values)
- Use functions in WHERE clauses on indexed columns
- Forget to ANALYZE after index creation
- Create redundant indexes (e.g., (a,b) and (a) both exist)

## Performance Considerations

- Each index adds 10-30% write overhead (INSERT/UPDATE/DELETE)
- Indexes consume storage (typically 20-30% of table size)
- Too many indexes slow writes more than they speed reads
- Index-only scans are 3-10x faster than table lookups
- Covering indexes eliminate random I/O entirely
- Partial indexes reduce storage and maintenance overhead

## Related Commands

- `/sql-query-optimizer` - Rewrite queries for better performance
- `/database-partition-manager` - Partition large tables for faster queries
- `/database-health-monitor` - Monitor index bloat and maintenance needs
- `/database-backup-automator` - Schedule REINDEX during maintenance windows

## Version History

- v1.0.0 (2024-10): Initial implementation with PostgreSQL and MySQL support
- Planned v1.1.0: Add hypothetical index simulation and automated A/B testing
