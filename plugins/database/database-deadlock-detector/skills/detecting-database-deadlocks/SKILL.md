---
name: detecting-database-deadlocks
description: |
  Process use when you need to work with deadlock detection.
  This skill provides deadlock detection and resolution with comprehensive guidance and automation.
  Trigger with phrases like "detect deadlocks", "resolve deadlocks",
  or "prevent deadlocks".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Deadlock Detector

## Overview

Detect, analyze, and prevent database deadlocks in PostgreSQL, MySQL, and MongoDB by examining lock wait graphs, parsing deadlock log entries, identifying the application code paths that cause lock ordering conflicts, and implementing preventive patterns.

## Prerequisites

- Database credentials with access to lock monitoring views (`pg_locks`, `INNODB_LOCK_WAITS`)
- `psql` or `mysql` CLI for executing diagnostic queries
- PostgreSQL: `log_lock_waits = on` and `deadlock_timeout = 1s` configured
- MySQL: `innodb_print_all_deadlocks = ON` for deadlock logging to error log
- Access to database error logs for deadlock event parsing
- Application source code access for identifying lock-inducing code paths

## Instructions

1. Check for currently blocked transactions and their blockers:
   - PostgreSQL: `SELECT blocked.pid AS blocked_pid, blocked.query AS blocked_query, blocking.pid AS blocking_pid, blocking.query AS blocking_query FROM pg_stat_activity blocked JOIN pg_locks bl ON bl.pid = blocked.pid JOIN pg_locks bl2 ON bl2.locktype = bl.locktype AND bl2.relation = bl.relation AND bl2.pid != bl.pid JOIN pg_stat_activity blocking ON blocking.pid = bl2.pid WHERE NOT bl.granted`
   - MySQL: `SELECT * FROM information_schema.INNODB_LOCK_WAITS`

2. Parse recent deadlock events from database logs:
   - PostgreSQL: Search logs for `ERROR: deadlock detected` entries, which include the two conflicting queries and the lock types
   - MySQL: Run `SHOW ENGINE INNODB STATUS\G` and examine the `LATEST DETECTED DEADLOCK` section
   - Extract: transaction IDs, queries involved, tables and rows locked, and which transaction was rolled back

3. Construct the lock wait graph from the deadlock log. Map which transaction held which lock and which lock each transaction was waiting for. The circular dependency reveals the deadlock cycle. Identify the specific rows or index ranges involved.

4. Trace the deadlocking queries back to application code. Use Grep to find the SQL statements in the codebase and identify the transaction boundaries (`BEGIN`/`COMMIT` blocks or ORM transaction decorators). Map the full sequence of operations within each transaction.

5. Identify the root cause pattern:
   - **Opposite lock ordering**: Transaction A locks row 1 then row 2; Transaction B locks row 2 then row 1. Fix by ensuring consistent lock ordering.
   - **Index gap locks (MySQL)**: UPDATE/DELETE on non-existent rows creates gap locks that conflict. Fix by adding the target row first or using `READ COMMITTED` isolation.
   - **Foreign key lock escalation**: INSERT into child table acquires shared lock on parent row, conflicting with UPDATE on parent. Fix by locking parent first explicitly.
   - **Implicit lock promotion**: SELECT with FOR UPDATE followed by UPDATE promotes shared to exclusive lock. Fix by acquiring the exclusive lock upfront.

6. Implement deadlock prevention strategies:
   - Enforce consistent lock ordering: always lock tables/rows in alphabetical or ID order within transactions
   - Minimize transaction duration: move non-database operations (API calls, file I/O) outside the transaction
   - Use `SELECT ... FOR UPDATE NOWAIT` or `SKIP LOCKED` to fail fast instead of waiting
   - Reduce transaction isolation level from SERIALIZABLE to READ COMMITTED where possible

7. Add retry logic for deadlock victims. When the database aborts a transaction due to deadlock, catch the error (PostgreSQL error code `40P01`, MySQL error code `1213`) and retry the entire transaction up to 3 times with a short random delay.

8. Monitor deadlock frequency over time. Create a query or script that counts deadlock events per hour from the database logs. Alert when deadlock frequency exceeds the baseline by more than 3x.

9. For persistent deadlocks on specific tables, consider advisory locks (`pg_advisory_lock()` in PostgreSQL) to serialize access to contended resources at the application level, avoiding database-level lock contention entirely.

10. Document all identified deadlock patterns, root causes, and fixes in a deadlock analysis report for the development team.

## Output

- **Lock wait graph visualization** showing the circular dependency between transactions
- **Deadlock analysis report** with root cause, affected queries, and code paths
- **Code fix recommendations** with before/after transaction ordering examples
- **Retry logic implementation** for deadlock victim transactions
- **Monitoring queries/scripts** for tracking deadlock frequency trends

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| PostgreSQL error `40P01: deadlock detected` | Circular lock dependency between transactions | Implement retry logic; fix lock ordering in application code; reduce transaction scope |
| MySQL error `1213: Deadlock found when trying to get lock` | InnoDB detected circular wait in lock wait graph | Enable `innodb_print_all_deadlocks`; analyze `SHOW ENGINE INNODB STATUS`; implement retry logic |
| Lock wait timeout (not deadlock) | Transaction holding lock too long, exceeding `lock_wait_timeout` | Investigate the blocking transaction; increase timeout or implement NOWAIT; optimize the long-running transaction |
| Phantom deadlocks in monitoring | Transient lock waits resolved before deadlock detection runs | Increase monitoring frequency; use database deadlock log instead of snapshot queries; set `deadlock_timeout` lower |
| Deadlock frequency increases after schema change | New index or constraint creates additional lock targets | Analyze new lock patterns with `EXPLAIN` and `pg_locks`; adjust transaction scope to avoid locking new index entries |

## Examples

**Classic opposite-ordering deadlock in an order processing system**: Transaction A processes order 100 (locks order row), then updates inventory for product 50 (waits for inventory lock). Transaction B processes order 200 with product 50 (locks inventory row), then updates order 100 status (waits for order lock). Fix: always lock inventory first, then order, regardless of the business flow.

**MySQL gap lock deadlock on a queue table**: Two workers concurrently `DELETE FROM job_queue WHERE status = 'pending' LIMIT 1`. InnoDB gap locks on the index range conflict even though the workers target different rows. Fix: use `SELECT ... FOR UPDATE SKIP LOCKED` to skip already-locked rows, or add unique job IDs and target specific rows.

**Foreign key deadlock between parent and child inserts**: Concurrent transactions inserting into `order_items` (child) acquire shared locks on `orders` (parent) for FK validation. A third transaction updating `orders` requires an exclusive lock and deadlocks with the shared FK locks. Fix: explicitly `SELECT ... FOR UPDATE` on the parent order row before inserting child items.

## Resources

- PostgreSQL deadlock detection: https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-DEADLOCKS
- MySQL InnoDB deadlocks: https://dev.mysql.com/doc/refman/8.0/en/innodb-deadlocks.html
- PostgreSQL lock monitoring: https://wiki.postgresql.org/wiki/Lock_Monitoring
- Advisory locks in PostgreSQL: https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS
- InnoDB lock types explained: https://dev.mysql.com/doc/refman/8.0/en/innodb-locking.html