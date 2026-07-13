# MySQL Backup and Restore Guide

## Backup Methods

### mysqldump (Logical Backup)

**Single Database:**

```bash
mysqldump -h localhost -u root -p mydb > mydb.sql
```

**With Compression:**

```bash
mysqldump -h localhost -u root -p mydb | gzip > mydb.sql.gz
```

**All Databases:**

```bash
mysqldump -h localhost -u root -p --all-databases > all_databases.sql
```

**Multiple Specific Databases:**

```bash
mysqldump -h localhost -u root -p --databases db1 db2 db3 > multi_db.sql
```

### mysqlpump (Parallel Backup)

```bash
mysqlpump -h localhost -u root -p \
  --default-parallelism=4 \
  mydb > mydb.sql
```

### XtraBackup (Physical Backup)

For large databases and hot backups:

```bash
# Full backup
xtrabackup --backup --target-dir=/var/backups/mysql/full \
  --user=root --password=secret

# Incremental backup
xtrabackup --backup --target-dir=/var/backups/mysql/inc1 \
  --incremental-basedir=/var/backups/mysql/full \
  --user=root --password=secret
```

## mysqldump Options

| Option | Description |
|--------|-------------|
| `--single-transaction` | Consistent snapshot without locking (InnoDB) |
| `--routines` | Include stored procedures and functions |
| `--triggers` | Include triggers (default: yes) |
| `--events` | Include scheduled events |
| `--quick` | Don't buffer results in memory |
| `--lock-tables` | Lock all tables before dump |
| `--add-drop-database` | Add DROP DATABASE before CREATE |
| `--no-data` | Schema only, no data |
| `--no-create-info` | Data only, no CREATE statements |
| `--ignore-table=db.table` | Exclude specific table |
| `--where="id > 1000"` | Filter rows |
| `--compress` | Compress client/server protocol |

## Production Backup Command

```bash
mysqldump -h localhost -u backup_user -p \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --quick \
  --add-drop-database \
  --databases mydb | gzip > mydb_$(date +%Y%m%d_%H%M%S).sql.gz
```

## Restore Methods

### mysql Client (SQL Dump)

```bash
mysql -h localhost -u root -p mydb < mydb.sql

# From compressed
gunzip -c mydb.sql.gz | mysql -h localhost -u root -p mydb

# Create database first if needed
mysql -h localhost -u root -p -e "CREATE DATABASE IF NOT EXISTS mydb"
mysql -h localhost -u root -p mydb < mydb.sql
```

### XtraBackup Restore

```bash
# Prepare backup
xtrabackup --prepare --target-dir=/var/backups/mysql/full

# Stop MySQL
systemctl stop mysql

# Clear data directory (BACKUP FIRST!)
rm -rf /var/lib/mysql/*

# Copy back
xtrabackup --copy-back --target-dir=/var/backups/mysql/full

# Fix permissions
chown -R mysql:mysql /var/lib/mysql

# Start MySQL
systemctl start mysql
```

## Point-in-Time Recovery

### Enable Binary Logging

In `my.cnf`:

```ini
[mysqld]
log_bin = /var/log/mysql/mysql-bin
binlog_format = ROW
expire_logs_days = 7
max_binlog_size = 100M
```

### Recovery Process

```bash
# Restore full backup
mysql -u root -p < full_backup.sql

# Apply binary logs up to specific time
mysqlbinlog --stop-datetime="2025-01-15 14:30:00" \
  /var/log/mysql/mysql-bin.000001 \
  /var/log/mysql/mysql-bin.000002 | mysql -u root -p
```

## Production Backup Script

```bash
#!/bin/bash
set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/mysql"
RETENTION_DAYS=7
DB_HOST="localhost"
DB_USER="backup"
DB_PASS="${MYSQL_BACKUP_PASSWORD:-}"
DB_NAME="production"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting backup of $DB_NAME"

# Perform backup
if mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --quick \
    "$DB_NAME" 2>> "$LOG_FILE" | gzip > "$BACKUP_FILE"; then

    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup completed: $BACKUP_FILE ($SIZE)"

    # Verify backup
    if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
        log "Backup verification passed"
    else
        log "ERROR: Backup verification failed"
        exit 1
    fi
else
    log "ERROR: Backup failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Cleanup old backups
log "Cleaning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime "+$RETENTION_DAYS" -delete

log "Backup process completed"
```

## Selective Restore

**Single Table:**

```bash
# Extract table from dump
sed -n '/^-- Table structure for table `users`/,/^-- Table structure for table/p' mydb.sql > users.sql

# Or use mysql with specific table
mysql -u root -p mydb -e "DROP TABLE IF EXISTS users; SOURCE users.sql;"
```

**Using mysqlpump for Selective Dump:**

```bash
mysqlpump -u root -p --include-tables=users,orders mydb > partial.sql
```

## Backup User Setup

```sql
CREATE USER 'backup'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT, SHOW VIEW, TRIGGER, LOCK TABLES, RELOAD, PROCESS ON *.* TO 'backup'@'localhost';
GRANT REPLICATION CLIENT ON *.* TO 'backup'@'localhost';  -- For --master-data
FLUSH PRIVILEGES;
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Lock wait timeout | Use `--single-transaction` for InnoDB |
| "Access denied" | Grant LOCK TABLES, SELECT privileges |
| Out of memory | Use `--quick` to stream results |
| Binary log not found | Enable with `log_bin` in my.cnf |
| Character set issues | Add `--default-character-set=utf8mb4` |
| Slow restore | Disable `foreign_key_checks`, `unique_checks` temporarily |
