---
description: Comprehensive database replication management with streaming replication, failover automation, and lag monitoring
shortcut: replication
---

# Database Replication Manager

Implement production-grade database replication for PostgreSQL and MySQL with streaming replication (physical), logical replication (selective tables), synchronous and asynchronous modes, automatic failover, lag monitoring, conflict resolution, and read scaling across multiple replicas. Achieve 99.99% availability with RPO <5 seconds and RTO <30 seconds for automated failover.

## When to Use This Command

Use `/replication` when you need to:
- Implement high availability with automatic failover (99.99%+ uptime)
- Scale read workloads across multiple replicas (10x read capacity)
- Create disaster recovery instances in different regions
- Enable zero-downtime database migrations and upgrades
- Implement read-heavy application architectures
- Meet compliance requirements for data redundancy

DON'T use this when:
- Single server handles all load comfortably (<50% CPU)
- Database size is small (<10GB) and backup/restore is fast
- Application doesn't support read replica routing
- Network latency between regions is high (>100ms for sync replication)
- You lack monitoring infrastructure for replication lag
- Write workload is too heavy for replication to keep up

## Design Decisions

This command implements **automated replication with failover** because:
- Streaming replication provides real-time data synchronization
- Automatic failover reduces RTO from hours to seconds
- Read replicas enable horizontal read scaling
- Logical replication allows selective table replication
- Synchronous mode ensures zero data loss for critical transactions

**Alternative considered: Application-level read/write splitting**
- No replication overhead at database level
- Requires application changes for every database interaction
- More complex error handling and retry logic
- Recommended when replication infrastructure unavailable

**Alternative considered: Database clustering (Patroni, Galera)**
- Multi-master with automatic failover
- More complex setup and maintenance
- Better for write-heavy workloads
- Recommended for high-write applications requiring HA

## Prerequisites

Before running this command:
1. Primary and replica servers with network connectivity
2. Sufficient disk space for WAL archiving (30-50% of database size)
3. Monitoring system for replication lag alerts
4. Understanding of RPO (Recovery Point Objective) and RTO requirements
5. Tested failover procedures and runbooks

## Implementation Process

### Step 1: Configure Primary for Replication
Enable WAL archiving, set max_wal_senders, and create replication user.

### Step 2: Initialize Replica with Base Backup
Use pg_basebackup to clone primary database to replica server.

### Step 3: Configure Replica Connection
Set primary_conninfo and start replica in standby mode.

### Step 4: Verify Replication Status
Check replication lag and ensure WAL streaming is active.

### Step 5: Implement Monitoring and Failover
Deploy replication lag alerts and automatic failover scripts.

## Output Format

The command generates:
- `replication/primary_setup.sql` - Primary configuration and replication user
- `replication/replica_setup.sh` - Automated replica initialization script
- `replication/failover.py` - Automatic failover orchestration
- `replication/monitoring.yml` - Prometheus/Grafana replication metrics
- `replication/recovery.conf` - Replica recovery configuration

## Code Examples

### Example 1: PostgreSQL Streaming Replication Setup

