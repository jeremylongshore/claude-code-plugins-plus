# Database Backup Best Practices

## The 3-2-1 Backup Rule

- **3** copies of data
- **2** different storage media
- **1** offsite location

```
Primary Database
       │
       ├──► Local Backup (NAS/SAN)
       │
       ├──► Remote Backup (S3/GCS)
       │
       └──► Archive (Tape/Glacier)
```

## Backup Types

### Full Backup

Complete copy of entire database.

| Pros | Cons |
|------|------|
| Simple to restore | Large storage |
| Self-contained | Long backup time |
| No dependencies | Network bandwidth |

### Incremental Backup

Only changes since last backup (any type).

| Pros | Cons |
|------|------|
| Fast backup | Complex restore (need all incrementals) |
| Small size | Single corrupt file breaks chain |
| Less I/O | More restore time |

### Differential Backup

Changes since last full backup.

| Pros | Cons |
|------|------|
| Simpler than incremental | Grows larger over time |
| Only need full + latest diff | Still requires full backup |
| Faster restore than incremental | More storage than incremental |

## Recommended Strategy

```
Week 1:
  Sun: Full backup (retain 4 weeks)
  Mon-Sat: Daily incremental

Monthly:
  1st: Monthly full (retain 12 months)

Yearly:
  Jan 1: Annual archive (retain 7 years)
```

## Security Best Practices

### Encryption

**At Rest:**

```bash
# GPG encryption
pg_dump mydb | gzip | gpg --symmetric --cipher-algo AES256 -o backup.sql.gz.gpg

# OpenSSL encryption
pg_dump mydb | gzip | openssl enc -aes-256-cbc -salt -pbkdf2 -out backup.sql.gz.enc
```

**In Transit:**

```bash
# Use SSL/TLS for remote connections
pg_dump "host=remote.server.com sslmode=require" ...
```

### Key Management

1. **Never** store encryption keys with backups
2. Use separate key storage (HashiCorp Vault, AWS KMS, GCP KMS)
3. Rotate keys periodically
4. Document key recovery procedure

```bash
# Example: Using AWS KMS
aws kms encrypt --key-id alias/backup-key \
  --plaintext fileb://backup.key \
  --output text --query CiphertextBlob > backup.key.encrypted
```

### Access Control

```sql
-- PostgreSQL: Dedicated backup user
CREATE USER backup_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE mydb TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;

-- MySQL: Backup-only privileges
CREATE USER 'backup'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT, SHOW VIEW, TRIGGER, LOCK TABLES ON *.* TO 'backup'@'localhost';
```

## Testing and Validation

### Regular Restore Testing

```bash
#!/bin/bash
# Monthly restore test
TEST_DB="restore_test_$(date +%Y%m)"

# Create test database
createdb "$TEST_DB"

# Restore latest backup
pg_restore -d "$TEST_DB" /backup/latest.dump

# Run validation queries
psql -d "$TEST_DB" -c "SELECT COUNT(*) FROM users;"

# Compare row counts with production
PROD_COUNT=$(psql -d production -t -c "SELECT COUNT(*) FROM users;")
TEST_COUNT=$(psql -d "$TEST_DB" -t -c "SELECT COUNT(*) FROM users;")

if [ "$PROD_COUNT" -eq "$TEST_COUNT" ]; then
    echo "Restore validation PASSED"
else
    echo "Restore validation FAILED: $PROD_COUNT vs $TEST_COUNT"
fi

# Cleanup
dropdb "$TEST_DB"
```

### Checksum Verification

```bash
# Create checksum during backup
pg_dump mydb | tee backup.sql | sha256sum > backup.sql.sha256

# Verify before restore
sha256sum -c backup.sql.sha256
```

## Monitoring and Alerting

### Key Metrics

| Metric | Alert Threshold |
|--------|-----------------|
| Backup duration | > 150% of average |
| Backup size | < 50% or > 150% of expected |
| Storage usage | > 80% capacity |
| Time since last backup | > configured interval |
| Restore test age | > 30 days |

### Backup Monitoring Script

