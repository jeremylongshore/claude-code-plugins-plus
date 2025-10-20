---
name: fairdb-setup-backup
description: Configure pgBackRest with Wasabi S3 for automated PostgreSQL backups
model: sonnet
---

# FairDB pgBackRest Backup Configuration with Wasabi S3

You are configuring pgBackRest with Wasabi S3 storage for automated PostgreSQL backups. Follow SOP-003 precisely.

## Prerequisites Check

Verify before starting:
1. PostgreSQL 16 is installed and running
2. Wasabi S3 account is active with bucket created
3. AWS CLI credentials are available
4. At least 50GB free disk space for local backups

## Step 1: Install pgBackRest

```bash
# Add pgBackRest repository
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:pgbackrest/backrest
sudo apt-get update

# Install pgBackRest
sudo apt-get install -y pgbackrest

# Verify installation
pgbackrest version
```

## Step 2: Configure Wasabi S3 Credentials

```bash
# Create pgBackRest configuration directory
sudo mkdir -p /etc/pgbackrest
sudo mkdir -p /var/lib/pgbackrest
sudo mkdir -p /var/log/pgbackrest
sudo mkdir -p /var/spool/pgbackrest

# Set ownership
sudo chown -R postgres:postgres /var/lib/pgbackrest
sudo chown -R postgres:postgres /var/log/pgbackrest
sudo chown -R postgres:postgres /var/spool/pgbackrest

# Store Wasabi credentials (secure these!)
export WASABI_ACCESS_KEY="YOUR_WASABI_ACCESS_KEY"
export WASABI_SECRET_KEY="YOUR_WASABI_SECRET_KEY"
export WASABI_BUCKET="fairdb-backups"
export WASABI_REGION="us-east-1"  # Or your Wasabi region
export WASABI_ENDPOINT="s3.us-east-1.wasabisys.com"  # Adjust for your region
```

## Step 3: Create pgBackRest Configuration

```bash
# Create main configuration file
sudo tee /etc/pgbackrest/pgbackrest.conf << EOF
[global]
# General Options
process-max=4
log-level-console=info
log-level-file=detail
start-fast=y
stop-auto=y
archive-async=y
archive-push-queue-max=4GB
spool-path=/var/spool/pgbackrest

# S3 Repository Configuration
repo1-type=s3
repo1-s3-endpoint=${WASABI_ENDPOINT}
repo1-s3-bucket=${WASABI_BUCKET}
repo1-s3-region=${WASABI_REGION}
repo1-s3-key=${WASABI_ACCESS_KEY}
repo1-s3-key-secret=${WASABI_SECRET_KEY}
repo1-path=/pgbackrest
repo1-retention-full=4
repo1-retention-diff=12
repo1-retention-archive=30
repo1-cipher-type=aes-256-cbc
repo1-cipher-pass=CHANGE_THIS_PASSPHRASE

# Local Repository (for faster restores)
repo2-type=posix
repo2-path=/var/lib/pgbackrest
repo2-retention-full=2
repo2-retention-diff=6

[fairdb]
# PostgreSQL Configuration
pg1-path=/var/lib/postgresql/16/main
pg1-port=5432
pg1-user=postgres

# Archive Configuration
archive-timeout=60
archive-check=y
backup-standby=n

# Backup Options
compress-type=lz4
compress-level=3
backup-user=backup_user
delta=y
process-max=2
EOF

# Secure the configuration file
sudo chmod 640 /etc/pgbackrest/pgbackrest.conf
sudo chown postgres:postgres /etc/pgbackrest/pgbackrest.conf
```

## Step 4: Configure PostgreSQL for pgBackRest

```bash
# Update PostgreSQL configuration
sudo tee -a /etc/postgresql/16/main/postgresql.conf << 'EOF'

# pgBackRest Archive Configuration
archive_mode = on
archive_command = 'pgbackrest --stanza=fairdb archive-push %p'
archive_timeout = 60
max_wal_senders = 3
wal_level = replica
wal_log_hints = on
EOF

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## Step 5: Initialize Backup Stanza

```bash
# Create the stanza
sudo -u postgres pgbackrest --stanza=fairdb stanza-create

# Verify stanza
sudo -u postgres pgbackrest --stanza=fairdb check
```

## Step 6: Create Backup Scripts

```bash
# Full backup script
sudo tee /opt/fairdb/scripts/backup-full.sh << 'EOF'
#!/bin/bash
set -e

LOG_FILE="/var/log/fairdb/backup-full-$(date +%Y%m%d-%H%M%S).log"
echo "Starting full backup at $(date)" | tee -a $LOG_FILE

