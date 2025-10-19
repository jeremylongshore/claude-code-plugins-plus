---
name: fairdb-emergency-response
description: Emergency incident response procedures for critical FairDB issues
model: sonnet
---

# FairDB Emergency Incident Response

You are responding to a critical incident in the FairDB PostgreSQL infrastructure. Follow this structured approach to diagnose, contain, and resolve the issue.

## Incident Classification

First, identify the incident type:
- **P1 Critical**: Complete service outage, data loss risk
- **P2 High**: Major degradation, affecting multiple customers
- **P3 Medium**: Single customer impact, performance issues
- **P4 Low**: Minor issues, cosmetic problems

## Initial Assessment (First 5 Minutes)

```bash
#!/bin/bash
# FairDB Emergency Response Script

echo "================================================"
echo "    FAIRDB EMERGENCY INCIDENT RESPONSE"
echo "    Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"

# Create incident log
INCIDENT_ID="INC-$(date +%Y%m%d-%H%M%S)"
INCIDENT_LOG="/opt/fairdb/incidents/${INCIDENT_ID}.log"
mkdir -p /opt/fairdb/incidents

{
    echo "Incident ID: $INCIDENT_ID"
    echo "Response started: $(date)"
    echo "Responding user: $(whoami)"
    echo "========================================"
} | tee $INCIDENT_LOG
```

## Step 1: Service Status Check

```bash
echo -e "\n[STEP 1] SERVICE STATUS CHECK" | tee -a $INCIDENT_LOG
echo "------------------------------" | tee -a $INCIDENT_LOG

# Check PostgreSQL service
if systemctl is-active --quiet postgresql; then
    echo "✅ PostgreSQL: RUNNING" | tee -a $INCIDENT_LOG
else
    echo "❌ CRITICAL: PostgreSQL is DOWN" | tee -a $INCIDENT_LOG
    echo "Attempting emergency restart..." | tee -a $INCIDENT_LOG

    # Try to start the service
    sudo systemctl start postgresql 2>&1 | tee -a $INCIDENT_LOG

    sleep 5

    if systemctl is-active --quiet postgresql; then
        echo "✅ PostgreSQL restarted successfully" | tee -a $INCIDENT_LOG
    else
        echo "❌ FAILED to restart PostgreSQL" | tee -a $INCIDENT_LOG
        echo "Checking for port conflicts..." | tee -a $INCIDENT_LOG
        sudo netstat -tulpn | grep :5432 | tee -a $INCIDENT_LOG

        # Check for corruption
        echo "Checking for data corruption..." | tee -a $INCIDENT_LOG
        sudo -u postgres /usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/16/main -C data_directory 2>&1 | tee -a $INCIDENT_LOG
    fi
fi

# Check disk space
echo -e "\nDisk Space:" | tee -a $INCIDENT_LOG
df -h | grep -E "^/dev|^Filesystem" | tee -a $INCIDENT_LOG

# Check for full disks
FULL_DISKS=$(df -h | grep -E "100%|9[5-9]%" | wc -l)
if [ $FULL_DISKS -gt 0 ]; then
    echo "⚠️  CRITICAL: Disk space exhausted!" | tee -a $INCIDENT_LOG
    echo "Emergency cleanup required..." | tee -a $INCIDENT_LOG

    # Emergency log cleanup
    find /var/log/postgresql -name "*.log" -mtime +7 -delete 2>/dev/null
    find /opt/fairdb/logs -name "*.log" -mtime +7 -delete 2>/dev/null

    echo "Old logs cleared. New disk usage:" | tee -a $INCIDENT_LOG
    df -h | grep -E "^/dev" | tee -a $INCIDENT_LOG
fi
```

## Step 2: Connection Diagnostics

