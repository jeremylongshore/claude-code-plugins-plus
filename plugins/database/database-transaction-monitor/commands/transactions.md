---
name: transactions
description: >
  Monitor database transactions with real-time alerting for performance
  and...
shortcut: txnm
---
# Database Transaction Monitor

Monitor database transaction performance, detect long-running transactions, identify lock contention, track rollback rates, and automatically alert on transaction anomalies for production database health.

## When to Use This Command

Use `/txn-monitor` when you need to:
- Detect and kill long-running transactions blocking other queries
- Monitor lock wait times and identify deadlock patterns
- Track transaction rollback rates for error analysis
- Alert on isolation level anomalies (phantom reads, dirty reads)
- Analyze transaction throughput and latency trends
- Investigate application connection leak issues

DON'T use this when:
- Database has minimal transaction load (<100 TPS)
- All transactions complete within milliseconds
- Looking for query optimization (use query optimizer instead)
- Investigating data corruption (use audit logger instead)

## Design Decisions

This command implements **real-time transaction monitoring with automated alerting** because:
- Long-running transactions (>30s) block other queries and cause performance degradation
- Lock contention detection prevents cascade failures
- Rollback rate monitoring identifies application bugs early
- Automatic alerts reduce MTTR (Mean Time To Resolution)
- Historical trend analysis enables capacity planning

**Alternative considered: Periodic manual checks**
- No automated alerting on issues
- Relies on humans checking dashboards
- Slower incident response
- Recommended only for development environments

**Alternative considered: Database log parsing**
- Post-mortem analysis only
- No real-time alerts
- Requires custom log parsing logic
- Recommended for compliance/audit purposes

## Prerequisites

Before running this command:
1. Database monitoring permissions (pg_monitor role or PROCESS privilege)
2. Access to pg_stat_activity (PostgreSQL) or performance_schema (MySQL)
3. Alerting infrastructure (Slack, PagerDuty, email)
4. Monitoring data retention strategy (metrics database or time-series DB)
5. Runbook for common transaction issues

## Implementation Process

### Step 1: Enable Transaction Monitoring
Configure database to track transaction statistics.

### Step 2: Build Real-Time Monitor
Create monitoring script that polls transaction statistics every 5-10 seconds.

### Step 3: Define Alert Thresholds
Set thresholds for long-running transactions, lock waits, and rollback rates.

### Step 4: Implement Automated Actions
Auto-kill transactions exceeding thresholds or alert operators.

### Step 5: Create Dashboards
Build Grafana dashboards for transaction metrics visualization.

## Output Format

The command generates:
- `monitoring/transaction_monitor.py` - Real-time transaction monitoring daemon
- `queries/transaction_analysis.sql` - Transaction health diagnostic queries
- `alerts/transaction_alerts.yml` - Prometheus alerting rules
- `dashboards/transaction_dashboard.json` - Grafana dashboard configuration
- `docs/transaction_runbook.md` - Incident response procedures

## Code Examples

### Example 1: PostgreSQL Real-Time Transaction Monitor

