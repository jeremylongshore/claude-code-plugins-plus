---
name: managing-database-replication
description: |
  Process use when you need to work with database scalability.
  This skill provides replication and sharding with comprehensive guidance and automation.
  Trigger with phrases like "set up replication", "implement sharding",
  or "scale database".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Replication Manager

## Overview

Configure and manage database replication topologies for PostgreSQL (streaming replication, logical replication), MySQL (source-replica, group replication), and MongoDB (replica sets). This skill covers primary-replica setup, read scaling through replica routing, failover automation, replication lag monitoring, and conflict resolution for multi-primary configurations.

## Prerequisites

- Superuser or replication-role credentials on primary and replica servers
- Network connectivity between all replication nodes (verify with `pg_isready` or `mysqladmin ping`)
- `psql`, `mysql`, or `mongosh` CLI tools installed on all nodes
- Matching major database versions across all replication nodes
- Sufficient disk space on replicas (equal to or greater than primary)
- SSH access to replica servers for initial base backup transfer

## Instructions

1. Choose the replication topology based on requirements:
   - **Single primary + read replicas**: Best for read-heavy workloads. All writes go to primary; reads distributed across replicas.
   - **Multi-primary (active-active)**: Best for geographic distribution. Requires conflict resolution. Use PostgreSQL logical replication or MySQL Group Replication.
   - **Cascading replication**: Replica A replicates from primary, Replica B replicates from Replica A. Reduces primary load for many replicas.

2. For PostgreSQL streaming replication, configure the primary:
   - Set `wal_level = replica`, `max_wal_senders = 10`, `max_replication_slots = 10`
   - Create replication user: `CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'secure_password'`
   - Add replication entry to `pg_hba.conf`: `host replication replicator replica_ip/32 scram-sha-256`
   - Reload configuration: `SELECT pg_reload_conf()`

3. Initialize the replica with a base backup: `pg_basebackup -h primary_host -U replicator -D /var/lib/postgresql/data -Fp -Xs -P -R`. The `-R` flag creates `standby.signal` and configures `primary_conninfo` automatically.

4. For MySQL source-replica replication, configure the source:
   - Set `server-id = 1`, `log_bin = mysql-bin`, `binlog_format = ROW`
   - Create replication user: `CREATE USER 'replicator'@'replica_ip' IDENTIFIED BY 'secure_password'; GRANT REPLICATION SLAVE ON *.* TO 'replicator'@'replica_ip'`
   - Record binary log position: `SHOW MASTER STATUS`

5. Configure the MySQL replica: `CHANGE REPLICATION SOURCE TO SOURCE_HOST='primary_host', SOURCE_USER='replicator', SOURCE_PASSWORD='...', SOURCE_LOG_FILE='mysql-bin.000001', SOURCE_LOG_POS=154; START REPLICA`.

6. For MongoDB replica sets: initialize with `rs.initiate({_id: "rs0", members: [{_id: 0, host: "node1:27017"}, {_id: 1, host: "node2:27017"}, {_id: 2, host: "node3:27017"}]})`. MongoDB handles leader election and failover automatically.

7. Monitor replication lag continuously:
   - PostgreSQL: `SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn, (sent_lsn - replay_lsn) AS lag_bytes FROM pg_stat_replication`
   - MySQL: `SHOW REPLICA STATUS\G` (check `Seconds_Behind_Source`)
   - MongoDB: `rs.printReplicationInfo()` and `rs.printSecondaryReplicationInfo()`

8. Configure application-level read routing: direct write queries to the primary connection and read queries to a load-balanced replica pool. Use connection poolers (PgBouncer, ProxySQL) or application middleware for automatic routing.

9. Set up automated failover using Patroni (PostgreSQL), MySQL InnoDB Cluster + MySQL Router, or MongoDB's built-in election mechanism. Test failover by stopping the primary and verifying the replica promotes automatically within the target RTO.

10. Configure alerting for replication lag exceeding 10 seconds, replication slot inactive for more than 1 hour, and replica connection drops. Stale replication slots in PostgreSQL cause WAL accumulation and can fill the disk.

## Output

- **Replication configuration files** for primary and replica nodes
- **Base backup and initialization scripts** for setting up new replicas
- **Replication monitoring queries** with lag measurement and health checks
- **Failover runbook** with manual and automated promotion procedures
- **Read routing configuration** for application or connection pooler

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Replication lag increasing steadily | Replica cannot keep up with primary write volume | Check replica I/O and CPU; increase `max_parallel_workers` on replica; consider upgrading replica hardware; reduce write-heavy batch operations on primary |
| `replication slot is inactive` warning | Replica disconnected or paused, WAL accumulating on primary | Reconnect replica; if permanently removed, drop the slot with `SELECT pg_drop_replication_slot('slot_name')` to prevent disk fill |
| `could not connect to primary` on replica | Network partition, primary down, or authentication failure | Verify network connectivity; check `pg_hba.conf` entries; confirm replication user credentials; check primary process status |
| Replica has diverged from primary | Split-brain after failed failover or manual writes to replica | Re-initialize replica from fresh base backup; for PostgreSQL, use `pg_rewind` if timeline divergence is small |
| Conflict in logical replication | Same row modified on both publisher and subscriber | Configure conflict resolution policy; use `UPDATE` conflict handler; design schema to avoid cross-node writes to same rows |

## Examples

**Setting up PostgreSQL read replicas for a web application**: A primary database handles 2,000 writes/second but read traffic is 10x higher. Two streaming replicas are added with PgBouncer routing read queries to replicas in round-robin. Result: primary CPU drops from 90% to 40%, read latency improves by 60%.

**Automated failover with Patroni**: A 3-node PostgreSQL cluster managed by Patroni with etcd for consensus. When the primary fails, Patroni promotes the most up-to-date replica within 10 seconds. Application reconnects automatically through the Patroni-managed VIP or DNS endpoint.

**Cross-region logical replication for compliance**: EU customer data must stay in EU region. Logical replication publishes only non-PII tables to the US region replica. EU application reads locally; US analytics queries use the replicated subset. Publication filter: `CREATE PUBLICATION us_analytics FOR TABLE orders, products, categories`.

## Resources

- PostgreSQL streaming replication: https://www.postgresql.org/docs/current/warm-standby.html
- PostgreSQL logical replication: https://www.postgresql.org/docs/current/logical-replication.html
- MySQL replication: https://dev.mysql.com/doc/refman/8.0/en/replication.html
- Patroni (PostgreSQL HA): https://patroni.readthedocs.io/
- MongoDB replica sets: https://www.mongodb.com/docs/manual/replication/