```bash
#!/bin/bash
# backup_monitor.sh

BACKUP_DIR="/var/backups/postgresql"
MAX_AGE_HOURS=25  # Alert if backup older than this
MIN_SIZE_MB=100   # Alert if backup smaller than this

# Check latest backup age
LATEST=$(find "$BACKUP_DIR" -name "*.dump" -type f -printf '%T@\n' | sort -n | tail -1)
AGE_HOURS=$(( ($(date +%s) - ${LATEST%.*}) / 3600 ))

if [ "$AGE_HOURS" -gt "$MAX_AGE_HOURS" ]; then
    echo "ALERT: Last backup is $AGE_HOURS hours old"
    # Send alert (email, Slack, PagerDuty)
fi

# Check backup size
SIZE_MB=$(du -m "$BACKUP_DIR"/*.dump 2>/dev/null | tail -1 | cut -f1)
if [ "$SIZE_MB" -lt "$MIN_SIZE_MB" ]; then
    echo "ALERT: Backup size ($SIZE_MB MB) below threshold ($MIN_SIZE_MB MB)"
fi

# Check disk space
USAGE=$(df "$BACKUP_DIR" | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$USAGE" -gt 80 ]; then
    echo "ALERT: Backup disk usage at $USAGE%"
fi
```

## Cloud Storage Integration

### AWS S3

```bash
# Upload to S3
aws s3 cp /backup/database.dump s3://my-backups/postgresql/

# With lifecycle policy for automatic transitions
# Configure in S3: Move to Glacier after 30 days, delete after 365

# Sync backup directory
aws s3 sync /backup/ s3://my-backups/postgresql/ --delete
```

### Google Cloud Storage

```bash
# Upload to GCS
gsutil cp /backup/database.dump gs://my-backups/postgresql/

# With retention policy
gsutil retention set 365d gs://my-backups/postgresql/
```

### Azure Blob Storage

```bash
# Upload to Azure
az storage blob upload \
  --container-name backups \
  --name postgresql/database.dump \
  --file /backup/database.dump
```

## Retention Policies

### Example Policy

```yaml
retention:
  hourly:
    keep: 24
    path: /backup/hourly
  daily:
    keep: 7
    path: /backup/daily
  weekly:
    keep: 4
    path: /backup/weekly
  monthly:
    keep: 12
    path: /backup/monthly
  yearly:
    keep: 7
    path: /backup/yearly
```

### Cleanup Script

```bash
#!/bin/bash
# cleanup_backups.sh

# Daily: Keep 7 days
find /backup/daily -name "*.dump" -mtime +7 -delete

# Weekly: Keep 4 weeks
find /backup/weekly -name "*.dump" -mtime +28 -delete

# Monthly: Keep 12 months
find /backup/monthly -name "*.dump" -mtime +365 -delete

# Log deleted files
echo "$(date): Cleanup completed" >> /var/log/backup_cleanup.log
```

## Disaster Recovery Checklist

### RTO/RPO Definition

| Tier | RPO | RTO | Example |
|------|-----|-----|---------|
| Critical | < 1 hour | < 15 min | Payment database |
| Important | < 4 hours | < 1 hour | User data |
| Standard | < 24 hours | < 4 hours | Logs, analytics |
| Archive | < 1 week | < 24 hours | Historical data |

### Recovery Procedure Document

```markdown
# Database Recovery Procedure

## Pre-Recovery Checklist
- [ ] Identify failure scope
- [ ] Notify stakeholders
- [ ] Prepare recovery environment
- [ ] Locate latest verified backup

## Recovery Steps
1. Stop dependent applications
2. Assess current database state
3. Select appropriate backup
4. Execute restore procedure
5. Verify data integrity
6. Test application connectivity
7. Resume operations

## Post-Recovery
- [ ] Document incident
- [ ] Update runbooks
- [ ] Review backup strategy
```

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Never tested restores | Monthly restore drills |
| Backups on same disk | Use separate storage/offsite |
| No encryption | Always encrypt sensitive data |
| No monitoring | Implement backup alerts |
| Incomplete backups | Include schema, procedures, permissions |
| No documentation | Maintain runbooks |
| Stale backups | Monitor backup freshness |
