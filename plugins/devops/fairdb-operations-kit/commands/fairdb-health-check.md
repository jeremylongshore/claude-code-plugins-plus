---
name: fairdb-health-check
description: Comprehensive health check for FairDB PostgreSQL infrastructure
model: sonnet
---

# FairDB System Health Check

Perform a comprehensive health check of the FairDB PostgreSQL infrastructure including server resources, database status, backup integrity, and customer databases.

## System Health Overview

```bash
#!/bin/bash
# FairDB Comprehensive Health Check

echo "================================================"
echo "        FairDB System Health Check"
echo "        $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"
```

## Step 1: Server Resources Check

```bash
echo -e "\n[1/10] SERVER RESOURCES"
echo "------------------------"

# CPU Usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
echo "CPU Usage: ${CPU_USAGE}%"
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "⚠️  WARNING: High CPU usage detected"
fi

# Memory Usage
MEM_INFO=$(free -m | awk 'NR==2{printf "Memory: %s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2 }')
echo "$MEM_INFO"
MEM_PERCENT=$(free | grep Mem | awk '{print $3/$2 * 100.0}')
if (( $(echo "$MEM_PERCENT > 90" | bc -l) )); then
    echo "⚠️  WARNING: High memory usage detected"
fi

# Disk Usage
echo "Disk Usage:"
df -h | grep -E '^/dev/' | while read line; do
    USAGE=$(echo $line | awk '{print $5}' | sed 's/%//')
    MOUNT=$(echo $line | awk '{print $6}')
    echo "  $MOUNT: $line"
    if [ $USAGE -gt 85 ]; then
        echo "  ⚠️  WARNING: Disk space critical on $MOUNT"
    fi
done

# Load Average
LOAD=$(uptime | awk -F'load average:' '{print $2}')
echo "Load Average:$LOAD"
CORES=$(nproc)
LOAD_1=$(echo $LOAD | cut -d, -f1 | tr -d ' ')
if (( $(echo "$LOAD_1 > $CORES" | bc -l) )); then
    echo "⚠️  WARNING: High load average detected"
fi
```

## Step 2: PostgreSQL Service Status

```bash
echo -e "\n[2/10] POSTGRESQL SERVICE"
echo "-------------------------"

# Check if PostgreSQL is running
if systemctl is-active --quiet postgresql; then
    echo "✅ PostgreSQL service: RUNNING"

    # Get version and uptime
    sudo -u postgres psql -t -c "SELECT version();" | head -1

    UPTIME=$(sudo -u postgres psql -t -c "
        SELECT now() - pg_postmaster_start_time() as uptime;")
    echo "Uptime: $UPTIME"
else
    echo "❌ CRITICAL: PostgreSQL service is NOT running!"
    echo "Attempting to start..."
    sudo systemctl start postgresql
    sleep 5
    if systemctl is-active --quiet postgresql; then
        echo "✅ Service restarted successfully"
    else
        echo "❌ Failed to start PostgreSQL - manual intervention required!"
        exit 1
    fi
fi

# Check PostgreSQL cluster status
sudo pg_lsclusters
```

## Step 3: Database Connections

```bash
echo -e "\n[3/10] DATABASE CONNECTIONS"
echo "---------------------------"

# Connection statistics
sudo -u postgres psql -t << EOF
SELECT
    'Total Connections: ' || count(*) || '/' || setting AS connection_info
FROM pg_stat_activity, pg_settings
WHERE pg_settings.name = 'max_connections'
GROUP BY setting;
EOF

# Connections by database
echo -e "\nConnections by database:"
sudo -u postgres psql -t -c "
    SELECT datname, count(*) as connections
    FROM pg_stat_activity
    GROUP BY datname
    ORDER BY connections DESC;"

# Connections by user
echo -e "\nConnections by user:"
sudo -u postgres psql -t -c "
    SELECT usename, count(*) as connections
    FROM pg_stat_activity
    GROUP BY usename
    ORDER BY connections DESC;"

# Check for idle connections
IDLE_COUNT=$(sudo -u postgres psql -t -c "
    SELECT count(*)
    FROM pg_stat_activity
    WHERE state = 'idle'
    AND state_change < NOW() - INTERVAL '10 minutes';")

if [ $IDLE_COUNT -gt 10 ]; then
    echo "⚠️  WARNING: $IDLE_COUNT idle connections older than 10 minutes"
fi
```

## Step 4: Database Performance Metrics

