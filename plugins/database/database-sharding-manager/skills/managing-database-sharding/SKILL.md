---
name: managing-database-sharding
description: |
  Process use when you need to work with database sharding.
  This skill provides horizontal sharding strategies with comprehensive guidance and automation.
  Trigger with phrases like "implement sharding", "shard database",
  or "distribute data".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Sharding Manager

## Overview

Implement and manage horizontal database sharding strategies across PostgreSQL, MySQL, and MongoDB. This skill covers shard key selection, data distribution analysis, cross-shard query routing, and rebalancing operations for databases that have outgrown single-node capacity.

## Prerequisites

- Database admin credentials with CREATE DATABASE, CREATE TABLE, and replication permissions
- `psql`, `mysql`, or `mongosh` CLI tools installed and configured
- Network connectivity between all shard nodes
- Current table sizes and growth rate data (query `pg_total_relation_size` or `information_schema.TABLES`)
- Application query patterns documented or access to slow query logs
- Enough disk and memory on target shard nodes to handle redistributed data

## Instructions

1. Analyze the current database size and identify tables exceeding single-node capacity thresholds (typically >500GB or >1B rows). Run `SELECT pg_size_pretty(pg_total_relation_size('table_name'))` for PostgreSQL or `SELECT data_length + index_length FROM information_schema.TABLES` for MySQL.

2. Evaluate candidate shard keys by examining query WHERE clauses, JOIN patterns, and data distribution. A good shard key has high cardinality, even distribution, and appears in most queries. Run `SELECT shard_key_column, COUNT(*) FROM table GROUP BY shard_key_column ORDER BY COUNT(*) DESC LIMIT 20` to check distribution.

3. Choose a sharding strategy based on workload patterns:
   - **Hash-based**: Even distribution, best for key-value lookups. Use `hash(shard_key) % num_shards`.
   - **Range-based**: Good for time-series or sequential data. Partition by date ranges or ID ranges.
   - **Directory-based**: Maximum flexibility with a lookup table mapping keys to shards.
   - **Geographic**: Route by region for data residency or latency requirements.

4. Design the shard topology by determining the number of shards, replication factor, and placement. For PostgreSQL, use Citus extension or manual foreign data wrappers. For MySQL, configure vitess or ProxySQL routing. For MongoDB, enable sharding on the cluster with `sh.enableSharding()` and `sh.shardCollection()`.

5. Create the shard schema on all target nodes, ensuring identical table definitions, indexes, and constraints across every shard. Generate DDL scripts and verify with checksums.

6. Implement the routing layer that directs queries to the correct shard. This can be application-level (connection selection based on shard key), middleware (ProxySQL, PgBouncer with routing), or database-native (Citus, MongoDB mongos).

7. Migrate existing data to shards using batch operations. Extract data in chunks of 10,000-50,000 rows, transform shard key assignments, and load into target shards. Verify row counts match after migration.

8. Validate cross-shard queries work correctly, especially aggregations and JOINs that span multiple shards. Test scatter-gather query performance and implement application-level aggregation where needed.

9. Set up monitoring for shard balance (data size per shard, query load per shard) and configure alerts for skew exceeding 20% deviation from the average.

10. Document the shard map, routing logic, and rebalancing procedures for operational runbooks.

## Output

- **Shard key analysis report** with cardinality, distribution histograms, and recommended key selection
- **Shard topology diagram** mapping databases, tables, and key ranges to physical nodes
- **DDL migration scripts** for creating shard schemas with matching indexes and constraints
- **Routing configuration** files for ProxySQL, Citus, vitess, or application-level routing
- **Data migration scripts** with batch extraction, transformation, and verification queries
- **Monitoring queries** for shard balance, cross-shard query latency, and hotspot detection

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Hotspot shard receiving disproportionate traffic | Poor shard key choice with low cardinality or skewed distribution | Re-analyze shard key distribution; consider compound shard keys or hash-based sharding |
| Cross-shard JOIN timeout | Scatter-gather query across too many shards | Denormalize frequently joined data onto the same shard; use application-level aggregation |
| Shard rebalancing data loss | Migration interrupted mid-batch without transaction wrapping | Wrap batch migrations in transactions; verify source and destination row counts before deleting source data |
| Connection pool exhaustion | Each shard requires its own connection pool, multiplying total connections | Reduce per-shard pool size; use connection multiplexing with PgBouncer or ProxySQL |
| Schema drift between shards | DDL changes applied to some shards but not others | Use centralized DDL deployment scripts; verify schema checksums across all shards after changes |

## Examples

**E-commerce order table sharding by customer_id**: A 2TB orders table with 800M rows is sharded across 8 nodes using hash-based distribution on `customer_id`. All queries for a single customer hit one shard. Cross-customer analytics queries use a separate read replica with full data.

**Time-series IoT data with range sharding**: Sensor readings partitioned by month into separate shards. Each shard holds one month of data. Queries for recent data hit the active shard; historical analysis queries span multiple shards with parallel execution. Old shards are archived to cold storage quarterly.

**Multi-tenant SaaS with directory-based sharding**: A tenant-to-shard lookup table routes each tenant to a dedicated shard. Large tenants get dedicated shards; small tenants share shards. Rebalancing moves tenants between shards by updating the directory and migrating data.

## Resources

- PostgreSQL Citus documentation: https://docs.citusdata.com/
- MySQL Vitess documentation: https://vitess.io/docs/
- MongoDB Sharding guide: https://www.mongodb.com/docs/manual/sharding/
- ProxySQL query routing: https://proxysql.com/documentation/
- Shard key design patterns: https://www.mongodb.com/docs/manual/core/sharding-choose-a-shard-key/