```python
# monitoring/postgres_transaction_monitor.py
import psycopg2
from psycopg2.extras import Dict Cursor
import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TransactionInfo:
    """Represents an active transaction."""
    pid: int
    username: str
    database: str
    application_name: str
    client_addr: str
    state: str
    query: str
    transaction_start: datetime
    query_start: datetime
    wait_event: Optional[str]
    blocking_pids: List[int]

    def duration_seconds(self) -> float:
        return (datetime.now() - self.transaction_start).total_seconds()

    def to_dict(self) -> dict:
        result = asdict(self)
        result['transaction_start'] = self.transaction_start.isoformat()
        result['query_start'] = self.query_start.isoformat()
        result['duration_seconds'] = self.duration_seconds()
        return result

class PostgreSQLTransactionMonitor:
    """Monitor PostgreSQL transactions in real-time."""

    def __init__(
        self,
        connection_string: str,
        long_transaction_threshold: int = 30,
        check_interval: int = 10
    ):
        self.conn_string = connection_string
        self.long_transaction_threshold = long_transaction_threshold
        self.check_interval = check_interval
        self.stats = {
            'total_transactions': 0,
            'long_running_count': 0,
            'blocked_count': 0,
            'idle_in_transaction_count': 0
        }

    def connect(self):
        return psycopg2.connect(self.conn_string, cursor_factory=DictCursor)

    def get_active_transactions(self) -> List[TransactionInfo]:
        """Fetch all active transactions with blocking information."""
        query = """
        SELECT
            a.pid,
            a.usename,
            a.datname AS database,
            a.application_name,
            a.client_addr::text,
            a.state,
            a.query,
            a.xact_start AS transaction_start,
            a.query_start,
            a.wait_event,
            array_agg(b.pid) FILTER (WHERE b.pid IS NOT NULL) AS blocking_pids
        FROM pg_stat_activity a
        LEFT JOIN pg_stat_activity b ON b.pid = ANY(pg_blocking_pids(a.pid))
        WHERE a.pid != pg_backend_pid()
          AND a.state != 'idle'
          AND a.xact_start IS NOT NULL
        GROUP BY a.pid, a.usename, a.datname, a.application_name,
                 a.client_addr, a.state, a.query, a.xact_start,
                 a.query_start, a.wait_event
        ORDER BY a.xact_start;
        """

        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                transactions = []
                for row in rows:
                    txn = TransactionInfo(
                        pid=row['pid'],
                        username=row['usename'],
                        database=row['database'],
                        application_name=row['application_name'] or 'unknown',
                        client_addr=row['client_addr'] or 'local',
                        state=row['state'],
                        query=row['query'][:200],  # Truncate long queries
                        transaction_start=row['transaction_start'],
                        query_start=row['query_start'],
                        wait_event=row['wait_event'],
                        blocking_pids=row['blocking_pids'] or []
                    )
                    transactions.append(txn)

                return transactions

        finally:
            conn.close()

    def find_long_running_transactions(
        self,
        transactions: List[TransactionInfo]
    ) -> List[TransactionInfo]:
        """Identify transactions exceeding threshold."""
        return [
            txn for txn in transactions
            if txn.duration_seconds() > self.long_transaction_threshold
        ]

    def find_blocked_transactions(
        self,
        transactions: List[TransactionInfo]
    ) -> List[TransactionInfo]:
        """Identify transactions waiting on locks."""
        return [
            txn for txn in transactions
            if txn.blocking_pids and len(txn.blocking_pids) > 0
        ]

    def find_idle_in_transaction(
        self,
        transactions: List[TransactionInfo]
    ) -> List[TransactionInfo]:
        """Find idle transactions holding locks."""
        return [
            txn for txn in transactions
            if txn.state == 'idle in transaction'
            and txn.duration_seconds() > 60
        ]

    def kill_transaction(self, pid: int, reason: str) -> bool:
        """Terminate a transaction by PID."""
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_terminate_backend(%s)", (pid,))
                success = cur.fetchone()[0]

                if success:
                    logger.warning(f"Killed transaction PID {pid}: {reason}")
                else:
                    logger.error(f"Failed to kill transaction PID {pid}")

                return success

        finally:
            conn.close()

    def get_transaction_stats(self) -> Dict[str, any]:
        """Get overall transaction statistics."""
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        (SELECT count(*) FROM pg_stat_activity WHERE state != 'idle') AS active_connections,
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction') AS idle_in_txn,
                        (SELECT sum(xact_commit) FROM pg_stat_database) AS total_commits,
                        (SELECT sum(xact_rollback) FROM pg_stat_database) AS total_rollbacks,
                        (SELECT sum(conflicts) FROM pg_stat_database_conflicts) AS conflicts
                """)

                row = cur.fetchone()

                total_txns = row['total_commits'] + row['total_rollbacks']
                rollback_rate = (row['total_rollbacks'] / total_txns * 100) if total_txns > 0 else 0

                return {
                    'active_connections': row['active_connections'],
                    'idle_in_transaction': row['idle_in_txn'],
                    'total_commits': row['total_commits'],
                    'total_rollbacks': row['total_rollbacks'],
                    'rollback_rate_percent': round(rollback_rate, 2),
                    'conflicts': row['conflicts']
                }

        finally:
            conn.close()

    def alert(self, severity: str, message: str, details: dict = None):
        """Send alert to monitoring system."""
        log_func = {
            'critical': logger.critical,
            'warning': logger.warning,
            'info': logger.info
        }.get(severity, logger.info)

        log_func(f"[{severity.upper()}] {message}")

        if details:
            logger.info(f"Details: {details}")

        # Implement webhook/email/PagerDuty integration here
        # Example: requests.post(webhook_url, json={'message': message, 'details': details})

    def run_monitoring_loop(self):
        """Main monitoring loop."""
        logger.info(f"Starting transaction monitoring (interval: {self.check_interval}s)")

        while True:
            try:
                # Fetch active transactions
                transactions = self.get_active_transactions()
                self.stats['total_transactions'] = len(transactions)

                # Check for long-running transactions
                long_running = self.find_long_running_transactions(transactions)
                if long_running:
                    self.stats['long_running_count'] = len(long_running)

                    for txn in long_running:
                        self.alert(
                            'warning',
                            f"Long-running transaction detected: PID {txn.pid}",
                            {
                                'duration': txn.duration_seconds(),
                                'database': txn.database,
                                'username': txn.username,
                                'query': txn.query
                            }
                        )

                        # Auto-kill if exceeds 5 minutes
                        if txn.duration_seconds() > 300:
                            self.kill_transaction(
                                txn.pid,
                                f"Exceeded 5 minute threshold ({txn.duration_seconds():.0f}s)"
                            )

                # Check for blocked transactions
                blocked = self.find_blocked_transactions(transactions)
                if blocked:
                    self.stats['blocked_count'] = len(blocked)

                    for txn in blocked:
                        self.alert(
                            'warning',
                            f"Blocked transaction: PID {txn.pid}",
                            {
                                'blocking_pids': txn.blocking_pids,
                                'wait_event': txn.wait_event,
                                'duration': txn.duration_seconds()
                            }
                        )

                # Check for idle in transaction
                idle_txns = self.find_idle_in_transaction(transactions)
                if idle_txns:
                    self.stats['idle_in_transaction_count'] = len(idle_txns)

                    for txn in idle_txns:
                        self.alert(
                            'warning',
                            f"Idle in transaction: PID {txn.pid}",
                            {
                                'duration': txn.duration_seconds(),
                                'application': txn.application_name
                            }
                        )

                        # Kill idle transactions after 10 minutes
                        if txn.duration_seconds() > 600:
                            self.kill_transaction(txn.pid, "Idle in transaction >10 minutes")

                # Get overall stats
                stats = self.get_transaction_stats()

                # Alert on high rollback rate
                if stats['rollback_rate_percent'] > 10:
                    self.alert(
                        'warning',
                        f"High transaction rollback rate: {stats['rollback_rate_percent']}%",
                        stats
                    )

                # Log periodic status
                logger.info(
                    f"Monitoring: {stats['active_connections']} active, "
                    f"{len(long_running)} long-running, "
                    f"{len(blocked)} blocked, "
                    f"{stats['rollback_rate_percent']}% rollback rate"
                )

                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(self.check_interval)

# Usage
if __name__ == "__main__":
    monitor = PostgreSQLTransactionMonitor(
        connection_string="postgresql://monitor_user:password@localhost:5432/mydb",
        long_transaction_threshold=30,  # 30 seconds
        check_interval=10  # Check every 10 seconds
    )

    monitor.run_monitoring_loop()
```

