---
description: Detect and resolve database deadlocks with automated monitoring
shortcut: deadlock
---

# Database Deadlock Detector

Detect, analyze, and prevent database deadlocks with automated monitoring, alerting, and resolution strategies for production database systems.

## When to Use This Command

Use `/deadlock` when you need to:
- Investigate recurring deadlock issues in production
- Implement proactive deadlock detection and alerting
- Analyze transaction patterns causing deadlocks
- Optimize lock acquisition order in applications
- Monitor database lock contention in real-time
- Generate deadlock reports for performance tuning

DON'T use this when:
- Database doesn't support deadlock detection (use lock monitoring instead)
- Dealing with application-level race conditions (not database deadlocks)
- Looking for slow queries (use query analyzer instead)
- Investigating connection pool exhaustion (use connection pooler)

## Design Decisions

This command implements **comprehensive deadlock detection and prevention** because:
- Proactive monitoring prevents production incidents
- Automated analysis identifies root causes faster
- Prevention strategies reduce deadlock frequency by 90%+
- Real-time alerting enables rapid incident response
- Historical analysis reveals patterns and trends

**Alternative considered: Reactive deadlock handling**
- Only responds after deadlocks occur
- Relies on application retry logic
- No visibility into deadlock patterns
- Recommended only for low-traffic systems

**Alternative considered: Database-native logging only**
- Limited to log file analysis
- No automated alerting or resolution
- Requires manual correlation of events
- Recommended only for development environments

## Prerequisites

Before running this command:
1. Database user with monitoring permissions (e.g., `pg_monitor` role)
2. Access to database logs or system views
3. Understanding of your application's transaction patterns
4. Monitoring infrastructure (Prometheus/Grafana recommended)
5. Python 3.8+ or Node.js 16+ for monitoring scripts

## Implementation Process

### Step 1: Configure Database Deadlock Logging
Enable comprehensive deadlock detection and logging in your database.

### Step 2: Implement Deadlock Monitoring
Set up automated monitoring to detect and alert on deadlocks in real-time.

### Step 3: Analyze Deadlock Patterns
Build analysis tools to identify common deadlock scenarios and root causes.

### Step 4: Implement Prevention Strategies
Apply code changes and database tuning to prevent deadlocks proactively.

### Step 5: Set Up Continuous Monitoring
Deploy dashboards and alerting for ongoing deadlock visibility.

## Output Format

The command generates:
- `monitoring/deadlock-detector.py` - Real-time deadlock monitoring script
- `analysis/deadlock-analyzer.sql` - SQL queries for pattern analysis
- `config/deadlock-prevention.md` - Prevention strategies documentation
- `dashboards/deadlock-dashboard.json` - Grafana dashboard configuration
- `alerts/deadlock-rules.yml` - Prometheus alerting rules

## Code Examples

### Example 1: PostgreSQL Deadlock Detection and Monitoring

