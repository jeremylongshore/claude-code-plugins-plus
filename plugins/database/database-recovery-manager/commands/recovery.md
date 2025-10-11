---
description: Implement disaster recovery and point-in-time recovery strategies
shortcut: recovery
---

# Database Recovery Manager

Implement comprehensive disaster recovery, point-in-time recovery (PITR), and automated failover strategies for production database systems with automated backup verification and recovery testing.

## When to Use This Command

Use `/recovery` when you need to:
- Set up disaster recovery infrastructure for production databases
- Implement point-in-time recovery (PITR) capabilities
- Automate backup validation and recovery testing
- Design multi-region failover strategies
- Recover from data corruption or accidental deletions
- Meet compliance requirements for backup retention and recovery time objectives (RTO)

DON'T use this when:
- Only need basic database backups (use backup automator instead)
- Working with development databases without recovery requirements
- Database system doesn't support WAL/binary log replication
- Compliance doesn't require tested recovery procedures

## Design Decisions

This command implements **comprehensive disaster recovery with PITR** because:
- Point-in-time recovery prevents data loss from user errors or corruption
- Automated failover ensures minimal downtime (RTO < 5 minutes)
- Regular recovery testing validates backup integrity before disasters
- Multi-region replication provides geographic redundancy
- WAL archiving enables recovery to any point in last 30 days

**Alternative considered: Snapshot-only backups**
- Simpler to implement and restore
- No point-in-time recovery capability
- Recovery point objective (RPO) limited to snapshot frequency
- Recommended only for non-critical databases

**Alternative considered: Manual recovery procedures**
- No automation or testing
- Prone to human error during incidents
- Longer recovery times (RTO hours vs minutes)
- Recommended only for development environments

## Prerequisites

Before running this command:
1. Database with WAL/binary logging enabled
2. Object storage for backup retention (S3, GCS, Azure Blob)
3. Monitoring infrastructure for backup validation
4. Understanding of RTO (Recovery Time Objective) and RPO (Recovery Point Objective) requirements
5. Separate recovery environment for testing

## Implementation Process

### Step 1: Configure WAL Archiving and Continuous Backup
Enable write-ahead logging (WAL) archiving for point-in-time recovery capabilities.

### Step 2: Implement Automated Base Backup System
Set up scheduled base backups with compression and encryption to object storage.

### Step 3: Design Failover and High Availability Architecture
Configure streaming replication with automated failover for zero-downtime recovery.

### Step 4: Build Recovery Testing Framework
Automate recovery validation by restoring backups to test environments regularly.

### Step 5: Document and Drill Recovery Procedures
Create runbooks and conduct disaster recovery drills quarterly.

## Output Format

The command generates:
- `config/recovery.conf` - PostgreSQL recovery configuration
- `scripts/pitr-restore.sh` - Point-in-time recovery automation script
- `monitoring/backup-validator.py` - Automated backup verification
- `failover/replication-monitor.py` - Streaming replication health monitoring
- `docs/recovery-runbook.md` - Step-by-step recovery procedures

## Code Examples

### Example 1: PostgreSQL PITR with WAL Archiving

```bash
# postgresql.conf - Enable WAL archiving
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://my-db-backups/wal-archive/%f --region us-east-1'
archive_timeout = 300  # Force segment switch every 5 minutes
max_wal_senders = 10
wal_keep_size = 1GB

# Continuous archiving with monitoring
restore_command = 'aws s3 cp s3://my-db-backups/wal-archive/%f %p'
archive_cleanup_command = 'pg_archivecleanup /path/to/archive %r'
```