# Perform full backup to both repositories
sudo -u postgres pgbackrest --stanza=fairdb --type=full --repo=1 backup 2>&1 | tee -a $LOG_FILE
sudo -u postgres pgbackrest --stanza=fairdb --type=full --repo=2 backup 2>&1 | tee -a $LOG_FILE

# Verify backup
sudo -u postgres pgbackrest --stanza=fairdb --repo=1 info 2>&1 | tee -a $LOG_FILE

echo "Full backup completed at $(date)" | tee -a $LOG_FILE

# Send notification (implement webhook/email here)
curl -X POST $FAIRDB_MONITORING_WEBHOOK \
  -H 'Content-Type: application/json' \
  -d "{\"text\":\"FairDB full backup completed successfully\"}" 2>/dev/null || true
EOF

# Incremental backup script
sudo tee /opt/fairdb/scripts/backup-incremental.sh << 'EOF'
#!/bin/bash
set -e

LOG_FILE="/var/log/fairdb/backup-incr-$(date +%Y%m%d-%H%M%S).log"
echo "Starting incremental backup at $(date)" | tee -a $LOG_FILE

# Perform incremental backup
sudo -u postgres pgbackrest --stanza=fairdb --type=incr --repo=1 backup 2>&1 | tee -a $LOG_FILE

echo "Incremental backup completed at $(date)" | tee -a $LOG_FILE
EOF

# Differential backup script
sudo tee /opt/fairdb/scripts/backup-differential.sh << 'EOF'
#!/bin/bash
set -e

LOG_FILE="/var/log/fairdb/backup-diff-$(date +%Y%m%d-%H%M%S).log"
echo "Starting differential backup at $(date)" | tee -a $LOG_FILE

# Perform differential backup
sudo -u postgres pgbackrest --stanza=fairdb --type=diff --repo=1 backup 2>&1 | tee -a $LOG_FILE

echo "Differential backup completed at $(date)" | tee -a $LOG_FILE
EOF

# Make scripts executable
sudo chmod +x /opt/fairdb/scripts/backup-*.sh
```

## Step 7: Schedule Automated Backups

```bash
# Add to root's crontab for automated backups
cat << 'EOF' | sudo tee /etc/cron.d/fairdb-backups
# FairDB Automated Backup Schedule
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Weekly full backup (Sunday 2 AM)
0 2 * * 0 root /opt/fairdb/scripts/backup-full.sh

# Daily differential backup (Mon-Sat 2 AM)
0 2 * * 1-6 root /opt/fairdb/scripts/backup-differential.sh

# Hourly incremental backup (business hours)
0 9-18 * * 1-5 root /opt/fairdb/scripts/backup-incremental.sh

# Backup verification (daily at 5 AM)
0 5 * * * postgres pgbackrest --stanza=fairdb --repo=1 check

# Archive expiration (daily at 3 AM)
0 3 * * * postgres pgbackrest --stanza=fairdb --repo=1 expire
EOF
```

## Step 8: Create Restore Procedures

```bash
# Point-in-time recovery script
sudo tee /opt/fairdb/scripts/restore-pitr.sh << 'EOF'
#!/bin/bash
# FairDB Point-in-Time Recovery Script