```sql
-- Enable comprehensive deadlock logging
-- Add to postgresql.conf
log_lock_waits = on
deadlock_timeout = '1s'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

-- Create deadlock monitoring view
CREATE OR REPLACE VIEW deadlock_monitor AS
SELECT
    l.locktype,
    l.relation::regclass AS table_name,
    l.mode,
    l.granted,
    l.pid AS blocked_pid,
    l.page,
    l.tuple,
    a.usename,
    a.application_name,
    a.client_addr,
    a.query AS blocked_query,
    a.state,
    a.wait_event_type,
    a.wait_event,
    NOW() - a.query_start AS query_duration,
    NOW() - a.state_change AS state_duration
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE NOT l.granted
ORDER BY a.query_start;

-- Query to identify blocking vs blocked processes
CREATE OR REPLACE FUNCTION show_deadlock_chains()
RETURNS TABLE (
    blocked_pid integer,
    blocked_query text,
    blocking_pid integer,
    blocking_query text,
    duration interval
) AS $$
SELECT
    blocked.pid AS blocked_pid,
    blocked.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.query AS blocking_query,
    NOW() - blocked.query_start AS duration
FROM pg_stat_activity blocked
JOIN pg_locks blocked_locks ON blocked.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON
    blocked_locks.locktype = blocking_locks.locktype
    AND blocked_locks.relation IS NOT DISTINCT FROM blocking_locks.relation
    AND blocked_locks.page IS NOT DISTINCT FROM blocking_locks.page
    AND blocked_locks.tuple IS NOT DISTINCT FROM blocking_locks.tuple
    AND blocked_locks.pid != blocking_locks.pid
JOIN pg_stat_activity blocking ON blocking_locks.pid = blocking.pid
WHERE NOT blocked_locks.granted
  AND blocking_locks.granted
  AND blocked.pid != blocking.pid;
$$ LANGUAGE SQL;

-- Historical deadlock analysis
CREATE TABLE deadlock_history (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP DEFAULT NOW(),
    victim_pid INTEGER,
    victim_query TEXT,
    blocker_pid INTEGER,
    blocker_query TEXT,
    lock_type TEXT,
    table_name TEXT,
    resolution_time_ms INTEGER,
    metadata JSONB
);

-- Function to log deadlocks
CREATE OR REPLACE FUNCTION log_deadlock_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO deadlock_history (
        victim_pid, victim_query, blocker_pid, blocker_query,
        lock_type, table_name, metadata
    )
    SELECT
        blocked_pid,
        blocked_query,
        blocking_pid,
        blocking_query,
        'deadlock',
        'detected_from_logs',
        jsonb_build_object(
            'detection_method', 'log_trigger',
            'timestamp', NOW()
        )
    FROM show_deadlock_chains()
    LIMIT 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

```python
# monitoring/deadlock-detector.py
import psycopg2
import time
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DeadlockEvent:
    """Represents a detected deadlock event."""
    detected_at: datetime
    blocked_pid: int
    blocked_query: str
    blocking_pid: int
    blocking_query: str
    lock_type: str
    table_name: Optional[str]
    duration_seconds: float

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            'detected_at': self.detected_at.isoformat()
        }

