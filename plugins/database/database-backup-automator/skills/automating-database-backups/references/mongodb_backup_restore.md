# MongoDB Backup and Restore Guide

## Backup Methods

### mongodump (Logical Backup)

**Single Database:**

```bash
mongodump --uri="mongodb://localhost:27017" --db=mydb --out=/backup/
```

**With Authentication:**

```bash
mongodump --uri="mongodb://user:password@localhost:27017/mydb?authSource=admin" \
  --out=/backup/
```

**With Compression:**

```bash
mongodump --uri="mongodb://localhost:27017" \
  --db=mydb \
  --gzip \
  --out=/backup/$(date +%Y%m%d_%H%M%S)
```

**Single Collection:**

```bash
mongodump --uri="mongodb://localhost:27017" \
  --db=mydb \
  --collection=users \
  --out=/backup/
```

**Archive Format (Single File):**

```bash
mongodump --uri="mongodb://localhost:27017" \
  --db=mydb \
  --archive=/backup/mydb.archive \
  --gzip
```

### Replica Set Backup

```bash
mongodump --uri="mongodb://rs1.example.com:27017,rs2.example.com:27017/mydb?replicaSet=myrs" \
  --readPreference=secondary \
  --out=/backup/
```

### Sharded Cluster Backup

```bash
# Connect to mongos
mongodump --uri="mongodb://mongos1.example.com:27017" \
  --db=mydb \
  --out=/backup/
```

## mongodump Options

| Option | Description |
|--------|-------------|
| `--db` | Database to dump |
| `--collection` | Collection to dump |
| `--query='{"active":true}'` | Filter documents |
| `--gzip` | Compress output files |
| `--archive=file` | Single archive file output |
| `--oplog` | Include oplog for point-in-time |
| `--numParallelCollections=4` | Parallel collection dumps |
| `--excludeCollection=col` | Skip collection |
| `--dumpDbUsersAndRoles` | Include users/roles |

## Restore Methods

### mongorestore

**From Directory:**

```bash
mongorestore --uri="mongodb://localhost:27017" /backup/mydb/
```

**To Different Database:**

```bash
mongorestore --uri="mongodb://localhost:27017" \
  --nsFrom="mydb.*" \
  --nsTo="mydb_restored.*" \
  /backup/mydb/
```

**From Archive:**

```bash
mongorestore --uri="mongodb://localhost:27017" \
  --archive=/backup/mydb.archive \
  --gzip
```

**Drop Collections First:**

```bash
mongorestore --uri="mongodb://localhost:27017" \
  --drop \
  /backup/mydb/
```

**Single Collection:**

```bash
mongorestore --uri="mongodb://localhost:27017" \
  --db=mydb \
  --collection=users \
  /backup/mydb/users.bson
```

## mongorestore Options

| Option | Description |
|--------|-------------|
| `--drop` | Drop collections before restore |
| `--noIndexRestore` | Skip index creation |
| `--numParallelCollections=4` | Parallel restore |
| `--numInsertionWorkersPerCollection=4` | Parallel inserts |
| `--stopOnError` | Stop on first error |
| `--maintainInsertionOrder` | Preserve document order |

## Point-in-Time Recovery

### With Oplog

**Backup with oplog:**

```bash
mongodump --uri="mongodb://localhost:27017" \
  --oplog \
  --out=/backup/full_with_oplog
```

**Restore to specific time:**

```bash
mongorestore --uri="mongodb://localhost:27017" \
  --oplogReplay \
  --oplogLimit="1642248000:1" \
  /backup/full_with_oplog
```

## Production Backup Script

```bash
#!/bin/bash
set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/mongodb"
RETENTION_DAYS=7
MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
DB_NAME="production"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${DB_NAME}_${DATE}"
LOG_FILE="${BACKUP_DIR}/backup.log"

mkdir -p "$BACKUP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting backup of $DB_NAME"

# Perform backup
if mongodump --uri="$MONGO_URI" \
    --db="$DB_NAME" \
    --gzip \
    --out="$BACKUP_PATH" 2>> "$LOG_FILE"; then

    SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    log "Backup completed: $BACKUP_PATH ($SIZE)"

    # Verify backup
    BSON_COUNT=$(find "$BACKUP_PATH" -name "*.bson.gz" | wc -l)
    if [ "$BSON_COUNT" -gt 0 ]; then
        log "Backup verification passed ($BSON_COUNT collections)"
    else
        log "WARNING: No BSON files found in backup"
    fi
else
    log "ERROR: Backup failed"
    rm -rf "$BACKUP_PATH"
    exit 1
fi

# Create tar archive
log "Creating archive..."
tar -cf "${BACKUP_PATH}.tar" -C "$BACKUP_DIR" "${DB_NAME}_${DATE}"
rm -rf "$BACKUP_PATH"
log "Archive created: ${BACKUP_PATH}.tar"

# Cleanup old backups
log "Cleaning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "*.tar" -mtime "+$RETENTION_DAYS" -delete

log "Backup process completed"
```

## Cloud Backup (Atlas)

For MongoDB Atlas, use the built-in backup or:

```bash
# Backup Atlas cluster
mongodump --uri="mongodb+srv://user:pass@cluster.mongodb.net/mydb" \
  --gzip \
  --out=/backup/atlas_$(date +%Y%m%d)
```

## Backup User Setup

```javascript
use admin
db.createUser({
  user: "backup",
  pwd: "secure_password",
  roles: [
    { role: "backup", db: "admin" },
    { role: "restore", db: "admin" }
  ]
})
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Check user credentials and authSource |
| Connection timeout | Increase `--socketTimeoutMS` |
| Oplog overflow | More frequent backups or larger oplog |
| Restore fails on indexes | Use `--noIndexRestore`, create indexes after |
| Memory issues | Reduce `--numParallelCollections` |
| Sharded cluster issues | Run mongodump against mongos, not individual shards |

## Selective Backup/Restore

**Query-based backup:**

```bash
mongodump --uri="mongodb://localhost:27017" \
  --db=mydb \
  --collection=orders \
  --query='{"status":"completed","date":{"$gte":{"$date":"2025-01-01T00:00:00Z"}}}'
```

**Exclude collections:**

```bash
mongodump --uri="mongodb://localhost:27017" \
  --db=mydb \
  --excludeCollection=logs \
  --excludeCollection=sessions
```