```bash
echo -e "\n[STEP 2] CONNECTION DIAGNOSTICS" | tee -a $INCIDENT_LOG
echo "--------------------------------" | tee -a $INCIDENT_LOG

# Test local connection
echo "Testing local connection..." | tee -a $INCIDENT_LOG
if sudo -u postgres psql -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Local connections: OK" | tee -a $INCIDENT_LOG

    # Get connection stats
    sudo -u postgres psql -t -c "
        SELECT 'Active connections: ' || count(*)
        FROM pg_stat_activity
        WHERE state != 'idle';" | tee -a $INCIDENT_LOG

    # Check for connection exhaustion
    MAX_CONN=$(sudo -u postgres psql -t -c "SHOW max_connections;")
    CURRENT_CONN=$(sudo -u postgres psql -t -c "SELECT count(*) FROM pg_stat_activity;")

    echo "Connections: $CURRENT_CONN / $MAX_CONN" | tee -a $INCIDENT_LOG

    if [ $CURRENT_CONN -gt $(( MAX_CONN * 90 / 100 )) ]; then
        echo "⚠️  WARNING: Connection pool nearly exhausted" | tee -a $INCIDENT_LOG
        echo "Terminating idle connections..." | tee -a $INCIDENT_LOG

        # Kill idle connections older than 10 minutes
        sudo -u postgres psql << 'EOF' | tee -a $INCIDENT_LOG
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE state = 'idle'
        AND state_change < NOW() - INTERVAL '10 minutes'
        AND pid != pg_backend_pid();
EOF
    fi
else
    echo "❌ CRITICAL: Cannot connect to PostgreSQL" | tee -a $INCIDENT_LOG
    echo "Checking PostgreSQL logs..." | tee -a $INCIDENT_LOG
    tail -50 /var/log/postgresql/postgresql-*.log | tee -a $INCIDENT_LOG
fi

# Check network connectivity
echo -e "\nNetwork status:" | tee -a $INCIDENT_LOG
ip addr show | grep "inet " | tee -a $INCIDENT_LOG
```

## Step 3: Performance Emergency Response

```bash
echo -e "\n[STEP 3] PERFORMANCE TRIAGE" | tee -a $INCIDENT_LOG
echo "----------------------------" | tee -a $INCIDENT_LOG

# Find and kill long-running queries
echo "Checking for blocked/long queries..." | tee -a $INCIDENT_LOG

sudo -u postgres psql << 'EOF' | tee -a $INCIDENT_LOG
-- Queries running longer than 5 minutes
SELECT
    pid,
    now() - query_start as duration,
    state,
    LEFT(query, 100) as query_preview
FROM pg_stat_activity
WHERE state != 'idle'
AND now() - query_start > interval '5 minutes'
ORDER BY duration DESC;

-- Kill queries running longer than 30 minutes
SELECT pg_cancel_backend(pid)
FROM pg_stat_activity
WHERE state != 'idle'
AND now() - query_start > interval '30 minutes'
AND pid != pg_backend_pid();
EOF

# Check for locks
echo -e "\nChecking for lock conflicts..." | tee -a $INCIDENT_LOG
sudo -u postgres psql << 'EOF' | tee -a $INCIDENT_LOG
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.GRANTED;
EOF
```

## Step 4: Data Integrity Check

```bash
echo -e "\n[STEP 4] DATA INTEGRITY CHECK" | tee -a $INCIDENT_LOG
echo "------------------------------" | tee -a $INCIDENT_LOG

# Check for corruption indicators
echo "Checking for corruption indicators..." | tee -a $INCIDENT_LOG

# Check PostgreSQL data directory
DATA_DIR="/var/lib/postgresql/16/main"
if [ -d "$DATA_DIR" ]; then
    echo "Data directory exists: $DATA_DIR" | tee -a $INCIDENT_LOG

    # Check for recovery in progress
    if [ -f "$DATA_DIR/recovery.signal" ]; then
        echo "⚠️  Recovery in progress!" | tee -a $INCIDENT_LOG
    fi

    # Check WAL status
    WAL_COUNT=$(ls -1 $DATA_DIR/pg_wal/*.partial 2>/dev/null | wc -l)
    if [ $WAL_COUNT -gt 0 ]; then
        echo "⚠️  Partial WAL files detected: $WAL_COUNT" | tee -a $INCIDENT_LOG
    fi
else
    echo "❌ CRITICAL: Data directory not found!" | tee -a $INCIDENT_LOG
fi

# Run basic integrity check
echo -e "\nRunning integrity checks..." | tee -a $INCIDENT_LOG
for DB in $(sudo -u postgres psql -t -c "SELECT datname FROM pg_database WHERE datistemplate = false;"); do
    echo "Checking database: $DB" | tee -a $INCIDENT_LOG
    sudo -u postgres psql -d $DB -c "SELECT 1;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✅ Database $DB is accessible" | tee -a $INCIDENT_LOG
    else
        echo "  ❌ Database $DB has issues!" | tee -a $INCIDENT_LOG
    fi
done
```

## Step 5: Emergency Recovery Actions