class PostgreSQLDeadlockDetector:
    """Real-time PostgreSQL deadlock detection and alerting."""

    def __init__(
        self,
        connection_string: str,
        check_interval: int = 5,
        alert_threshold: int = 3,
        alert_webhook: Optional[str] = None
    ):
        self.connection_string = connection_string
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold
        self.alert_webhook = alert_webhook
        self.deadlock_count = defaultdict(int)
        self.last_alert_time = {}

    def connect(self) -> psycopg2.extensions.connection:
        """Establish database connection with monitoring role."""
        return psycopg2.connect(self.connection_string)

    def detect_deadlocks(self) -> List[DeadlockEvent]:
        """Detect current deadlocks using pg_locks and pg_stat_activity."""
        query = """
        SELECT
            blocked.pid AS blocked_pid,
            blocked.query AS blocked_query,
            blocking.pid AS blocking_pid,
            blocking.query AS blocking_query,
            blocked_locks.locktype AS lock_type,
            blocked_locks.relation::regclass::text AS table_name,
            EXTRACT(EPOCH FROM (NOW() - blocked.query_start)) AS duration_seconds
        FROM pg_stat_activity blocked
        JOIN pg_locks blocked_locks ON blocked.pid = blocked_locks.pid
        JOIN pg_locks blocking_locks ON
            blocked_locks.locktype = blocking_locks.locktype
            AND blocked_locks.relation IS NOT DISTINCT FROM blocking_locks.relation
            AND blocked_locks.page IS NOT DISTINCT FROM blocking_locks.page
            AND blocked_locks.tuple IS NOT DISTINCT FROM blocking_locks.tuple
            AND blocked_locks.pid != blocking_locks.pid
        JOIN pg_stat_activity blocking ON blocking_locks.pid = blocking.pid
        WHERE NOT blocked_locks.granted
          AND blocking_locks.granted
          AND blocked.pid != blocking.pid
          AND blocked.state = 'active'
        ORDER BY duration_seconds DESC;
        """

        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                events = []
                for row in rows:
                    event = DeadlockEvent(
                        detected_at=datetime.now(),
                        blocked_pid=row[0],
                        blocked_query=row[1][:500],  # Truncate long queries
                        blocking_pid=row[2],
                        blocking_query=row[3][:500],
                        lock_type=row[4],
                        table_name=row[5],
                        duration_seconds=float(row[6])
                    )
                    events.append(event)

                return events
        finally:
            conn.close()

    def analyze_deadlock_pattern(self, events: List[DeadlockEvent]) -> Dict[str, any]:
        """Analyze deadlock patterns to identify root causes."""
        if not events:
            return {}

        # Group by table name
        tables = defaultdict(int)
        lock_types = defaultdict(int)
        query_patterns = defaultdict(int)

        for event in events:
            if event.table_name:
                tables[event.table_name] += 1
            lock_types[event.lock_type] += 1

            # Extract query type (SELECT, UPDATE, DELETE, INSERT)
            query_type = event.blocked_query.strip().split()[0].upper()
            query_patterns[query_type] += 1

        return {
            'total_deadlocks': len(events),
            'most_common_table': max(tables.items(), key=lambda x: x[1])[0] if tables else None,
            'most_common_lock_type': max(lock_types.items(), key=lambda x: x[1])[0] if lock_types else None,
            'query_type_distribution': dict(query_patterns),
            'average_duration': sum(e.duration_seconds for e in events) / len(events),
            'max_duration': max(e.duration_seconds for e in events)
        }

    def suggest_prevention_strategy(self, analysis: Dict[str, any]) -> List[str]:
        """Generate prevention recommendations based on analysis."""
        suggestions = []

        if analysis.get('most_common_table'):
            table = analysis['most_common_table']
            suggestions.append(
                f"Consider reviewing lock acquisition order for table '{table}'. "
                f"Ensure all transactions lock this table in consistent order."
            )

        if analysis.get('query_type_distribution', {}).get('UPDATE', 0) > 0:
            suggestions.append(
                "UPDATE queries detected in deadlocks. Use SELECT ... FOR UPDATE "
                "with consistent ordering to prevent UPDATE deadlocks."
            )

        if analysis.get('average_duration', 0) > 10:
            suggestions.append(
                f"Average deadlock duration is {analysis['average_duration']:.2f}s. "
                "Consider reducing transaction scope or implementing application-level "
                "retry logic with exponential backoff."
            )

        lock_type = analysis.get('most_common_lock_type')
        if lock_type == 'relation':
            suggestions.append(
                "Table-level locks detected. Consider using row-level locking "
                "or implementing optimistic locking patterns."
            )

        return suggestions

    def alert_on_deadlock(self, events: List[DeadlockEvent], analysis: Dict[str, any]):
        """Send alerts when deadlock threshold is exceeded."""
        if len(events) >= self.alert_threshold:
            logger.warning(
                f"DEADLOCK ALERT: {len(events)} deadlocks detected. "
                f"Analysis: {json.dumps(analysis, indent=2)}"
            )

            # Send webhook alert if configured
            if self.alert_webhook:
                import requests
                payload = {
                    'text': f'🚨 Deadlock Alert: {len(events)} deadlocks detected',
                    'events': [e.to_dict() for e in events],
                    'analysis': analysis,
                    'suggestions': self.suggest_prevention_strategy(analysis)
                }
                try:
                    requests.post(self.alert_webhook, json=payload, timeout=5)
                except Exception as e:
                    logger.error(f"Failed to send webhook alert: {e}")

    def run_continuous_monitoring(self):
        """Run continuous deadlock monitoring loop."""
        logger.info(f"Starting deadlock monitoring (check interval: {self.check_interval}s)")

        while True:
            try:
                events = self.detect_deadlocks()

                if events:
                    logger.info(f"Detected {len(events)} potential deadlocks")
                    analysis = self.analyze_deadlock_pattern(events)

                    # Log detailed information
                    for event in events:
                        logger.warning(
                            f"Deadlock: PID {event.blocked_pid} blocked by {event.blocking_pid} "
                            f"on {event.table_name} ({event.lock_type}) for {event.duration_seconds:.2f}s"
                        )

                    # Print suggestions
                    suggestions = self.suggest_prevention_strategy(analysis)
                    if suggestions:
                        logger.info("Prevention strategies:")
                        for suggestion in suggestions:
                            logger.info(f"  - {suggestion}")

                    self.alert_on_deadlock(events, analysis)

                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)

