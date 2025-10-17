---
name: incident-p0-disk-full
description: Emergency response for SOP-203 P0 - Disk Space Emergency
model: sonnet
---

# SOP-203: P0 - Disk Space Emergency

🚨 **CRITICAL: Disk Space at 100% or >95%**

You are responding to a **disk space emergency** that threatens database operations.

## Severity: P0 - CRITICAL
- **Impact:** Database writes failing, potential data loss
- **Response Time:** IMMEDIATE
- **Resolution Target:** <30 minutes

## IMMEDIATE DANGER SIGNS

If disk is at 100%:
- ❌ PostgreSQL cannot write data
- ❌ WAL files cannot be created
- ❌ Transactions will fail
- ❌ Database may crash
- ❌ Backups will fail

**Act NOW to free space!**

## RAPID ASSESSMENT

### 1. Check Current Usage
```bash
# Overall disk usage
df -h

# PostgreSQL data directory
du -sh /var/lib/postgresql/16/main

# Find largest directories
du -sh /var/lib/postgresql/16/main/* | sort -rh | head -10

# Find largest files
find /var/lib/postgresql/16/main -type f -size +100M -exec ls -lh {} \; | sort -k5 -rh | head -20
```

### 2. Identify Culprits
```bash
# Check log sizes
du -sh /var/log/postgresql/

# Check WAL directory
du -sh /var/lib/postgresql/16/main/pg_wal/
ls -lh /var/lib/postgresql/16/main/pg_wal/ | wc -l

# Check for temp files
du -sh /tmp/
find /tmp -type f -size +10M -ls

# Database sizes
sudo -u postgres psql -c "
SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) AS size,
    pg_database_size(datname) AS size_bytes
FROM pg_database
ORDER BY size_bytes DESC;"
```

## EMERGENCY SPACE RECOVERY

### Priority 1: Clear Old Logs (SAFEST)

```bash
# PostgreSQL logs older than 7 days
sudo find /var/log/postgresql/ -name "*.log" -mtime +7 -delete

# Compress recent logs
sudo gzip /var/log/postgresql/*.log

# Clear syslog/journal
sudo journalctl --vacuum-time=7d

# Check space recovered
df -h
```

**Expected recovery:** 1-5 GB

### Priority 2: Archive Old WAL Files

⚠️ **ONLY if you have confirmed backups!**

```bash
# Check WAL retention settings
sudo -u postgres psql -c "SHOW wal_keep_size;"

# List old WAL files
ls -lh /var/lib/postgresql/16/main/pg_wal/ | tail -50

# Archive WAL files (pgBackRest will help)
sudo -u postgres pgbackrest --stanza=main --type=full backup

# Clean archived WALs (CAREFUL!)
sudo -u postgres pg_archivecleanup /var/lib/postgresql/16/main/pg_wal \
    $(ls /var/lib/postgresql/16/main/pg_wal/ | grep -v '\.history' | head -1)

# Check space
df -h
```

**Expected recovery:** 5-20 GB

### Priority 3: Vacuum Databases

```bash
# Quick vacuum (recovers space within tables)
sudo -u postgres vacuumdb --all --analyze

# Check largest tables
sudo -u postgres psql -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;"

# Full vacuum on bloated tables (SLOW, locks table)
sudo -u postgres psql -d [database] -c "VACUUM FULL [table_name];"

# Check space
df -h
```

**Expected recovery:** Variable, depends on bloat

### Priority 4: Remove Temp Files

```bash
# Clear PostgreSQL temp files
sudo rm -rf /var/lib/postgresql/16/main/pgsql_tmp/*

# Clear system temp
sudo rm -rf /tmp/*

# Clear old backups (if local copies exist)
ls -lh /opt/fairdb/backups/
# Delete old local backups if remote backups are confirmed

df -h
```

### Priority 5: Drop Old/Unused Databases (DANGER!)

⚠️ **ONLY with customer approval!**

```bash
# List databases and last access
sudo -u postgres psql -c "
SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) AS size,
    (SELECT max(query_start) FROM pg_stat_activity WHERE datname = d.datname) AS last_activity
FROM pg_database d
WHERE datname NOT IN ('template0', 'template1', 'postgres')
ORDER BY pg_database_size(datname) DESC;"

# Identify inactive databases (last_activity is NULL or very old)

# BEFORE DROPPING: Backup!
sudo -u postgres pg_dump [database_name] | gzip > /opt/fairdb/backups/emergency-backup-[database_name].sql.gz

# Drop database (IRREVERSIBLE!)
sudo -u postgres psql -c "DROP DATABASE [database_name];"
```