### Example 2: Transaction Analysis Queries

```sql
-- PostgreSQL transaction health diagnostic queries

-- 1. Long-running transactions
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    NOW() - xact_start AS transaction_duration,
    NOW() - query_start AS query_duration,
    state,
    LEFT(query, 100) AS query_snippet
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
  AND state != 'idle'
  AND pid != pg_backend_pid()
ORDER BY xact_start;

-- 2. Blocking tree (which transactions are blocking others)
WITH RECURSIVE blocking_tree AS (
    SELECT
        a.pid,
        a.usename,
        a.query AS blocked_query,
        NULL::integer AS blocking_pid,
        NULL::text AS blocking_query,
        1 AS level
    FROM pg_stat_activity a
    WHERE NOT EXISTS (
        SELECT 1 FROM pg_stat_activity b
        WHERE b.pid = ANY(pg_blocking_pids(a.pid))
    )
    AND a.pid IN (
        SELECT unnest(pg_blocking_pids(c.pid))
        FROM pg_stat_activity c
    )

    UNION ALL

    SELECT
        a.pid,
        a.usename,
        a.query,
        b.pid,
        b.query,
        bt.level + 1
    FROM blocking_tree bt
    JOIN pg_stat_activity a ON a.pid = ANY(
        SELECT unnest(pg_blocking_pids(x.pid))
        FROM pg_stat_activity x
        WHERE x.pid = bt.pid
    )
    JOIN pg_stat_activity b ON b.pid = ANY(pg_blocking_pids(a.pid))
)
SELECT
    level,
    pid,
    usename,
    blocking_pid,
    LEFT(blocked_query, 50) AS blocked_query,
    LEFT(blocking_query, 50) AS blocking_query
FROM blocking_tree
ORDER BY level, pid;

-- 3. Transaction rollback rate by database
SELECT
    datname,
    xact_commit AS commits,
    xact_rollback AS rollbacks,
    ROUND(100.0 * xact_rollback / NULLIF(xact_commit + xact_rollback, 0), 2) AS rollback_rate_percent
FROM pg_stat_database
WHERE datname NOT IN ('template0', 'template1', 'postgres')
ORDER BY rollback_rate_percent DESC;

-- 4. Idle in transaction connections
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    NOW() - state_change AS idle_duration,
    state,
    query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND pid != pg_backend_pid()
ORDER BY state_change;

-- 5. Lock wait time by query
SELECT
    wait_event_type,
    wait_event,
    COUNT(*) AS waiting_count,
    array_agg(DISTINCT pid) AS waiting_pids
FROM pg_stat_activity
WHERE wait_event IS NOT NULL
  AND state = 'active'
GROUP BY wait_event_type, wait_event
ORDER BY waiting_count DESC;
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Permission denied for pg_stat_activity" | Insufficient monitoring privileges | Grant pg_monitor role or SELECT on pg_stat_activity |
| "Cannot terminate backend" | Trying to kill superuser connection | Use pg_cancel_backend or kill from OS level |
| "Connection pool exhausted" | Too many idle connections | Kill idle in transaction connections, increase pool size |
| "High rollback rate" | Application errors or constraint violations | Review application logs and fix bugs |
| "Lock wait timeout exceeded" | Deadlock or very long lock hold | Analyze blocking queries, implement timeouts |

## Configuration Options

**Monitoring Intervals**
- `check_interval`: 5-10 seconds for real-time alerting
- `long_transaction_threshold`: 30-60 seconds (production), 300s (analytics)
- `idle_in_transaction_timeout`: 600 seconds (10 minutes)

**Auto-Kill Thresholds**
- Long-running OLTP: 60-300 seconds
- Long-running analytics: 3600 seconds (1 hour)
- Idle in transaction: 600 seconds (10 minutes)

**Alert Thresholds**
- Rollback rate: >5% warning, >10% critical
- Blocked transactions: >10 warning, >50 critical
- Active connections: >80% of max_connections

## Best Practices

DO:
- Set statement_timeout in application connection strings
- Use connection pooling to limit total connections
- Implement transaction timeout in application code
- Monitor transaction throughput trends over time
- Kill idle in transaction connections automatically
- Track rollback reasons in application logs

DON'T:
- Leave transactions open while waiting for user input
- Hold locks during expensive operations (file I/O, network calls)
- Use long-running transactions in OLTP workloads
- Ignore idle in transaction connections (they hold locks)
- Set transaction timeouts too low (causes false positives)

## Performance Considerations

- Monitoring adds <0.1% CPU overhead with 10-second intervals
- pg_stat_activity queries are lightweight (<1ms)
- Auto-killing transactions requires careful threshold tuning
- Historical metrics retention: 30 days (aggregated), 7 days (detailed)
- Consider read replicas for monitoring queries in high-load systems

## Related Commands

- `/database-deadlock-detector` - Detailed deadlock analysis
- `/database-health-monitor` - Overall database health metrics
- `/sql-query-optimizer` - Optimize slow queries causing lock contention
- `/database-connection-pooler` - Manage connection pool sizing

## Version History

- v1.0.0 (2024-10): Initial implementation with PostgreSQL real-time monitoring
- Planned v1.1.0: Add MySQL transaction monitoring and distributed transaction support
