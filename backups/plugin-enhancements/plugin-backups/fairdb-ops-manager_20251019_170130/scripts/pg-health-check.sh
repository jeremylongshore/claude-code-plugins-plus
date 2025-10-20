#!/bin/bash
# PostgreSQL Health Check Script
# Returns exit code 0 if healthy, 1 if unhealthy
# Deploy to: /opt/fairdb/scripts/pg-health-check.sh

# Configuration
PG_USER="postgres"
PG_DB="postgres"
LOG_FILE="/opt/fairdb/logs/health-check.log"
ALERT_EMAIL="${ALERT_EMAIL:-ops@fairdb.io}"

# Create log directory if doesn't exist
mkdir -p /opt/fairdb/logs

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to send alert
send_alert() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
}

# Check 1: Is PostgreSQL running?
if ! systemctl is-active --quiet postgresql; then
    log "ERROR: PostgreSQL service is not running"
    send_alert "FairDB ALERT: PostgreSQL Down" "PostgreSQL service is not running on $(hostname)"
    exit 1
fi

# Check 2: Can we connect?
if ! sudo -u postgres psql -c "SELECT 1;" > /dev/null 2>&1; then
    log "ERROR: Cannot connect to PostgreSQL"
    send_alert "FairDB ALERT: PostgreSQL Connection Failed" "Cannot connect to PostgreSQL on $(hostname)"
    exit 1
fi

# Check 3: Check database connections
CONN_COUNT=$(sudo -u postgres psql -t -c "SELECT count(*) FROM pg_stat_activity;" | tr -d ' ')
MAX_CONN=$(sudo -u postgres psql -t -c "SHOW max_connections;" | tr -d ' ')

if [ "$CONN_COUNT" -ge "$((MAX_CONN * 90 / 100))" ]; then
    log "WARNING: Connection usage at ${CONN_COUNT}/${MAX_CONN} (90%+)"
    send_alert "FairDB WARNING: High Connection Usage" "Connections: ${CONN_COUNT}/${MAX_CONN} on $(hostname)"
fi

# Check 4: Check disk space
DISK_USAGE=$(df -h /var/lib/postgresql | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    log "WARNING: Disk usage at ${DISK_USAGE}%"
    send_alert "FairDB WARNING: High Disk Usage" "Disk at ${DISK_USAGE}% on $(hostname)"
fi

# Check 5: Check for long-running queries (>5 minutes)
LONG_QUERIES=$(sudo -u postgres psql -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '5 minutes';" | tr -d ' ')
if [ "$LONG_QUERIES" -gt 0 ]; then
    log "WARNING: ${LONG_QUERIES} queries running >5 minutes"
    send_alert "FairDB WARNING: Long Running Queries" "${LONG_QUERIES} queries running >5min on $(hostname)"
fi

# Check 6: Check for failed backups
if [ -f /var/log/pgbackrest/main-backup.log ]; then
    if grep -q "ERROR" /var/log/pgbackrest/main-backup.log | tail -20; then
        log "WARNING: Recent backup errors detected"
        send_alert "FairDB WARNING: Backup Errors" "Check pgBackRest logs on $(hostname)"
    fi
fi

# All checks passed
log "INFO: Health check passed - Connections: ${CONN_COUNT}/${MAX_CONN}, Disk: ${DISK_USAGE}%"
exit 0