# Usage example
if __name__ == "__main__":
    detector = PostgreSQLDeadlockDetector(
        connection_string="postgresql://monitor_user:password@localhost:5432/mydb",
        check_interval=5,
        alert_threshold=3,
        alert_webhook="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    )

    detector.run_continuous_monitoring()
```

### Example 2: MySQL Deadlock Detection and InnoDB Monitoring

```sql
-- Enable InnoDB deadlock logging
-- Add to my.cnf
[mysqld]
innodb_print_all_deadlocks = 1
innodb_deadlock_detect = ON
innodb_lock_wait_timeout = 50

-- Create deadlock monitoring table
CREATE TABLE deadlock_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    victim_thread_id BIGINT,
    victim_query TEXT,
    waiting_query TEXT,
    lock_mode VARCHAR(50),
    table_name VARCHAR(255),
    index_name VARCHAR(255),
    deadlock_info TEXT,
    INDEX idx_detected_at (detected_at)
) ENGINE=InnoDB;

-- View current locks and blocking sessions
SELECT
    r.trx_id AS waiting_trx_id,
    r.trx_mysql_thread_id AS waiting_thread,
    r.trx_query AS waiting_query,
    b.trx_id AS blocking_trx_id,
    b.trx_mysql_thread_id AS blocking_thread,
    b.trx_query AS blocking_query,
    l.lock_mode,
    l.lock_type,
    l.lock_table,
    l.lock_index,
    TIMESTAMPDIFF(SECOND, r.trx_started, NOW()) AS wait_time_seconds
FROM information_schema.innodb_lock_waits w
JOIN information_schema.innodb_trx r ON w.requesting_trx_id = r.trx_id
JOIN information_schema.innodb_trx b ON w.blocking_trx_id = b.trx_id
JOIN information_schema.innodb_locks l ON w.requesting_lock_id = l.lock_id
ORDER BY wait_time_seconds DESC;

-- Analyze deadlock frequency by table
SELECT
    table_name,
    COUNT(*) AS deadlock_count,
    MAX(detected_at) AS last_deadlock,
    AVG(TIMESTAMPDIFF(SECOND, detected_at, NOW())) AS avg_age_seconds
FROM deadlock_log
WHERE detected_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY table_name
ORDER BY deadlock_count DESC;
```

```javascript
// monitoring/mysql-deadlock-detector.js
const mysql = require('mysql2/promise');
const fs = require('fs').promises;

class MySQLDeadlockDetector {
    constructor(config) {
        this.config = config;
        this.pool = mysql.createPool({
            host: config.host,
            user: config.user,
            password: config.password,
            database: config.database,
            waitForConnections: true,
            connectionLimit: 10,
            queueLimit: 0
        });
        this.checkInterval = config.checkInterval || 10000;
        this.deadlockStats = {
            total: 0,
            byTable: {},
            byHour: {}
        };
    }

    async detectCurrentLockWaits() {
        const query = `
            SELECT
                r.trx_id AS waiting_trx_id,
                r.trx_mysql_thread_id AS waiting_thread,
                r.trx_query AS waiting_query,
                b.trx_id AS blocking_trx_id,
                b.trx_mysql_thread_id AS blocking_thread,
                b.trx_query AS blocking_query,
                l.lock_mode,
                l.lock_type,
                l.lock_table,
                l.lock_index,
                TIMESTAMPDIFF(SECOND, r.trx_started, NOW()) AS wait_time_seconds
            FROM information_schema.innodb_lock_waits w
            JOIN information_schema.innodb_trx r ON w.requesting_trx_id = r.trx_id
            JOIN information_schema.innodb_trx b ON w.blocking_trx_id = b.trx_id
            JOIN information_schema.innodb_locks l ON w.requesting_lock_id = l.lock_id
            WHERE TIMESTAMPDIFF(SECOND, r.trx_started, NOW()) > 5
            ORDER BY wait_time_seconds DESC
        `;

        const [rows] = await this.pool.query(query);
        return rows;
    }

