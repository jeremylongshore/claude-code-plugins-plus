# Scripts

Bundled resources for database-recovery-manager skill

- [x] validate_backup.sh: Script to validate database backups by checking integrity and recoverability.
- [x] pitr_restore.sh: Script to perform point-in-time recovery to a specified timestamp.
- [x] failover.sh: Script to initiate a failover to a secondary database instance.
- [x] test_recovery.sh: Script to automate recovery testing by restoring backups to a test environment.

## Script Descriptions

### validate_backup.sh
Validates database backups by checking file integrity and recoverability. Supports PostgreSQL, MySQL, and MongoDB backup formats. Performs format-specific validation and optional connectivity tests.

**Usage:**
```bash
./validate_backup.sh -p /path/to/backup -t postgresql
./validate_backup.sh -p /backups/dump.sql.gz -t mysql -c "mysql://user@localhost"
```

### pitr_restore.sh
Performs point-in-time recovery (PITR) to a specified timestamp. Manages base backups and WAL/transaction logs for recovery to any specific point in time.

**Usage:**
```bash
./pitr_restore.sh -t postgresql --target-time "2025-12-10T14:30:00Z" -b /backups/base.sql.gz -w /backups/wal
./pitr_restore.sh -t mysql --target-time "2025-12-10 14:30:00" --verify
```

### failover.sh
Initiates automatic or manual failover to a secondary database instance. Supports monitoring, health checks, DNS updates, and reverse replication setup.

**Usage:**
```bash
./failover.sh -t postgresql --primary-host db1.example.com --secondary-host db2.example.com
./failover.sh -t mysql --mode automatic --check-interval 10 --dns-record db.example.com
```

### test_recovery.sh
Automates recovery testing by restoring backups to a test environment. Validates backup recoverability without affecting production. Includes data verification and automatic cleanup.

**Usage:**
```bash
./test_recovery.sh -t postgresql -b /backups/db.sql.gz --test-db-port 5433
./test_recovery.sh -t mysql -b /backups/dump.sql --verify-data --cleanup
```