```bash
echo -e "\n[STEP 5] RECOVERY ACTIONS" | tee -a $INCIDENT_LOG
echo "-------------------------" | tee -a $INCIDENT_LOG

# Determine if recovery is needed
read -p "Do you need to initiate emergency recovery? (yes/no): " NEED_RECOVERY

if [ "$NEED_RECOVERY" = "yes" ]; then
    echo "Starting emergency recovery procedures..." | tee -a $INCIDENT_LOG

    # Option 1: Restart in single-user mode for repairs
    echo "Option 1: Single-user mode repair" | tee -a $INCIDENT_LOG
    echo "Command: sudo -u postgres /usr/lib/postgresql/16/bin/postgres --single -D $DATA_DIR" | tee -a $INCIDENT_LOG

    # Option 2: Restore from backup
    echo "Option 2: Restore from backup" | tee -a $INCIDENT_LOG

    # Check available backups
    if command -v pgbackrest &> /dev/null; then
        echo "Available backups:" | tee -a $INCIDENT_LOG
        sudo -u postgres pgbackrest --stanza=fairdb info 2>&1 | tee -a $INCIDENT_LOG
    fi

    # Option 3: Point-in-time recovery
    echo "Option 3: Point-in-time recovery" | tee -a $INCIDENT_LOG
    echo "Use: /opt/fairdb/scripts/restore-pitr.sh 'YYYY-MM-DD HH:MM:SS'" | tee -a $INCIDENT_LOG

    read -p "Select recovery option (1/2/3/none): " RECOVERY_OPTION

    case $RECOVERY_OPTION in
        1)
            echo "Starting single-user mode..." | tee -a $INCIDENT_LOG
            sudo systemctl stop postgresql
            sudo -u postgres /usr/lib/postgresql/16/bin/postgres --single -D $DATA_DIR
            ;;
        2)
            echo "Starting backup restore..." | tee -a $INCIDENT_LOG
            read -p "Enter backup label to restore: " BACKUP_LABEL
            sudo systemctl stop postgresql
            sudo -u postgres pgbackrest --stanza=fairdb --set=$BACKUP_LABEL restore
            sudo systemctl start postgresql
            ;;
        3)
            echo "Starting PITR..." | tee -a $INCIDENT_LOG
            read -p "Enter target time (YYYY-MM-DD HH:MM:SS): " TARGET_TIME
            /opt/fairdb/scripts/restore-pitr.sh "$TARGET_TIME"
            ;;
        *)
            echo "No recovery action taken" | tee -a $INCIDENT_LOG
            ;;
    esac
fi
```

## Step 6: Customer Communication

```bash
echo -e "\n[STEP 6] CUSTOMER IMPACT ASSESSMENT" | tee -a $INCIDENT_LOG
echo "------------------------------------" | tee -a $INCIDENT_LOG

# Identify affected customers
echo "Affected customer databases:" | tee -a $INCIDENT_LOG

AFFECTED_DBS=$(sudo -u postgres psql -t -c "
    SELECT datname FROM pg_database
    WHERE datname NOT IN ('postgres', 'template0', 'template1')
    ORDER BY datname;")

for DB in $AFFECTED_DBS; do
    # Check if database is accessible
    if sudo -u postgres psql -d $DB -c "SELECT 1;" > /dev/null 2>&1; then
        echo "  ✅ $DB - Operational" | tee -a $INCIDENT_LOG
    else
        echo "  ❌ $DB - IMPACTED" | tee -a $INCIDENT_LOG
    fi
done

# Generate customer notification
cat << EOF | tee -a $INCIDENT_LOG

CUSTOMER NOTIFICATION TEMPLATE
===============================
Subject: FairDB Service Incident - $INCIDENT_ID

Dear Customer,

We are currently experiencing a service incident affecting FairDB PostgreSQL services.

Incident ID: $INCIDENT_ID
Start Time: $(date)
Severity: [P1/P2/P3/P4]
Status: Investigating / Identified / Monitoring / Resolved

Impact:
[Describe customer impact]

Current Actions:
[List recovery actions being taken]

Next Update:
We will provide an update within 30 minutes or sooner if the situation changes.

We apologize for any inconvenience and are working to resolve this as quickly as possible.

For urgent matters, please contact our emergency hotline: [PHONE]

Regards,
FairDB Operations Team
EOF
```

## Step 7: Post-Incident Checklist