```bash
#!/bin/bash
# scripts/pitr-restore.sh - Point-in-Time Recovery Script

set -euo pipefail

# Configuration
BACKUP_BUCKET="s3://my-db-backups"
PGDATA="/var/lib/postgresql/14/main"
TARGET_TIME="${1:-latest}"  # Format: '2024-10-15 14:30:00 UTC'
RECOVERY_TARGET="${2:-immediate}"  # immediate, time, xid, name

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Step 1: Verify prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if PostgreSQL is stopped
    if systemctl is-active --quiet postgresql; then
        warn "PostgreSQL is running. Stopping service..."
        systemctl stop postgresql
    fi

    # Verify AWS credentials
    if ! aws sts get-caller-identity &>/dev/null; then
        error "AWS credentials not configured"
    fi

    # Check available disk space
    REQUIRED_SPACE=$((50 * 1024 * 1024))  # 50GB in KB
    AVAILABLE_SPACE=$(df -k "$PGDATA" | tail -1 | awk '{print $4}')

    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        error "Insufficient disk space. Required: 50GB, Available: $((AVAILABLE_SPACE / 1024 / 1024))GB"
    fi

    log "Prerequisites check passed"
}

# Step 2: List available base backups
list_backups() {
    log "Fetching available base backups..."

    aws s3 ls "$BACKUP_BUCKET/base-backups/" --recursive | \
        grep "backup.tar.gz" | \
        awk '{print $4}' | \
        sort -r | \
        head -10

    read -p "Enter backup to restore (or press Enter for latest): " SELECTED_BACKUP

    if [ -z "$SELECTED_BACKUP" ]; then
        SELECTED_BACKUP=$(aws s3 ls "$BACKUP_BUCKET/base-backups/" --recursive | \
            grep "backup.tar.gz" | \
            awk '{print $4}' | \
            sort -r | \
            head -1)
    fi

    log "Selected backup: $SELECTED_BACKUP"
}

# Step 3: Restore base backup
restore_base_backup() {
    log "Restoring base backup..."

    # Backup current PGDATA if it exists
    if [ -d "$PGDATA" ]; then
        BACKUP_DIR="${PGDATA}.$(date +%Y%m%d_%H%M%S)"
        warn "Backing up current PGDATA to $BACKUP_DIR"
        mv "$PGDATA" "$BACKUP_DIR"
    fi

    mkdir -p "$PGDATA"

    # Download and extract base backup
    log "Downloading base backup from S3..."
    aws s3 cp "$BACKUP_BUCKET/$SELECTED_BACKUP" - | \
        tar -xzf - -C "$PGDATA"

    # Set correct permissions
    chown -R postgres:postgres "$PGDATA"
    chmod 700 "$PGDATA"

    log "Base backup restored successfully"
}

# Step 4: Configure recovery
configure_recovery() {
    log "Configuring recovery settings..."

    cat > "$PGDATA/recovery.signal" << EOF
# Recovery signal file created by pitr-restore.sh
EOF

    # Create postgresql.auto.conf with recovery settings
    cat > "$PGDATA/postgresql.auto.conf" << EOF
# Temporary recovery configuration
restore_command = 'aws s3 cp $BACKUP_BUCKET/wal-archive/%f %p'
recovery_target_action = 'promote'
EOF

    # Add recovery target if specified
    case "$RECOVERY_TARGET" in
        time)
            echo "recovery_target_time = '$TARGET_TIME'" >> "$PGDATA/postgresql.auto.conf"
            log "Recovery target: $TARGET_TIME"
            ;;
        xid)
            echo "recovery_target_xid = '$TARGET_TIME'" >> "$PGDATA/postgresql.auto.conf"
            log "Recovery target XID: $TARGET_TIME"
            ;;
        name)
            echo "recovery_target_name = '$TARGET_TIME'" >> "$PGDATA/postgresql.auto.conf"
            log "Recovery target name: $TARGET_TIME"
            ;;
        immediate)
            echo "recovery_target = 'immediate'" >> "$PGDATA/postgresql.auto.conf"
            log "Recovery target: end of base backup"
            ;;
    esac

    log "Recovery configuration complete"
}

# Step 5: Start recovery and monitor
start_recovery() {
    log "Starting PostgreSQL in recovery mode..."

    systemctl start postgresql

    log "Monitoring recovery progress..."

    # Wait for recovery to complete
    while true; do
        if sudo -u postgres psql -c "SELECT pg_is_in_recovery();" 2>/dev/null | grep -q "f"; then
            log "Recovery completed successfully!"
            break
        fi

        # Show recovery progress
        RECOVERY_INFO=$(sudo -u postgres psql -c "
            SELECT
                CASE
                    WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() THEN 100
                    ELSE ROUND(100.0 * pg_wal_lsn_diff(pg_last_wal_replay_lsn(), '0/0') /
                         NULLIF(pg_wal_lsn_diff(pg_last_wal_receive_lsn(), '0/0'), 0), 2)
                END AS recovery_percent,
                pg_last_wal_replay_lsn() AS replay_lsn,
                NOW() - pg_last_xact_replay_timestamp() AS replay_lag
        " 2>/dev/null | tail -3 | head -1 || echo "Checking...")

        echo -ne "\r${YELLOW}Recovery in progress: $RECOVERY_INFO${NC}"
        sleep 5
    done

    echo ""
}

# Step 6: Verify recovery
verify_recovery() {
    log "Verifying database integrity..."

    # Run basic checks
    sudo -u postgres psql -c "SELECT version();"
    sudo -u postgres psql -c "SELECT COUNT(*) FROM pg_stat_database;"

    # Check for replication slots
    SLOT_COUNT=$(sudo -u postgres psql -t -c "SELECT COUNT(*) FROM pg_replication_slots;")
    if [ "$SLOT_COUNT" -gt 0 ]; then
        warn "$SLOT_COUNT replication slots found. Consider cleaning up if this is a new primary."
    fi

    log "Database verification complete"
}

# Main recovery workflow
main() {
    log "=== PostgreSQL Point-in-Time Recovery ==="
    log "Target: $TARGET_TIME"
    log "Recovery mode: $RECOVERY_TARGET"

    check_prerequisites
    list_backups
    restore_base_backup
    configure_recovery
    start_recovery
    verify_recovery

    log "Recovery completed successfully!"
    log "Database is now operational"

    cat << EOF

${GREEN}Next Steps:${NC}
1. Verify application connectivity
2. Check data integrity for affected tables
3. Update DNS/load balancer to point to recovered database
4. Monitor replication lag if standby servers exist
5. Create new base backup after recovery

EOF
}

# Run main function
main "$@"
```

