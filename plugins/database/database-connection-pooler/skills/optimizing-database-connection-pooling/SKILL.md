---
name: optimizing-database-connection-pooling
description: |
  Process use when you need to work with connection management.
  This skill provides connection pooling and management with comprehensive guidance and automation.
  Trigger with phrases like "manage connections", "configure pooling",
  or "optimize connection usage".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Connection Pooler

## Overview

Configure and optimize database connection pooling using external poolers (PgBouncer, ProxySQL, Odyssey) and application-level pool settings to prevent connection exhaustion, reduce connection overhead, and improve database throughput. This skill sizes connection pools correctly based on workload patterns, configures pool modes (session, transaction, statement), and diagnoses connection-related failures like pool exhaustion, idle connection waste, and connection storms.

## Prerequisites

- `psql` or `mysql` CLI for querying connection metrics
- Access to database configuration files (`postgresql.conf`, `my.cnf`) for `max_connections` settings
- PgBouncer, ProxySQL, or Odyssey installed if using external pooling
- Application connection pool settings accessible (database URL, pool size parameters)
- Server CPU core count and available memory for pool sizing calculations

## Instructions

1. Audit current connection usage by querying active connections:
   - PostgreSQL: `SELECT count(*) AS total, state, usename FROM pg_stat_activity GROUP BY state, usename ORDER BY total DESC`
   - MySQL: `SHOW STATUS LIKE 'Threads_connected'` and `SHOW PROCESSLIST`
   - Compare against `max_connections` setting to determine headroom

2. Calculate the optimal pool size using the formula: `pool_size = (core_count * 2) + effective_spindle_count`. For SSD-backed databases, use `core_count * 2 + 1`. A 4-core server with SSD storage should have a pool size of approximately 9. This formula applies per application instance.

3. Configure application-level connection pool parameters:
   - **minimumIdle**: Set to 2-5 for low-traffic periods (avoids cold-start latency)
   - **maximumPoolSize**: Set using the formula from step 2
   - **connectionTimeout**: 5-10 seconds (fail fast rather than queue indefinitely)
   - **idleTimeout**: 10-30 minutes (release idle connections back to pool)
   - **maxLifetime**: 30 minutes (prevent stale connections from accumulating)
   - **leakDetectionThreshold**: 60 seconds (log warning for connections held too long)

4. For PostgreSQL with many application instances, deploy PgBouncer in transaction pooling mode:
   - Set `pool_mode = transaction` to multiplex connections (one backend connection serves many clients between transactions)
   - Set `default_pool_size = 20` and `max_client_conn = 1000`
   - Configure `server_idle_timeout = 600` to close unused backend connections
   - Set `server_lifetime = 3600` to periodically refresh connections

5. For MySQL with many application instances, deploy ProxySQL:
   - Configure connection multiplexing in `mysql_servers` table
   - Set `max_connections` per backend server
   - Configure query rules for read/write splitting to replicas
   - Enable connection pooling with `free_connections_pct = 10`

6. Set `max_connections` in the database server based on available memory. Each PostgreSQL connection uses approximately 5-10MB of memory. For a server with 8GB RAM: `max_connections = (8192MB - 2048MB_for_OS - 2048MB_shared_buffers) / 10MB = ~400`. For MySQL, each thread uses approximately 1-4MB.

7. Implement connection health checks. Configure the pool to validate connections before lending (`testOnBorrow` or `validation-query`). Use a lightweight query: `SELECT 1` for MySQL or a simple query for PostgreSQL. Set validation interval to avoid excessive overhead.

8. Monitor connection pool metrics continuously:
   - Active connections vs. pool size (saturation indicator)
   - Wait time for connection acquisition (queuing indicator)
   - Connection creation rate (churn indicator)
   - Idle connection count (waste indicator)
   - Connection leak warnings (application bug indicator)

9. Handle connection storms (sudden spike in connection requests) by configuring a connection request queue with a bounded wait time, implementing retry with exponential backoff in the application, and pre-warming the pool during application startup.

10. Document the connection architecture: application pool size per instance, number of application instances, PgBouncer/ProxySQL settings, database `max_connections`, and the maximum theoretical connections formula (`instances * pool_size_per_instance`).

## Output

- **PgBouncer/ProxySQL configuration files** with optimized pool settings
- **Application pool configuration** with connection string and pool parameters
- **Connection sizing worksheet** documenting the calculation from cores to pool size
- **Monitoring queries** for connection metrics and health checks
- **Connection architecture diagram** showing application -> pooler -> database flow

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `FATAL: too many connections for role` | Application pool size exceeds `max_connections` or connection leak | Reduce pool size; fix connection leaks (enable leak detection); add PgBouncer for connection multiplexing |
| Connection timeout after 5 seconds | Pool exhausted, all connections in use | Increase pool size cautiously; check for long-running transactions holding connections; add connection queue with backpressure |
| `connection reset by peer` errors | Server-side idle timeout killed the connection | Set pool `maxLifetime` shorter than server `idle_in_transaction_session_timeout`; enable connection validation |
| PgBouncer `no more connections allowed` | `max_client_conn` exceeded | Increase `max_client_conn`; or reduce client connection demand; check for connection leaks in application |
| High connection churn (create/destroy rate) | Pool too small for workload or `maxLifetime` too short | Increase pool size; extend `maxLifetime` to 30 minutes; ensure `minimumIdle` is set to avoid constant pool resizing |

## Examples

**Right-sizing a pool for a Spring Boot microservice**: 4-core server, SSD storage, 3 microservice instances. Optimal pool per instance: `(4 * 2) + 1 = 9`. Total connections: `9 * 3 = 27`. Database `max_connections = 100` with comfortable headroom. Application startup pre-warms 5 connections per instance. Connection leak detection set to 60 seconds catches a missing `connection.close()` in an error handler.

**PgBouncer deployment for a serverless application**: Lambda functions create a new database connection per invocation, overwhelming PostgreSQL with 500+ connections. PgBouncer deployed between Lambda and PostgreSQL with `pool_mode = transaction`, `default_pool_size = 25`, `max_client_conn = 5000`. Lambda connects to PgBouncer; PgBouncer multiplexes to 25 backend connections. Connection errors eliminated; database CPU reduced from 95% to 30%.

**ProxySQL read/write splitting**: A MySQL application sends 80% reads and 20% writes. ProxySQL routes writes to the primary and distributes reads across 2 replicas. Connection pooling reduces backend connections from 300 (direct) to 60 (pooled). Average query latency drops from 8ms to 3ms due to reduced connection overhead.

## Resources

- PgBouncer documentation: https://www.pgbouncer.org/config.html
- ProxySQL documentation: https://proxysql.com/documentation/
- HikariCP pool sizing: https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing
- PostgreSQL connection management: https://www.postgresql.org/docs/current/runtime-config-connection.html
- Odyssey connection pooler: https://github.com/yandex/odyssey
