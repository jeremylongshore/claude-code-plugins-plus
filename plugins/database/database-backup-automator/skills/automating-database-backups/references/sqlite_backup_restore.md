# SQLite Backup and Restore Guide

## Backup Methods

### File Copy (Simple)

SQLite databases are single files, so simple copy works when database is not being written to:

```bash
# Ensure no writes during copy
cp /path/to/database.db /backup/database_$(date +%Y%m%d).db
```

### sqlite3 .backup Command (Safe)

Uses SQLite's online backup API - safe during active connections:

```bash
sqlite3 /path/to/database.db ".backup '/backup/database.db'"
```

**With Compression:**

```bash
sqlite3 /path/to/database.db ".backup '/dev/stdout'" | gzip > /backup/database.db.gz
```

### sqlite3 .dump Command (SQL Export)

Exports as SQL statements - portable and inspectable:

```bash
sqlite3 /path/to/database.db .dump > /backup/database.sql

# With compression
sqlite3 /path/to/database.db .dump | gzip > /backup/database.sql.gz
```

### VACUUM INTO (SQLite 3.27+)

Creates optimized copy:

```bash
sqlite3 /path/to/database.db "VACUUM INTO '/backup/database_optimized.db'"
```

## Backup Comparison

| Method | During Writes | Portable | Size | Speed |
|--------|--------------|----------|------|-------|
| File copy | Risky | Yes | Original | Fast |
| .backup | Safe | Yes | Original | Fast |
| .dump | Safe | Very | Larger | Slower |
| VACUUM INTO | Safe | Yes | Optimized | Medium |

## Restore Methods

### From File Copy

```bash
# Stop application
systemctl stop myapp

# Replace database
cp /backup/database.db /path/to/database.db

# Fix permissions
chown app:app /path/to/database.db
chmod 644 /path/to/database.db

# Start application
systemctl start myapp
```

### From SQL Dump

```bash
# Create new database from dump
sqlite3 /path/to/database_new.db < /backup/database.sql

# From compressed
gunzip -c /backup/database.sql.gz | sqlite3 /path/to/database_new.db
```

### Selective Restore

**Single Table from Dump:**

```bash
# Extract CREATE TABLE and INSERT statements for specific table
grep -E "^(CREATE TABLE|INSERT INTO) \"?users" /backup/database.sql > users.sql
sqlite3 /path/to/database.db < users.sql
```

## Production Backup Script

```bash
#!/bin/bash
set -euo pipefail

# Configuration
DB_PATH="/var/lib/myapp/database.db"
BACKUP_DIR="/var/backups/sqlite"
RETENTION_DAYS=7
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/database_${DATE}.db"
LOG_FILE="${BACKUP_DIR}/backup.log"

mkdir -p "$BACKUP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting backup of $DB_PATH"

# Check database exists
if [ ! -f "$DB_PATH" ]; then
    log "ERROR: Database not found: $DB_PATH"
    exit 1
fi

# Check database integrity before backup
if ! sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | grep -q "^ok$"; then
    log "WARNING: Database integrity check failed"
fi

# Perform backup using online backup API
if sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'" 2>> "$LOG_FILE"; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup completed: $BACKUP_FILE ($SIZE)"

    # Verify backup
    if sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" | grep -q "^ok$"; then
        log "Backup verification passed"
    else
        log "ERROR: Backup verification failed"
        exit 1
    fi

    # Compress backup
    gzip "$BACKUP_FILE"
    log "Compressed to: ${BACKUP_FILE}.gz"
else
    log "ERROR: Backup failed"
    exit 1
fi

# Cleanup old backups
log "Cleaning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "*.db.gz" -mtime "+$RETENTION_DAYS" -delete

log "Backup process completed"
```

## Incremental Backup Strategy

SQLite doesn't have built-in incremental backup, but you can use these strategies:

### WAL Mode Backup

```bash
# Enable WAL mode (run once)
sqlite3 /path/to/database.db "PRAGMA journal_mode=WAL;"

# Checkpoint before backup to merge WAL into main file
sqlite3 /path/to/database.db "PRAGMA wal_checkpoint(TRUNCATE);"

# Then backup
sqlite3 /path/to/database.db ".backup '/backup/database.db'"
```

### Change Tracking with Triggers

```sql
-- Create change log table
CREATE TABLE IF NOT EXISTS change_log (
    id INTEGER PRIMARY KEY,
    table_name TEXT,
    row_id INTEGER,
    action TEXT,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger for each table
CREATE TRIGGER users_changes AFTER INSERT OR UPDATE OR DELETE ON users
BEGIN
    INSERT INTO change_log (table_name, row_id, action)
    VALUES ('users', COALESCE(NEW.id, OLD.id),
            CASE WHEN NEW.id IS NULL THEN 'DELETE'
                 WHEN OLD.id IS NULL THEN 'INSERT'
                 ELSE 'UPDATE' END);
END;
```

## Performance Optimization

### Before Backup

```bash
# Optimize database
sqlite3 /path/to/database.db "VACUUM;"
sqlite3 /path/to/database.db "ANALYZE;"
```

### WAL Mode for Concurrent Access

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

## Database Integrity Check

```bash
# Quick integrity check
sqlite3 /path/to/database.db "PRAGMA quick_check;"

# Full integrity check
sqlite3 /path/to/database.db "PRAGMA integrity_check;"

# Check foreign keys
sqlite3 /path/to/database.db "PRAGMA foreign_key_check;"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "database is locked" | Wait for transactions, use WAL mode |
| Backup too slow | Use `.backup` instead of `.dump` |
| Corrupted backup | Run integrity check on source first |
| Permission denied | Check file and directory permissions |
| Disk full | Clean old backups, check df -h |
| Large WAL file | Run `PRAGMA wal_checkpoint(TRUNCATE)` |

## Restore Verification

```bash
# After restore, verify
sqlite3 /path/to/restored.db <<EOF
PRAGMA integrity_check;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM orders;
.tables
EOF
```

## Python Backup Script

```python
#!/usr/bin/env python3
"""SQLite backup with verification."""
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

def backup_database(source: str, backup_dir: str) -> str:
    """Create verified backup of SQLite database."""
    source_path = Path(source)
    backup_path = Path(backup_dir) / f"{source_path.stem}_{datetime.now():%Y%m%d_%H%M%S}.db"

    # Ensure backup directory exists
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    # Use SQLite backup API
    source_conn = sqlite3.connect(source)
    backup_conn = sqlite3.connect(str(backup_path))

    with backup_conn:
        source_conn.backup(backup_conn)

    source_conn.close()

    # Verify backup
    verify_conn = sqlite3.connect(str(backup_path))
    result = verify_conn.execute("PRAGMA integrity_check").fetchone()
    verify_conn.close()

    if result[0] != "ok":
        raise RuntimeError(f"Backup integrity check failed: {result}")

    return str(backup_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <source.db> <backup_dir>")
        sys.exit(1)

    backup_file = backup_database(sys.argv[1], sys.argv[2])
    print(f"Backup created: {backup_file}")
```