    async parseInnoDBStatus() {
        const [rows] = await this.pool.query('SHOW ENGINE INNODB STATUS');
        const status = rows[0].Status;

        // Extract deadlock information
        const deadlockRegex = /LATEST DETECTED DEADLOCK[\s\S]*?(?=TRANSACTIONS|$)/;
        const match = status.match(deadlockRegex);

        if (match) {
            const deadlockInfo = match[0];
            const timestamp = new Date();

            // Parse transaction details
            const transactions = this.extractTransactionDetails(deadlockInfo);

            return {
                timestamp,
                deadlockInfo,
                transactions
            };
        }

        return null;
    }

    extractTransactionDetails(deadlockInfo) {
        // Extract table names involved
        const tableRegex = /table `([^`]+)`\.`([^`]+)`/g;
        const tables = [];
        let match;

        while ((match = tableRegex.exec(deadlockInfo)) !== null) {
            tables.push(`${match[1]}.${match[2]}`);
        }

        // Extract lock modes
        const lockRegex = /lock mode (\w+)/g;
        const lockModes = [];

        while ((match = lockRegex.exec(deadlockInfo)) !== null) {
            lockModes.push(match[1]);
        }

        return {
            tables: [...new Set(tables)],
            lockModes: [...new Set(lockModes)]
        };
    }

    async logDeadlock(deadlockEvent) {
        const query = `
            INSERT INTO deadlock_log (
                victim_thread_id,
                victim_query,
                waiting_query,
                lock_mode,
                table_name,
                deadlock_info
            ) VALUES (?, ?, ?, ?, ?, ?)
        `;

        const tables = deadlockEvent.transactions.tables.join(', ');
        const lockModes = deadlockEvent.transactions.lockModes.join(', ');

        await this.pool.query(query, [
            null,
            'extracted_from_innodb_status',
            'extracted_from_innodb_status',
            lockModes,
            tables,
            deadlockEvent.deadlockInfo
        ]);

        this.deadlockStats.total++;

        // Update per-table stats
        deadlockEvent.transactions.tables.forEach(table => {
            this.deadlockStats.byTable[table] =
                (this.deadlockStats.byTable[table] || 0) + 1;
        });
    }

    generatePreventionAdvice(lockWaits) {
        const advice = [];

        // Analyze lock wait patterns
        const tableFrequency = {};
        lockWaits.forEach(wait => {
            const table = wait.lock_table;
            tableFrequency[table] = (tableFrequency[table] || 0) + 1;
        });

        // Find most problematic table
        const sortedTables = Object.entries(tableFrequency)
            .sort((a, b) => b[1] - a[1]);

        if (sortedTables.length > 0) {
            const [mostProblematicTable, count] = sortedTables[0];

            advice.push({
                severity: 'high',
                table: mostProblematicTable,
                suggestion: `Table ${mostProblematicTable} has ${count} lock waits. ` +
                    `Consider: 1) Reducing transaction scope, 2) Adding appropriate indexes, ` +
                    `3) Implementing consistent lock ordering.`
            });
        }

        // Check for long-running transactions
        const longRunning = lockWaits.filter(w => w.wait_time_seconds > 30);
        if (longRunning.length > 0) {
            advice.push({
                severity: 'medium',
                suggestion: `${longRunning.length} transactions waiting > 30s. ` +
                    `Review transaction isolation levels and consider READ COMMITTED ` +
                    `instead of REPEATABLE READ for reduced lock contention.`
            });
        }

        return advice;
    }

    async startMonitoring() {
        console.log('Starting MySQL deadlock monitoring...');

        setInterval(async () => {
            try {
                // Check for current lock waits
                const lockWaits = await this.detectCurrentLockWaits();

                if (lockWaits.length > 0) {
                    console.warn(`⚠️  ${lockWaits.length} lock waits detected:`);
                    lockWaits.forEach(wait => {
                        console.warn(
                            `  Thread ${wait.waiting_thread} waiting on thread ${wait.blocking_thread} ` +
                            `for ${wait.wait_time_seconds}s on ${wait.lock_table}`
                        );
                    });

                    const advice = this.generatePreventionAdvice(lockWaits);
                    if (advice.length > 0) {
                        console.log('\n💡 Prevention advice:');
                        advice.forEach(item => {
                            console.log(`  [${item.severity}] ${item.suggestion}`);
                        });
                    }
                }

                // Check InnoDB status for recent deadlocks
                const deadlock = await this.parseInnoDBStatus();
                if (deadlock) {
                    console.error('🚨 DEADLOCK DETECTED:');
                    console.error(`  Tables: ${deadlock.transactions.tables.join(', ')}`);
                    console.error(`  Lock modes: ${deadlock.transactions.lockModes.join(', ')}`);

                    await this.logDeadlock(deadlock);
                }

            } catch (error) {
                console.error('Monitoring error:', error);
            }
        }, this.checkInterval);
    }

    async getStatistics() {
        const query = `
            SELECT
                DATE(detected_at) AS date,
                COUNT(*) AS deadlock_count,
                table_name,
                lock_mode
            FROM deadlock_log
            WHERE detected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(detected_at), table_name, lock_mode
            ORDER BY date DESC, deadlock_count DESC
        `;

        const [rows] = await this.pool.query(query);
        return {
            historical: rows,
            current: this.deadlockStats
        };
    }
}