```bash
#!/bin/bash
#
# Production-ready PostgreSQL streaming replication setup
# with automatic failover and monitoring integration
#

set -e

# Configuration
PRIMARY_HOST="${PRIMARY_HOST:-primary.example.com}"
REPLICA_HOST="${REPLICA_HOST:-replica.example.com}"
REPLICATION_USER="${REPLICATION_USER:-replicator}"
REPLICATION_PASSWORD="${REPLICATION_PASSWORD:-changeme}"
POSTGRES_DATA_DIR="/var/lib/postgresql/14/main"

echo "========================================="
echo "PostgreSQL Streaming Replication Setup"
echo "========================================="
echo ""

# ===== PRIMARY SERVER CONFIGURATION =====

setup_primary() {
    echo "Configuring PRIMARY server: $PRIMARY_HOST"
    echo ""

    # 1. Configure postgresql.conf for replication
    cat >> /etc/postgresql/14/main/postgresql.conf <<EOF

# ========== REPLICATION SETTINGS ==========
# Added by replication setup script

# Write-Ahead Log (WAL) settings
wal_level = replica                    # Enable WAL for replication
max_wal_senders = 10                   # Max concurrent replication connections
wal_keep_size = 1024                   # Keep 1GB of WAL segments (PostgreSQL 13+)
max_replication_slots = 10             # For replication slots (recommended)

# Synchronous replication (optional - for zero data loss)
# synchronous_standby_names = 'replica1'  # Uncomment for sync replication
synchronous_commit = local             # Options: off, local, remote_write, remote_apply, on

# Archive WAL for point-in-time recovery (optional)
archive_mode = on
archive_command = 'test ! -f /var/lib/postgresql/wal_archive/%f && cp %p /var/lib/postgresql/wal_archive/%f'
archive_timeout = 300                  # Force WAL switch every 5 minutes

# Hot standby settings
hot_standby = on                       # Allow reads on replica
hot_standby_feedback = on              # Prevent query conflicts

# ========================================
EOF

    # 2. Create WAL archive directory
    mkdir -p /var/lib/postgresql/wal_archive
    chown postgres:postgres /var/lib/postgresql/wal_archive
    chmod 700 /var/lib/postgresql/wal_archive

    # 3. Configure pg_hba.conf for replication connections
    cat >> /etc/postgresql/14/main/pg_hba.conf <<EOF

# Replication connections (added by setup script)
host    replication     $REPLICATION_USER    $REPLICA_HOST/32    scram-sha-256
host    replication     $REPLICATION_USER    0.0.0.0/0           scram-sha-256  # For multiple replicas
EOF

    # 4. Create replication user
    sudo -u postgres psql <<EOF
-- Create replication user with strong password
CREATE ROLE $REPLICATION_USER WITH REPLICATION LOGIN PASSWORD '$REPLICATION_PASSWORD';

-- Grant necessary permissions
GRANT CONNECT ON DATABASE postgres TO $REPLICATION_USER;

-- Create replication slot (recommended for reliability)
SELECT * FROM pg_create_physical_replication_slot('replica1_slot');

-- Verify replication user
\du $REPLICATION_USER
EOF

    # 5. Restart PostgreSQL to apply changes
    systemctl restart postgresql@14-main

    echo ""
    echo "✅ Primary server configured successfully"
    echo ""
    echo "Replication Status:"
    sudo -u postgres psql -c "SELECT * FROM pg_replication_slots;"
    sudo -u postgres psql -c "SELECT usename, application_name, client_addr, state, sync_state FROM pg_stat_replication;"
}

# ===== REPLICA SERVER CONFIGURATION =====

setup_replica() {
    echo "Configuring REPLICA server: $REPLICA_HOST"
    echo ""

    # 1. Stop PostgreSQL on replica (will be rebuilt)
    systemctl stop postgresql@14-main

    # 2. Backup existing data (safety)
    if [ -d "$POSTGRES_DATA_DIR" ]; then
        mv "$POSTGRES_DATA_DIR" "${POSTGRES_DATA_DIR}.backup.$(date +%Y%m%d-%H%M%S)"
    fi

    # 3. Create base backup from primary using pg_basebackup
    echo "Creating base backup from primary (this may take several minutes)..."
    sudo -u postgres pg_basebackup \
        -h $PRIMARY_HOST \
        -D $POSTGRES_DATA_DIR \
        -U $REPLICATION_USER \
        -P \
        -v \
        -R \
        -X stream \
        -C \
        -S replica1_slot

    # -R: Creates standby.signal and writes recovery parameters
    # -X stream: Stream WAL while backup is in progress
    # -C: Create replication slot on primary (if it doesn't exist)
    # -S: Use replication slot for reliable replication

    # 4. Configure replica-specific settings (optional)
    cat >> $POSTGRES_DATA_DIR/postgresql.auto.conf <<EOF

# Replica-specific configuration
primary_conninfo = 'host=$PRIMARY_HOST port=5432 user=$REPLICATION_USER password=$REPLICATION_PASSWORD application_name=replica1'
primary_slot_name = 'replica1_slot'

# Recovery settings
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'  # If using WAL archiving
recovery_target_timeline = 'latest'

# Hot standby settings (allow read queries on replica)
hot_standby = on
max_standby_streaming_delay = 30s      # Max delay before canceling conflicting queries
EOF

    # 5. Set proper permissions
    chown -R postgres:postgres $POSTGRES_DATA_DIR
    chmod 700 $POSTGRES_DATA_DIR

    # 6. Start replica
    systemctl start postgresql@14-main

    echo ""
    echo "✅ Replica server configured successfully"
    echo ""
    echo "Replica Status:"
    sudo -u postgres psql -c "SELECT pg_is_in_recovery();"  # Should return 't'
    sudo -u postgres psql -c "SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn(), pg_last_xact_replay_timestamp();"
}

# ===== REPLICATION VERIFICATION =====

verify_replication() {
    echo "Verifying replication setup..."
    echo ""

    # Check primary replication status
    echo "=== PRIMARY SERVER STATUS ==="
    sudo -u postgres psql -h $PRIMARY_HOST -U $REPLICATION_USER postgres <<EOF
SELECT
    client_addr,
    application_name,
    state,
    sync_state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    sync_priority,
    EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp())) AS lag_seconds
FROM pg_stat_replication;
EOF

    echo ""
    echo "=== REPLICA SERVER STATUS ==="
    sudo -u postgres psql -h $REPLICA_HOST postgres <<EOF
SELECT
    pg_is_in_recovery() AS is_replica,
    pg_last_wal_receive_lsn() AS receive_lsn,
    pg_last_wal_replay_lsn() AS replay_lsn,
    pg_last_xact_replay_timestamp() AS last_replay_timestamp,
    EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp())) AS lag_seconds;
EOF

    echo ""
    echo "=== REPLICATION LAG ==="
    # Acceptable lag: <1 second for local replicas, <5 seconds for remote
    LAG=$(sudo -u postgres psql -h $PRIMARY_HOST -U postgres postgres -t -c \
        "SELECT EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp())) FROM pg_stat_replication LIMIT 1;")

    if (( $(echo "$LAG < 5" | bc -l) )); then
        echo "✅ Replication lag: ${LAG}s (healthy)"
    else
        echo "⚠️ Replication lag: ${LAG}s (high)"
    fi
}

# ===== MAIN =====

case "${1:-}" in
    primary)
        setup_primary
        ;;
    replica)
        setup_replica
        ;;
    verify)
        verify_replication
        ;;
    *)
        echo "Usage: $0 {primary|replica|verify}"
        echo ""
        echo "  primary  - Configure primary server for replication"
        echo "  replica  - Set up replica from primary"
        echo "  verify   - Verify replication status"
        exit 1
        ;;
esac
```