if [ $# -ne 1 ]; then
    echo "Usage: $0 'YYYY-MM-DD HH:MM:SS'"
    exit 1
fi

TARGET_TIME="$1"
BACKUP_PATH="/var/lib/postgresql/16/main"

echo "WARNING: This will restore the database to $TARGET_TIME"
echo "Current data will be LOST. Continue? (yes/no)"
read CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 1
fi

# Stop PostgreSQL
sudo systemctl stop postgresql

# Clear data directory
sudo rm -rf ${BACKUP_PATH}/*

# Restore to target time
sudo -u postgres pgbackrest --stanza=fairdb \
    --type=time \
    --target="$TARGET_TIME" \
    --target-action=promote \
    restore

# Start PostgreSQL
sudo systemctl start postgresql

echo "Restore completed. Verify data integrity."
EOF

sudo chmod +x /opt/fairdb/scripts/restore-pitr.sh
```

## Step 9: Test Backup and Restore

```bash
# Perform test backup
sudo -u postgres pgbackrest --stanza=fairdb --type=full backup

# Check backup info
sudo -u postgres pgbackrest --stanza=fairdb info

# List backups
sudo -u postgres pgbackrest --stanza=fairdb info --output=json

# Test restore to alternate location
sudo mkdir -p /tmp/pgbackrest-test
sudo chown postgres:postgres /tmp/pgbackrest-test
sudo -u postgres pgbackrest --stanza=fairdb \
    --pg1-path=/tmp/pgbackrest-test \
    --type=latest \
    restore
```

## Step 10: Monitor Backup Health

```bash
# Create monitoring script
sudo tee /opt/fairdb/scripts/check-backup-health.sh << 'EOF'
#!/bin/bash
# FairDB Backup Health Check

# Check last backup time
LAST_BACKUP=$(sudo -u postgres pgbackrest --stanza=fairdb info --output=json | \
    jq -r '.[] | .backup[-1].timestamp.stop')

# Convert to seconds
LAST_BACKUP_EPOCH=$(date -d "$LAST_BACKUP" +%s)
CURRENT_EPOCH=$(date +%s)
HOURS_AGO=$(( ($CURRENT_EPOCH - $LAST_BACKUP_EPOCH) / 3600 ))

# Alert if backup is older than 25 hours
if [ $HOURS_AGO -gt 25 ]; then
    echo "ALERT: Last backup was $HOURS_AGO hours ago!"
    # Send alert (implement notification here)
    exit 1
fi

echo "Backup health OK - last backup $HOURS_AGO hours ago"

# Check S3 connectivity
aws s3 ls s3://${WASABI_BUCKET}/pgbackrest/ \
    --endpoint-url=https://${WASABI_ENDPOINT} > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ALERT: Cannot connect to Wasabi S3!"
    exit 1
fi

echo "S3 connectivity OK"
EOF

sudo chmod +x /opt/fairdb/scripts/check-backup-health.sh

# Add to monitoring cron
echo "*/30 * * * * root /opt/fairdb/scripts/check-backup-health.sh" | \
    sudo tee -a /etc/cron.d/fairdb-monitoring
```

## Step 11: Document Backup Configuration

```bash
cat > /opt/fairdb/configs/backup-info.txt << EOF
FairDB Backup Configuration
===========================
Backup Solution: pgBackRest
Primary Repository: Wasabi S3 (${WASABI_BUCKET})
Secondary Repository: Local (/var/lib/pgbackrest)
Stanza Name: fairdb
Encryption: AES-256-CBC

Retention Policy:
- Full Backups: 4 (S3), 2 (Local)
- Differential: 12 (S3), 6 (Local)
- WAL Archives: 30 days

Schedule:
- Full: Weekly (Sunday 2 AM)
- Differential: Daily (Mon-Sat 2 AM)
- Incremental: Hourly (9 AM - 6 PM weekdays)

Restore Procedures:
- Latest: pgbackrest --stanza=fairdb restore
- PITR: /opt/fairdb/scripts/restore-pitr.sh 'YYYY-MM-DD HH:MM:SS'

Monitoring:
- Health checks: Every 30 minutes
- Verification: Daily at 5 AM
- Expiration: Daily at 3 AM
EOF
```

## Verification Checklist

Confirm these items:
- [ ] pgBackRest installed and configured
- [ ] Wasabi S3 credentials configured
- [ ] Stanza created and verified
- [ ] PostgreSQL archive_command configured
- [ ] Backup scripts created and executable
- [ ] Automated schedule configured
- [ ] Test backup successful
- [ ] Test restore successful
- [ ] Monitoring scripts in place
- [ ] Documentation complete

## Security Notes

- Store Wasabi credentials securely (use AWS Secrets Manager in production)
- Encrypt backup repository with strong passphrase
- Regularly test restore procedures
- Monitor backup logs for failures
- Keep pgBackRest updated

## Output Summary

Provide the user with:
1. Backup stanza status: `pgbackrest --stanza=fairdb info`
2. Next full backup time from cron schedule
3. Location of backup scripts and logs
4. Restore procedure documentation
5. Monitoring webhook configuration needed

## Important Commands

```bash
# Manual backup commands
sudo -u postgres pgbackrest --stanza=fairdb --type=full backup      # Full
sudo -u postgres pgbackrest --stanza=fairdb --type=diff backup      # Differential
sudo -u postgres pgbackrest --stanza=fairdb --type=incr backup      # Incremental

# Check backup status
sudo -u postgres pgbackrest --stanza=fairdb info
sudo -u postgres pgbackrest --stanza=fairdb check

# Restore commands
sudo -u postgres pgbackrest --stanza=fairdb restore                 # Latest
sudo -u postgres pgbackrest --stanza=fairdb --type=time --target="2024-01-01 12:00:00" restore  # PITR
```