```bash
echo -e "\n[STEP 7] STABILIZATION CHECKLIST" | tee -a $INCIDENT_LOG
echo "---------------------------------" | tee -a $INCIDENT_LOG

# Verification checklist
cat << 'EOF' | tee -a $INCIDENT_LOG
Post-Recovery Verification:
[ ] PostgreSQL service running
[ ] All customer databases accessible
[ ] Backup system operational
[ ] Monitoring alerts cleared
[ ] Network connectivity verified
[ ] Disk space adequate (>20% free)
[ ] CPU usage normal (<80%)
[ ] Memory usage normal (<90%)
[ ] No blocking locks
[ ] No long-running queries
[ ] Recent backup available
[ ] Customer access verified
[ ] Incident documented
[ ] Root cause identified
[ ] Prevention plan created
EOF

# Final status
echo -e "\n[FINAL STATUS]" | tee -a $INCIDENT_LOG
echo "==============" | tee -a $INCIDENT_LOG
/usr/local/bin/fairdb-health-check | head -20 | tee -a $INCIDENT_LOG
```

## Step 8: Root Cause Analysis

```bash
echo -e "\n[STEP 8] ROOT CAUSE ANALYSIS" | tee -a $INCIDENT_LOG
echo "-----------------------------" | tee -a $INCIDENT_LOG

# Collect evidence
echo "Collecting evidence for RCA..." | tee -a $INCIDENT_LOG

# System logs
echo -e "\nSystem logs (last hour):" | tee -a $INCIDENT_LOG
sudo journalctl --since "1 hour ago" -p err --no-pager | tail -20 | tee -a $INCIDENT_LOG

# PostgreSQL logs
echo -e "\nPostgreSQL error logs:" | tee -a $INCIDENT_LOG
find /var/log/postgresql -name "*.log" -mmin -60 -exec grep -i "error\|fatal\|panic" {} \; | tail -20 | tee -a $INCIDENT_LOG

# Resource history
echo -e "\nResource usage history:" | tee -a $INCIDENT_LOG
sar -u -f /var/log/sysstat/sa$(date +%d) | tail -10 | tee -a $INCIDENT_LOG 2>/dev/null

# Create RCA document
cat << EOF | tee /opt/fairdb/incidents/${INCIDENT_ID}-rca.md
# Root Cause Analysis - $INCIDENT_ID

## Incident Summary
- **Date/Time**: $(date)
- **Duration**: [TO BE FILLED]
- **Severity**: [P1/P2/P3/P4]
- **Impact**: [Number of customers/databases affected]

## Timeline
[Document sequence of events]

## Root Cause
[Identify primary cause]

## Contributing Factors
[List any contributing factors]

## Resolution
[Describe how the incident was resolved]

## Lessons Learned
[What was learned from this incident]

## Action Items
[ ] [Prevention measure 1]
[ ] [Prevention measure 2]
[ ] [Monitoring improvement]

## Metrics
- Time to Detection: [minutes]
- Time to Resolution: [minutes]
- Customer Impact Duration: [minutes]

Generated: $(date)
EOF

echo -e "\n================================================" | tee -a $INCIDENT_LOG
echo "    INCIDENT RESPONSE COMPLETED" | tee -a $INCIDENT_LOG
echo "    Incident ID: $INCIDENT_ID" | tee -a $INCIDENT_LOG
echo "    Log saved to: $INCIDENT_LOG" | tee -a $INCIDENT_LOG
echo "    RCA template: /opt/fairdb/incidents/${INCIDENT_ID}-rca.md" | tee -a $INCIDENT_LOG
echo "================================================" | tee -a $INCIDENT_LOG
```

## Emergency Contacts

Keep these contacts readily available:
- PostgreSQL Expert: [Contact info]
- Infrastructure Team: [Contact info]
- Customer Success: [Contact info]
- Management Escalation: [Contact info]

## Quick Reference Commands

```bash
# Emergency service control
sudo systemctl stop postgresql
sudo systemctl start postgresql
sudo systemctl restart postgresql

# Kill all connections
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid != pg_backend_pid();"

# Emergency single-user mode
sudo -u postgres /usr/lib/postgresql/16/bin/postgres --single -D /var/lib/postgresql/16/main

# Force checkpoint
sudo -u postgres psql -c "CHECKPOINT;"

# Emergency vacuum
sudo -u postgres vacuumdb --all --analyze-in-stages

# Check data checksums
sudo -u postgres /usr/lib/postgresql/16/bin/pg_checksums -D /var/lib/postgresql/16/main --check
```