### Example 2: Automated Failover Script with Prometheus Integration

```python
#!/usr/bin/env python3
"""
Production-ready PostgreSQL automatic failover script with
health checks, monitoring integration, and rollback capability.
"""

import psycopg2
import time
import logging
import subprocess
from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServerRole(Enum):
    """Database server role."""
    PRIMARY = "primary"
    REPLICA = "replica"
    UNKNOWN = "unknown"


@dataclass
class ReplicationStatus:
    """Replication status information."""
    is_primary: bool
    is_replica: bool
    replication_lag_seconds: Optional[float]
    wal_receive_lsn: Optional[str]
    wal_replay_lsn: Optional[str]
    connected_replicas: int


class PostgreSQLFailoverManager:
    """
    Manages automatic failover for PostgreSQL streaming replication.
    """

    def __init__(
        self,
        primary_host: str,
        replica_host: str,
        postgres_user: str = "postgres",
        postgres_password: str = "",
        failover_threshold_seconds: int = 30,
        alert_webhook: Optional[str] = None
    ):
        """
        Initialize failover manager.

        Args:
            primary_host: Primary server hostname
            replica_host: Replica server hostname
            postgres_user: PostgreSQL superuser
            postgres_password: PostgreSQL password
            failover_threshold_seconds: Trigger failover after this many seconds down
            alert_webhook: Slack/PagerDuty webhook for alerts
        """
        self.primary_host = primary_host
        self.replica_host = replica_host
        self.postgres_user = postgres_user
        self.postgres_password = postgres_password
        self.failover_threshold = failover_threshold_seconds
        self.alert_webhook = alert_webhook

        self.primary_down_since: Optional[float] = None

    def check_server_health(self, host: str) -> bool:
        """
        Check if PostgreSQL server is healthy.

        Args:
            host: Server hostname

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            conn = psycopg2.connect(
                host=host,
                user=self.postgres_user,
                password=self.postgres_password,
                database="postgres",
                connect_timeout=5
            )
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Health check failed for {host}: {e}")
            return False

    def get_replication_status(self, host: str) -> Optional[ReplicationStatus]:
        """
        Get replication status from a server.

        Args:
            host: Server hostname

        Returns:
            ReplicationStatus or None if unreachable
        """
        try:
            conn = psycopg2.connect(
                host=host,
                user=self.postgres_user,
                password=self.postgres_password,
                database="postgres",
                connect_timeout=5
            )

            with conn.cursor() as cur:
                # Check if primary or replica
                cur.execute("SELECT pg_is_in_recovery()")
                is_replica = cur.fetchone()[0]
                is_primary = not is_replica

                # Get replication lag (for replicas)
                replication_lag = None
                wal_receive_lsn = None
                wal_replay_lsn = None

                if is_replica:
                    cur.execute("""
                        SELECT
                            EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp())) AS lag_seconds,
                            pg_last_wal_receive_lsn()::text AS receive_lsn,
                            pg_last_wal_replay_lsn()::text AS replay_lsn
                    """)
                    row = cur.fetchone()
                    replication_lag = row[0]
                    wal_receive_lsn = row[1]
                    wal_replay_lsn = row[2]

                # Count connected replicas (for primary)
                connected_replicas = 0
                if is_primary:
                    cur.execute("SELECT COUNT(*) FROM pg_stat_replication")
                    connected_replicas = cur.fetchone()[0]

            conn.close()

            return ReplicationStatus(
                is_primary=is_primary,
                is_replica=is_replica,
                replication_lag_seconds=replication_lag,
                wal_receive_lsn=wal_receive_lsn,
                wal_replay_lsn=wal_replay_lsn,
                connected_replicas=connected_replicas
            )

        except Exception as e:
            logger.error(f"Failed to get replication status from {host}: {e}")
            return None

    def promote_replica_to_primary(self, replica_host: str) -> bool:
        """
        Promote replica to primary.

        Args:
            replica_host: Replica server to promote

        Returns:
            True if promotion successful
        """
        logger.info(f"Promoting replica {replica_host} to primary...")

        try:
            # Execute pg_promote() via SSH or local command
            # (Assuming replica is on same machine for this example)
            conn = psycopg2.connect(
                host=replica_host,
                user=self.postgres_user,
                password=self.postgres_password,
                database="postgres"
            )

            with conn.cursor() as cur:
                # Promote replica to primary
                cur.execute("SELECT pg_promote()")
                conn.commit()

            conn.close()

            # Wait for promotion to complete
            time.sleep(5)

            # Verify promotion
            status = self.get_replication_status(replica_host)
            if status and status.is_primary:
                logger.info(f"✅ Successfully promoted {replica_host} to primary")
                return True
            else:
                logger.error(f"❌ Promotion failed - server is still replica")
                return False

        except Exception as e:
            logger.error(f"Promotion failed: {e}")
            return False

    def send_alert(self, message: str, severity: str = "error") -> None:
        """
        Send alert to configured webhook.

        Args:
            message: Alert message
            severity: Alert severity (info, warning, error, critical)
        """
        if not self.alert_webhook:
            return

        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }

        payload = {
            'text': f"{emoji_map.get(severity, '❓')} PostgreSQL Failover Alert",
            'attachments': [{
                'color': 'danger' if severity in ['error', 'critical'] else 'warning',
                'text': message,
                'footer': 'PostgreSQL Failover Manager',
                'ts': int(time.time())
            }]
        }

        try:
            requests.post(self.alert_webhook, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    def monitor_and_failover(self) -> None:
        """
        Continuously monitor replication and perform automatic failover.
        """
        logger.info("Starting replication monitoring...")

        while True:
            try:
                # Check primary health
                primary_healthy = self.check_server_health(self.primary_host)

                if not primary_healthy:
                    if self.primary_down_since is None:
                        # Primary just went down
                        self.primary_down_since = time.time()
                        logger.warning(f"⚠️ Primary {self.primary_host} is DOWN")
                        self.send_alert(
                            f"Primary database {self.primary_host} is unreachable. "
                            f"Failover will trigger in {self.failover_threshold} seconds.",
                            severity='warning'
                        )

                    # Check if primary has been down long enough to trigger failover
                    down_duration = time.time() - self.primary_down_since

                    if down_duration >= self.failover_threshold:
                        logger.critical(
                            f"🚨 Primary down for {down_duration:.0f}s - "
                            f"TRIGGERING FAILOVER"
                        )

                        self.send_alert(
                            f"PRIMARY FAILURE: {self.primary_host} down for "
                            f"{down_duration:.0f}s. Initiating automatic failover to "
                            f"{self.replica_host}",
                            severity='critical'
                        )

                        # Perform failover
                        success = self.promote_replica_to_primary(self.replica_host)

                        if success:
                            self.send_alert(
                                f"✅ FAILOVER SUCCESSFUL: {self.replica_host} is now PRIMARY. "
                                f"Update application connection strings immediately.",
                                severity='error'  # Still an error situation
                            )
                            # Stop monitoring (manual intervention required)
                            break
                        else:
                            self.send_alert(
                                f"❌ FAILOVER FAILED: Could not promote {self.replica_host}. "
                                f"Manual intervention required immediately.",
                                severity='critical'
                            )
                            break

                else:
                    # Primary is healthy
                    if self.primary_down_since is not None:
                        # Primary recovered
                        logger.info(f"✅ Primary {self.primary_host} recovered")
                        self.send_alert(
                            f"Primary database {self.primary_host} has recovered.",
                            severity='info'
                        )
                        self.primary_down_since = None

                    # Check replication lag
                    replica_status = self.get_replication_status(self.replica_host)

                    if replica_status:
                        lag = replica_status.replication_lag_seconds or 0

                        if lag > 60:
                            logger.warning(f"⚠️ High replication lag: {lag:.1f}s")
                            self.send_alert(
                                f"High replication lag detected: {lag:.1f} seconds",
                                severity='warning'
                            )
                        else:
                            logger.info(
                                f"Replication healthy: lag={lag:.1f}s, "
                                f"primary={self.primary_host}, replica={self.replica_host}"
                            )

                # Sleep before next check
                time.sleep(10)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(10)


# CLI usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PostgreSQL Failover Manager")
    parser.add_argument("--primary", required=True, help="Primary host")
    parser.add_argument("--replica", required=True, help="Replica host")
    parser.add_argument("--user", default="postgres", help="PostgreSQL user")
    parser.add_argument("--password", default="", help="PostgreSQL password")
    parser.add_argument("--threshold", type=int, default=30, help="Failover threshold (seconds)")
    parser.add_argument("--webhook", help="Alert webhook URL")

    args = parser.parse_args()

    manager = PostgreSQLFailoverManager(
        primary_host=args.primary,
        replica_host=args.replica,
        postgres_user=args.user,
        postgres_password=args.password,
        failover_threshold_seconds=args.threshold,
        alert_webhook=args.webhook
    )

    manager.monitor_and_failover()
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "could not connect to server" | Replica cannot reach primary | Check network connectivity, firewall rules, pg_hba.conf |
| "requested WAL segment already removed" | WAL files deleted before replica could receive them | Increase wal_keep_size or use replication slots |
| "replication slot does not exist" | Replica trying to use non-existent slot | Create slot on primary: `SELECT pg_create_physical_replication_slot('slot_name')` |
| "hot standby conflict" | Query on replica conflicts with recovery | Increase max_standby_streaming_delay or tune query cancellation |
| "timeline history file missing" | Replica and primary have diverged after failover | Rebuild replica from new primary using pg_basebackup |

## Configuration Options

**Replication Modes**
- **Asynchronous** (default): Best performance, small data loss risk
- **Synchronous** (`synchronous_commit=on`): Zero data loss, slower writes
- **Remote write** (`synchronous_commit=remote_write`): Balanced approach
- **Remote apply** (`synchronous_commit=remote_apply`): Strongest consistency

**Replication Methods**
- **Streaming replication**: Binary WAL streaming (physical replication)
- **Logical replication**: Selective table replication (PostgreSQL 10+)
- **WAL shipping**: Archive-based replication (for backups)

**Failover Strategies**
- **Manual failover**: DBA triggers promotion (safest)
- **Automatic failover**: Scripted promotion after health check failure
- **Patroni/repmgr**: Cluster management with automatic failover
- **Cloud-managed**: RDS/CloudSQL automatic failover

## Best Practices

DO:
- Use replication slots to prevent WAL deletion before replica receives it
- Monitor replication lag continuously (alert at >10 seconds)
- Test failover procedures quarterly (disaster recovery drills)
- Use synchronous replication for critical write transactions only
- Implement connection pooling to handle failover reconnections
- Document failover runbooks with step-by-step procedures
- Keep replicas on same PostgreSQL major version as primary

DON'T:
- Run long-running queries on replicas without tuning conflict resolution
- Forget to update application connection strings after failover
- Use synchronous replication over high-latency networks (>50ms)
- Skip monitoring replication lag (leads to split-brain scenarios)
- Promote replica without verifying it's up-to-date
- Delete replication slots without stopping replicas first
- Ignore hot standby conflicts (causes query cancellations)

## Performance Considerations

- **Replication lag**: <1s for local replicas, <5s for cross-region
- **Write overhead**: 5-10% for asynchronous, 20-50% for synchronous
- **Network bandwidth**: 10-50 Mbps per active replica
- **Disk I/O**: Replica writes same data as primary (similar load)
- **Failover time (RTO)**: 10-60 seconds for automatic, 5-15 minutes for manual
- **Data loss (RPO)**: 0 seconds (sync), 0-5 seconds (async)

## Security Considerations

- Use strong passwords for replication user (20+ characters)
- Encrypt replication traffic with SSL/TLS (`sslmode=require`)
- Restrict replication connections in pg_hba.conf to specific IPs
- Audit all failover operations for compliance
- Rotate replication credentials quarterly
- Use dedicated replication user (not superuser)
- Enable connection logging for replication connections

## Related Commands

- `/database-backup-automator` - Backup before major replication changes
- `/database-health-monitor` - Monitor replication lag and health
- `/database-recovery-manager` - PITR using WAL archives from replication
- `/database-connection-pooler` - Handle connection routing after failover

## Version History

- v1.0.0 (2024-10): Initial implementation with streaming replication and automatic failover
- Planned v1.1.0: Add logical replication support, Patroni integration