```python
# monitoring/backup-validator.py - Automated Backup Verification
import subprocess
import boto3
import psycopg2
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BackupValidationResult:
    """Results from backup validation."""
    backup_name: str
    backup_date: datetime
    validation_date: datetime
    size_mb: float
    restore_time_seconds: float
    integrity_check_passed: bool
    table_count: int
    row_sample_count: int
    errors: List[str]
    warnings: List[str]

    def to_dict(self) -> dict:
        result = asdict(self)
        result['backup_date'] = self.backup_date.isoformat()
        result['validation_date'] = self.validation_date.isoformat()
        return result

class PostgreSQLBackupValidator:
    """Validates PostgreSQL backups by restoring to test environment."""

    def __init__(
        self,
        s3_bucket: str,
        test_db_config: Dict[str, str],
        retention_days: int = 30
    ):
        self.s3_bucket = s3_bucket
        self.test_db_config = test_db_config
        self.retention_days = retention_days
        self.s3_client = boto3.client('s3')

    def list_recent_backups(self, days: int = 7) -> List[Dict[str, any]]:
        """List backups from last N days."""
        prefix = "base-backups/"
        response = self.s3_client.list_objects_v2(
            Bucket=self.s3_bucket,
            Prefix=prefix
        )

        cutoff_date = datetime.now() - timedelta(days=days)
        backups = []

        for obj in response.get('Contents', []):
            if obj['LastModified'].replace(tzinfo=None) > cutoff_date:
                backups.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                })

        return sorted(backups, key=lambda x: x['last_modified'], reverse=True)

    def download_backup(self, backup_key: str, local_path: str) -> bool:
        """Download backup from S3."""
        try:
            logger.info(f"Downloading backup {backup_key}...")
            self.s3_client.download_file(
                self.s3_bucket,
                backup_key,
                local_path
            )
            logger.info(f"Downloaded to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    def restore_to_test_db(self, backup_path: str) -> Optional[float]:
        """Restore backup to test database and measure time."""
        start_time = datetime.now()

        try:
            # Drop and recreate test database
            conn = psycopg2.connect(
                host=self.test_db_config['host'],
                user=self.test_db_config['user'],
                password=self.test_db_config['password'],
                database='postgres'
            )
            conn.autocommit = True

            with conn.cursor() as cur:
                cur.execute(f"DROP DATABASE IF EXISTS {self.test_db_config['database']};")
                cur.execute(f"CREATE DATABASE {self.test_db_config['database']};")

            conn.close()

            # Restore backup using pg_restore
            restore_cmd = [
                'pg_restore',
                '--host', self.test_db_config['host'],
                '--username', self.test_db_config['user'],
                '--dbname', self.test_db_config['database'],
                '--no-owner',
                '--no-acl',
                '--verbose',
                backup_path
            ]

            result = subprocess.run(
                restore_cmd,
                capture_output=True,
                text=True,
                env={'PGPASSWORD': self.test_db_config['password']}
            )

            if result.returncode != 0:
                logger.error(f"Restore failed: {result.stderr}")
                return None

            restore_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Restore completed in {restore_time:.2f} seconds")

            return restore_time

        except Exception as e:
            logger.error(f"Restore error: {e}")
            return None

    def verify_database_integrity(self) -> Dict[str, any]:
        """Run integrity checks on restored database."""
        checks = {
            'table_count': 0,
            'row_sample_count': 0,
            'index_validity': True,
            'constraint_violations': [],
            'errors': [],
            'warnings': []
        }

        try:
            conn = psycopg2.connect(
                host=self.test_db_config['host'],
                user=self.test_db_config['user'],
                password=self.test_db_config['password'],
                database=self.test_db_config['database']
            )

            with conn.cursor() as cur:
                # Count tables
                cur.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema NOT IN ('pg_catalog', 'information_schema');
                """)
                checks['table_count'] = cur.fetchone()[0]

                # Sample row counts from largest tables
                cur.execute("""
                    SELECT schemaname, tablename
                    FROM pg_tables
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY random()
                    LIMIT 10;
                """)

                for schema, table in cur.fetchall():
                    try:
                        cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}";')
                        row_count = cur.fetchone()[0]
                        checks['row_sample_count'] += row_count
                    except Exception as e:
                        checks['warnings'].append(f"Could not count {schema}.{table}: {e}")

                # Check for invalid indexes
                cur.execute("""
                    SELECT schemaname, tablename, indexname
                    FROM pg_indexes
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    LIMIT 100;
                """)

                for schema, table, index in cur.fetchall():
                    try:
                        cur.execute(f'REINDEX INDEX "{schema}"."{index}";')
                    except Exception as e:
                        checks['errors'].append(f"Invalid index {schema}.{index}: {e}")
                        checks['index_validity'] = False

            conn.close()

        except Exception as e:
            checks['errors'].append(f"Integrity check failed: {e}")

        return checks

    def validate_backup(self, backup_info: Dict[str, any]) -> BackupValidationResult:
        """Complete backup validation workflow."""
        logger.info(f"Validating backup: {backup_info['key']}")

        errors = []
        warnings = []

        # Download backup
        local_backup = f"/tmp/{backup_info['key'].split('/')[-1]}"
        if not self.download_backup(backup_info['key'], local_backup):
            errors.append("Failed to download backup")

        # Restore to test database
        restore_time = self.restore_to_test_db(local_backup)
        if restore_time is None:
            errors.append("Failed to restore backup")

        # Verify integrity
        integrity_checks = self.verify_database_integrity()
        errors.extend(integrity_checks.get('errors', []))
        warnings.extend(integrity_checks.get('warnings', []))

        result = BackupValidationResult(
            backup_name=backup_info['key'],
            backup_date=backup_info['last_modified'].replace(tzinfo=None),
            validation_date=datetime.now(),
            size_mb=backup_info['size'] / (1024 * 1024),
            restore_time_seconds=restore_time or 0.0,
            integrity_check_passed=len(errors) == 0,
            table_count=integrity_checks.get('table_count', 0),
            row_sample_count=integrity_checks.get('row_sample_count', 0),
            errors=errors,
            warnings=warnings
        )

        # Log results
        if result.integrity_check_passed:
            logger.info(f"✅ Backup validation PASSED: {backup_info['key']}")
        else:
            logger.error(f"❌ Backup validation FAILED: {backup_info['key']}")
            for error in errors:
                logger.error(f"  - {error}")

        return result

    def run_daily_validation(self):
        """Run daily backup validation on most recent backup."""
        logger.info("Starting daily backup validation...")

        backups = self.list_recent_backups(days=1)
        if not backups:
            logger.warning("No recent backups found")
            return

        latest_backup = backups[0]
        result = self.validate_backup(latest_backup)

        # Save validation results
        report_file = f"validation-report-{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Validation report saved to {report_file}")

        # Alert if validation failed
        if not result.integrity_check_passed:
            self.send_alert(result)

    def send_alert(self, result: BackupValidationResult):
        """Send alert for failed validation."""
        logger.critical(f"ALERT: Backup validation failed for {result.backup_name}")
        # Implement alerting (email, Slack, PagerDuty, etc.)

# Usage
if __name__ == "__main__":
    validator = PostgreSQLBackupValidator(
        s3_bucket="my-db-backups",
        test_db_config={
            'host': 'test-db.example.com',
            'user': 'postgres',
            'password': 'password',
            'database': 'validation_test'
        },
        retention_days=30
    )

    validator.run_daily_validation()
```