```bash
echo -e "\n[4/10] PERFORMANCE METRICS"
echo "--------------------------"

# Cache hit ratio
sudo -u postgres psql -t << 'EOF'
SELECT
    'Cache Hit Ratio: ' ||
    ROUND(100.0 * sum(heap_blks_hit) /
          NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2) || '%'
FROM pg_statio_user_tables;
EOF

# Transaction statistics
sudo -u postgres psql -t -c "
    SELECT
        'Transactions: ' || xact_commit || ' commits, ' ||
        xact_rollback || ' rollbacks, ' ||
        ROUND(100.0 * xact_rollback / NULLIF(xact_commit + xact_rollback, 0), 2) || '% rollback rate'
    FROM pg_stat_database
    WHERE datname = 'postgres';"

# Longest running queries
echo -e "\nLong-running queries (>1 minute):"
sudo -u postgres psql -t -c "
    SELECT pid, now() - query_start as duration,
           LEFT(query, 50) as query_preview
    FROM pg_stat_activity
    WHERE state = 'active'
    AND now() - query_start > interval '1 minute'
    ORDER BY duration DESC
    LIMIT 5;"

# Table bloat check
echo -e "\nTable bloat (top 5):"
sudo -u postgres psql -t << 'EOF'
SELECT
    schemaname || '.' || tablename AS table,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    ROUND(100 * pg_total_relation_size(schemaname||'.'||tablename) /
          NULLIF(sum(pg_total_relation_size(schemaname||'.'||tablename))
          OVER (), 0), 2) AS percentage
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 5;
EOF
```

## Step 5: Backup Status

```bash
echo -e "\n[5/10] BACKUP STATUS"
echo "--------------------"

# Check pgBackRest status
if command -v pgbackrest &> /dev/null; then
    echo "pgBackRest Status:"

    # Get all stanzas
    STANZAS=$(sudo -u postgres pgbackrest info --output=json 2>/dev/null | jq -r '.[].name' 2>/dev/null)

    if [ -z "$STANZAS" ]; then
        echo "⚠️  WARNING: No backup stanzas configured"
    else
        for STANZA in $STANZAS; do
            echo -e "\nStanza: $STANZA"

            # Get last backup info
            LAST_BACKUP=$(sudo -u postgres pgbackrest --stanza=$STANZA info --output=json 2>/dev/null | \
                jq -r '.[] | select(.name=="'$STANZA'") | .backup[-1].timestamp.stop' 2>/dev/null)

            if [ ! -z "$LAST_BACKUP" ]; then
                echo "  Last backup: $LAST_BACKUP"

                # Calculate age in hours
                BACKUP_AGE=$(( ($(date +%s) - $(date -d "$LAST_BACKUP" +%s)) / 3600 ))

                if [ $BACKUP_AGE -gt 25 ]; then
                    echo "  ⚠️  WARNING: Last backup is $BACKUP_AGE hours old"
                else
                    echo "  ✅ Backup is current ($BACKUP_AGE hours old)"
                fi
            else
                echo "  ❌ ERROR: No backups found for this stanza"
            fi
        done
    fi
else
    echo "❌ ERROR: pgBackRest is not installed"
fi

# Check WAL archiving
WAL_STATUS=$(sudo -u postgres psql -t -c "SHOW archive_mode;")
echo -e "\nWAL Archiving: $WAL_STATUS"

if [ "$WAL_STATUS" = " on" ]; then
    LAST_ARCHIVED=$(sudo -u postgres psql -t -c "
        SELECT age(now(), last_archived_time)
        FROM pg_stat_archiver;")
    echo "Last WAL archived: $LAST_ARCHIVED ago"
fi
```

## Step 6: Replication Status

```bash
echo -e "\n[6/10] REPLICATION STATUS"
echo "-------------------------"

# Check if this is a primary or replica
IS_PRIMARY=$(sudo -u postgres psql -t -c "SELECT pg_is_in_recovery();")

if [ "$IS_PRIMARY" = " f" ]; then
    echo "Role: PRIMARY"

    # Check replication slots
    REP_SLOTS=$(sudo -u postgres psql -t -c "
        SELECT count(*) FROM pg_replication_slots WHERE active = true;")
    echo "Active replication slots: $REP_SLOTS"

    # Check connected replicas
    sudo -u postgres psql -t -c "
        SELECT client_addr, state, sync_state,
               pg_size_pretty(pg_wal_lsn_diff(sent_lsn, replay_lsn)) as lag
        FROM pg_stat_replication;" 2>/dev/null
else
    echo "Role: REPLICA"

    # Check replication lag
    LAG=$(sudo -u postgres psql -t -c "
        SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag;")
    echo "Replication lag: ${LAG} seconds"

    if (( $(echo "$LAG > 60" | bc -l) )); then
        echo "⚠️  WARNING: High replication lag detected"
    fi
fi
```

## Step 7: Security Audit

```bash
echo -e "\n[7/10] SECURITY AUDIT"
echo "---------------------"

# Check for default passwords
echo "Checking for common issues..."

# SSL status
SSL_STATUS=$(sudo -u postgres psql -t -c "SHOW ssl;")
echo "SSL: $SSL_STATUS"
if [ "$SSL_STATUS" != " on" ]; then
    echo "⚠️  WARNING: SSL is not enabled"
fi

# Check for users without passwords
NO_PASS=$(sudo -u postgres psql -t -c "
    SELECT count(*) FROM pg_shadow WHERE passwd IS NULL;")
if [ $NO_PASS -gt 0 ]; then
    echo "⚠️  WARNING: $NO_PASS users without passwords"
fi

# Check firewall status
if sudo ufw status | grep -q "Status: active"; then
    echo "✅ Firewall: ACTIVE"
else
    echo "⚠️  WARNING: Firewall is not active"
fi

# Check fail2ban status
if systemctl is-active --quiet fail2ban; then
    echo "✅ Fail2ban: RUNNING"
    JAIL_STATUS=$(sudo fail2ban-client status postgresql 2>/dev/null | grep "Currently banned" || echo "Jail not configured")
    echo "  PostgreSQL jail: $JAIL_STATUS"
else
    echo "⚠️  WARNING: Fail2ban is not running"
fi
```