## LONG-TERM SOLUTIONS

### Option 1: Increase Disk Size

**Contabo/VPS Provider:**
1. Log into provider control panel
2. Upgrade storage plan
3. Resize disk partition
4. Expand filesystem

```bash
# After resize, expand filesystem
sudo resize2fs /dev/sda1  # Adjust device as needed

# Verify
df -h
```

### Option 2: Move Data to External Volume

```bash
# Create new volume/mount point
# Move PostgreSQL data directory
sudo systemctl stop postgresql
sudo rsync -av /var/lib/postgresql/ /mnt/new-volume/postgresql/
sudo mv /var/lib/postgresql /var/lib/postgresql.old
sudo ln -s /mnt/new-volume/postgresql /var/lib/postgresql
sudo systemctl start postgresql
```

### Option 3: Offload Old Data

- Archive old customer databases
- Export historical data to cold storage
- Implement data retention policies

### Option 4: Optimize Storage

```bash
# Enable compression for tables (PostgreSQL 14+)
ALTER TABLE [table_name] SET COMPRESSION lz4;

# Rewrite table to apply compression
VACUUM FULL [table_name];

# Set autovacuum more aggressively
ALTER TABLE [table_name] SET (autovacuum_vacuum_scale_factor = 0.05);
```

## MONITORING & PREVENTION

### Set Up Disk Monitoring

Add to cron (`crontab -e`):
```bash
# Check disk space every hour
0 * * * * /opt/fairdb/scripts/check-disk-space.sh
```

**Create script** `/opt/fairdb/scripts/check-disk-space.sh`:
```bash
#!/bin/bash
THRESHOLD=80
USAGE=$(df -h /var/lib/postgresql | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$USAGE" -gt "$THRESHOLD" ]; then
    echo "WARNING: Disk usage at ${USAGE}%" | mail -s "FairDB Disk Warning" your-email@example.com
fi
```

### Configure Log Rotation

Edit `/etc/logrotate.d/postgresql`:
```
/var/log/postgresql/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
}
```

### Implement Database Quotas

```sql
-- Set database size limits
ALTER DATABASE customer_db_001 SET max_database_size = '10GB';
```

## POST-RECOVERY ACTIONS

### 1. Verify Database Health
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connections
sudo -u postgres psql -c "SELECT 1;"

# Run health check
/opt/fairdb/scripts/pg-health-check.sh
```

### 2. Document Incident

```markdown
# Disk Space Emergency - YYYY-MM-DD

## Initial State
- Disk usage: X%
- Free space: XGB
- Affected services: [list]

## Actions Taken
- [List each action with space recovered]

## Final State
- Disk usage: X%
- Free space: XGB
- Time to resolution: X minutes

## Root Cause
[Why did disk fill up?]

## Prevention
- [ ] Implement monitoring
- [ ] Set up log rotation
- [ ] Schedule regular cleanups
- [ ] Consider storage upgrade
```

### 3. Implement Monitoring

```bash
# Install monitoring script
sudo cp /opt/fairdb/scripts/check-disk-space.sh /etc/cron.hourly/

# Set up alerts
# (Configure email/Slack notifications)
```

## DECISION TREE

```
Disk at 100%?
├─ Yes → Priority 1 & 2 (Logs + WAL) IMMEDIATELY
│   ├─ Space freed? → Continue to monitoring
│   └─ Still full? → Priority 3 (Vacuum) + Consider Priority 5
│
└─ Disk at 85-99%?
    ├─ Priority 1 (Logs) + Schedule Priority 3 (Vacuum)
    └─ Plan long-term solution (resize disk)
```

## START RESPONSE

Ask user:
1. "What is the current disk usage? (run `df -h`)"
2. "Is PostgreSQL still running?"
3. "When did this start happening?"

Then immediately execute Rapid Assessment and Emergency Space Recovery procedures.

**Remember:** Time is critical. Database writes are failing. Act fast but safely!