### Example 2: MySQL PITR with Binary Log Replication

```bash
# my.cnf - Enable binary logging for PITR
[mysqld]
server-id = 1
log-bin = /var/log/mysql/mysql-bin
binlog_format = ROW
binlog_row_image = FULL
expire_logs_days = 7
sync_binlog = 1
innodb_flush_log_at_trx_commit = 1

# Replication for high availability
gtid_mode = ON
enforce_gtid_consistency = ON
log_slave_updates = ON
```

```bash
#!/bin/bash
# scripts/mysql-pitr-restore.sh

set -euo pipefail

BACKUP_DIR="/backups/mysql"
BINLOG_DIR="/var/log/mysql"
TARGET_DATETIME="$1"  # Format: '2024-10-15 14:30:00'
RESTORE_DIR="/var/lib/mysql-restore"

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"; }
error() { echo "[ERROR] $1" >&2; exit 1; }

# Find base backup before target time
find_base_backup() {
    log "Finding appropriate base backup..."

    TARGET_EPOCH=$(date -d "$TARGET_DATETIME" +%s)

    for backup in $(ls -t "$BACKUP_DIR"/*.tar.gz); do
        BACKUP_TIME=$(basename "$backup" .tar.gz | cut -d'-' -f2)
        BACKUP_EPOCH=$(date -d "$BACKUP_TIME" +%s 2>/dev/null || continue)

        if [ "$BACKUP_EPOCH" -lt "$TARGET_EPOCH" ]; then
            echo "$backup"
            return 0
        fi
    done

    error "No suitable backup found before $TARGET_DATETIME"
}

# Restore base backup
BASE_BACKUP=$(find_base_backup)
log "Restoring base backup: $BASE_BACKUP"

systemctl stop mysql
rm -rf "$RESTORE_DIR"
mkdir -p "$RESTORE_DIR"
tar -xzf "$BASE_BACKUP" -C "$RESTORE_DIR"

# Apply binary logs up to target time
log "Applying binary logs up to $TARGET_DATETIME..."

mysqlbinlog \
    --stop-datetime="$TARGET_DATETIME" \
    "$BINLOG_DIR"/mysql-bin.* | \
    mysql --defaults-file="$RESTORE_DIR"/my.cnf

log "Point-in-time recovery completed"
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "WAL segment not found" | Missing archived WAL files | Check `archive_command` and S3 bucket permissions |
| "Invalid checkpoint" | Corrupted base backup | Restore from previous base backup |
| "Recovery target not reached" | Target time beyond available WAL | Verify WAL archiving is functioning |
| "Insufficient disk space" | Large database or WAL files | Provision additional storage or compress archives |
| "Connection refused during recovery" | PostgreSQL still in recovery mode | Wait for recovery to complete before connecting |

## Configuration Options

**WAL Archiving**
- `wal_level = replica`: Enable WAL archiving (PostgreSQL)
- `archive_mode = on`: Activate WAL archiving
- `archive_timeout = 300`: Force WAL segment switch every 5 minutes
- `log-bin`: Enable binary logging (MySQL)

**Recovery Targets**
- `recovery_target_time`: Restore to specific timestamp
- `recovery_target_xid`: Restore to transaction ID
- `recovery_target_name`: Restore to named restore point
- `recovery_target = 'immediate'`: Stop at end of base backup

**Replication**
- `max_wal_senders = 10`: Maximum replication connections
- `wal_keep_size = 1GB`: Minimum WAL retention on primary

## Best Practices

DO:
- Test recovery procedures monthly in isolated environment
- Monitor WAL archiving lag and alert if > 5 minutes
- Encrypt backups at rest and in transit
- Store backups in multiple regions for geographic redundancy
- Validate backup integrity automatically after creation
- Document RTO/RPO requirements and measure against them

DON'T:
- Skip recovery testing (untested backups are useless)
- Store backups on same infrastructure as production database
- Ignore WAL archiving failures (creates recovery gaps)
- Use same credentials for production and backup storage
- Assume backups work without validation

## Performance Considerations

- WAL archiving adds ~1-5% overhead depending on write workload
- Use parallel backup tools (pgBackRest, Barman) for large databases
- Compress WAL archives to reduce storage costs (50-70% reduction typical)
- Use incremental backups to minimize backup window
- Consider backup network bandwidth (1TB database = ~30 minutes over 10 Gbps)

## Related Commands

- `/database-backup-automator` - Automated backup scheduling
- `/database-replication-manager` - Configure streaming replication
- `/database-health-monitor` - Monitor backup and replication health
- `/database-migration-manager` - Schema change management with recovery points

## Version History

- v1.0.0 (2024-10): Initial implementation with PostgreSQL and MySQL PITR support
- Planned v1.1.0: Add automated failover orchestration and multi-region replication
