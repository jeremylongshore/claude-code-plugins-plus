# PostgreSQL Backup and Restore Guide

## Backup Methods

### pg_dump (Logical Backup)

**Single Database Backup:**

```bash
pg_dump -h localhost -U postgres -d mydb > mydb.sql
```

**With Compression (Custom Format):**

```bash
pg_dump -h localhost -U postgres -d mydb \
  --format=custom \
  --compress=9 \
  --file=mydb.dump
```

**Plain SQL with Compression:**

```bash
pg_dump -h localhost -U postgres -d mydb | gzip > mydb.sql.gz
```

### pg_dumpall (All Databases)

```bash
pg_dumpall -h localhost -U postgres > all_databases.sql
```

### pg_basebackup (Physical Backup)

For point-in-time recovery and replication:

```bash
pg_basebackup -h localhost -U replication -D /var/lib/postgresql/backup \
  --wal-method=stream \
  --checkpoint=fast \
  --progress
```

## Backup Options

| Option | Description | Example |
|--------|-------------|---------|
| `-F c` | Custom format (compressed) | `pg_dump -F c -f backup.dump` |
| `-F p` | Plain SQL (default) | `pg_dump -F p -f backup.sql` |
| `-F t` | Tar format | `pg_dump -F t -f backup.tar` |
| `-F d` | Directory format | `pg_dump -F d -f backup_dir/` |
| `-j N` | Parallel jobs (dir format only) | `pg_dump -F d -j 4` |
| `-T table` | Exclude table | `pg_dump -T logs` |
| `-t table` | Include only table | `pg_dump -t users` |
| `-n schema` | Dump specific schema | `pg_dump -n public` |
| `--data-only` | Data without schema | `pg_dump --data-only` |
| `--schema-only` | Schema without data | `pg_dump --schema-only` |

## Restore Methods

### psql (Plain SQL)

```bash
psql -h localhost -U postgres -d mydb < mydb.sql

# From compressed
gunzip -c mydb.sql.gz | psql -h localhost -U postgres -d mydb
```

### pg_restore (Custom/Tar/Directory)

```bash
# Create empty database first
createdb -h localhost -U postgres mydb_restored

# Restore
pg_restore -h localhost -U postgres -d mydb_restored mydb.dump
```

**Parallel Restore:**

```bash
pg_restore -h localhost -U postgres -d mydb -j 4 mydb.dump
```

**Restore Options:**

```bash
pg_restore \
  --clean           # Drop objects before recreating
  --if-exists       # Don't error if object doesn't exist
  --no-owner        # Skip ownership commands
  --no-privileges   # Skip grant/revoke commands
  --single-transaction  # All-or-nothing restore
  -d mydb mydb.dump
```

## Point-in-Time Recovery (PITR)

### Setup WAL Archiving

In `postgresql.conf`:

```conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
```

### Recovery

1. Stop PostgreSQL
2. Clear data directory (backup first!)
3. Restore base backup
4. Create `recovery.signal` file
5. Configure `postgresql.conf`:

   ```conf
   restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
   recovery_target_time = '2025-01-15 14:30:00'
   ```

6. Start PostgreSQL

## Production Backup Script

```bash
#!/bin/bash
set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/postgresql"
RETENTION_DAYS=7
DB_HOST="localhost"
DB_USER="postgres"
DB_NAME="production"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.dump"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Perform backup
log "Starting backup of $DB_NAME"

if PGPASSWORD="${PGPASSWORD:-}" pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --verbose \
    --file="$BACKUP_FILE" 2>> "$LOG_FILE"; then

    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup completed: $BACKUP_FILE ($SIZE)"

    # Verify backup
    if pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1; then
        log "Backup verification passed"
    else
        log "ERROR: Backup verification failed"
        exit 1
    fi
else
    log "ERROR: Backup failed"
    exit 1
fi

# Cleanup old backups
log "Cleaning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "*.dump" -mtime "+$RETENTION_DAYS" -delete

log "Backup process completed"
```

## Selective Restore

**Single Table:**

```bash
pg_restore -h localhost -U postgres -d mydb \
  --table=users \
  --data-only \
  mydb.dump
```

**List Contents:**

```bash
pg_restore --list mydb.dump > toc.txt
# Edit toc.txt to select items
pg_restore -h localhost -U postgres -d mydb \
  --use-list=toc.txt \
  mydb.dump
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "permission denied" | Grant CONNECT, SELECT on tables to backup user |
| "out of memory" | Use `-F d` with `-j` for parallel backup |
| "lock timeout" | Run during low-traffic period |
| Restore fails on constraints | Use `--disable-triggers` or restore in correct order |
| Large object issues | Add `--blobs` to include BLOBs |