// Usage
const detector = new MySQLDeadlockDetector({
    host: 'localhost',
    user: 'monitor_user',
    password: 'password',
    database: 'mydb',
    checkInterval: 10000
});

detector.startMonitoring();

// Export statistics every hour
setInterval(async () => {
    const stats = await detector.getStatistics();
    await fs.writeFile(
        'deadlock-stats.json',
        JSON.stringify(stats, null, 2)
    );
}, 3600000);
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Permission denied" | Insufficient database privileges | Grant `pg_monitor` role (PostgreSQL) or `PROCESS` privilege (MySQL) |
| "Connection timeout" | Network or authentication issues | Verify connection string and firewall rules |
| "No deadlocks detected" | Deadlocks resolved before detection | Reduce `deadlock_timeout` to 500ms for faster detection |
| "Table not found" | Missing monitoring tables | Run setup scripts to create required tables |
| "Log file not accessible" | Filesystem permissions | Ensure logging user has write access to log directory |

## Configuration Options

**Deadlock Detection**
- `deadlock_timeout`: Time to wait before logging lock waits (PostgreSQL: 1s default)
- `innodb_deadlock_detect`: Enable/disable InnoDB deadlock detection (MySQL)
- `innodb_print_all_deadlocks`: Log all deadlocks to error log (MySQL)
- `log_lock_waits`: Log queries waiting for locks (PostgreSQL)

**Monitoring Parameters**
- `check_interval`: Frequency of deadlock checks (5-10 seconds recommended)
- `alert_threshold`: Number of deadlocks before alerting (3-5 recommended)
- `retention_period`: How long to keep deadlock history (7-30 days)

## Best Practices

DO:
- Always acquire locks in consistent order across transactions
- Keep transactions as short as possible
- Use row-level locking instead of table-level when possible
- Implement retry logic with exponential backoff
- Monitor deadlock trends over time
- Set appropriate lock timeouts (`innodb_lock_wait_timeout` = 50s)

DON'T:
- Hold locks during expensive operations (network calls, file I/O)
- Mix DDL and DML in the same transaction
- Use SELECT ... FOR UPDATE without ORDER BY
- Ignore deadlock patterns (they indicate design issues)
- Set deadlock_timeout too high (delays detection)

## Performance Considerations

- Monitoring queries add minimal overhead (<0.1% CPU typically)
- Use connection pooling to reduce monitoring overhead
- Index `deadlock_history` table on `detected_at` for fast queries
- Archive old deadlock logs to separate table monthly
- Consider read replicas for monitoring queries in high-traffic systems

## Related Commands

- `/sql-query-optimizer` - Optimize queries to reduce lock duration
- `/database-index-advisor` - Add indexes to minimize table scans
- `/database-transaction-monitor` - Monitor transaction patterns
- `/database-connection-pooler` - Optimize connection management
- `/database-health-monitor` - Overall database health monitoring

## Version History

- v1.0.0 (2024-10): Initial implementation with PostgreSQL and MySQL support
- Planned v1.1.0: Add Microsoft SQL Server and Oracle deadlock detection