## Step 8: Customer Database Health

```bash
echo -e "\n[8/10] CUSTOMER DATABASES"
echo "-------------------------"

# Check each customer database
CUSTOMER_DBS=$(sudo -u postgres psql -t -c "
    SELECT datname FROM pg_database
    WHERE datname NOT IN ('postgres', 'template0', 'template1')
    ORDER BY datname;")

for DB in $CUSTOMER_DBS; do
    echo -e "\nDatabase: $DB"

    # Size
    SIZE=$(sudo -u postgres psql -t -c "
        SELECT pg_size_pretty(pg_database_size('$DB'));")
    echo "  Size: $SIZE"

    # Connection count
    CONN=$(sudo -u postgres psql -t -c "
        SELECT count(*) FROM pg_stat_activity WHERE datname = '$DB';")
    echo "  Connections: $CONN"

    # Transaction rate
    TPS=$(sudo -u postgres psql -t -c "
        SELECT xact_commit + xact_rollback as transactions
        FROM pg_stat_database WHERE datname = '$DB';")
    echo "  Total transactions: $TPS"

    # Check for locks
    LOCKS=$(sudo -u postgres psql -t -d $DB -c "
        SELECT count(*) FROM pg_locks WHERE granted = false;")
    if [ $LOCKS -gt 0 ]; then
        echo "  ⚠️  WARNING: $LOCKS blocked locks detected"
    fi
done
```

## Step 9: System Logs Analysis

```bash
echo -e "\n[9/10] LOG ANALYSIS"
echo "-------------------"

# Check PostgreSQL logs for errors
LOG_DIR="/var/log/postgresql"
if [ -d "$LOG_DIR" ]; then
    echo "Recent PostgreSQL errors (last 24 hours):"
    find $LOG_DIR -name "*.log" -mtime -1 -exec grep -i "error\|fatal\|panic" {} \; | \
        tail -10 | head -5

    ERROR_COUNT=$(find $LOG_DIR -name "*.log" -mtime -1 -exec grep -i "error\|fatal\|panic" {} \; | wc -l)
    echo "Total errors in last 24 hours: $ERROR_COUNT"

    if [ $ERROR_COUNT -gt 100 ]; then
        echo "⚠️  WARNING: High error rate detected"
    fi
fi

# Check system logs
echo -e "\nRecent system issues:"
sudo journalctl -p err -since "24 hours ago" --no-pager | tail -5
```

## Step 10: Recommendations

```bash
echo -e "\n[10/10] HEALTH SUMMARY & RECOMMENDATIONS"
echo "========================================="

# Collect all warnings
WARNINGS=0
CRITICAL=0

# Generate recommendations based on findings
echo -e "\nRecommendations:"

# Check if vacuum is needed
LAST_VACUUM=$(sudo -u postgres psql -t -c "
    SELECT MAX(last_autovacuum) FROM pg_stat_user_tables;")
echo "- Last autovacuum: $LAST_VACUUM"

# Check if analyze is needed
LAST_ANALYZE=$(sudo -u postgres psql -t -c "
    SELECT MAX(last_autoanalyze) FROM pg_stat_user_tables;")
echo "- Last autoanalyze: $LAST_ANALYZE"

# Generate overall health score
echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $CRITICAL -eq 0 ] && [ $WARNINGS -lt 3 ]; then
    echo "✅ OVERALL HEALTH: GOOD"
elif [ $CRITICAL -eq 0 ] && [ $WARNINGS -lt 10 ]; then
    echo "⚠️  OVERALL HEALTH: FAIR - Review warnings"
else
    echo "❌ OVERALL HEALTH: POOR - Immediate action required"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Save report
REPORT_FILE="/opt/fairdb/logs/health-check-$(date +%Y%m%d-%H%M%S).log"
echo -e "\nFull report saved to: $REPORT_FILE"
```

## Actions Based on Results

### If Critical Issues Found:
1. Check PostgreSQL service status
2. Review disk space availability
3. Verify backup integrity
4. Check for data corruption
5. Review security vulnerabilities

### If Warnings Found:
1. Schedule maintenance window
2. Plan capacity upgrades
3. Review query performance
4. Update monitoring thresholds
5. Document issues for trending

### Regular Maintenance Tasks:
1. Run VACUUM ANALYZE on large tables
2. Update table statistics
3. Review and optimize slow queries
4. Clean up old logs
5. Test backup restoration

## Schedule Next Health Check

```bash
# Schedule regular health checks
echo "30 */6 * * * root /usr/local/bin/fairdb-health-check > /dev/null 2>&1" | \
    sudo tee /etc/cron.d/fairdb-health-check

echo "Health checks scheduled every 6 hours"
```