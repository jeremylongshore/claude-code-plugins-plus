#!/bin/bash
# FairDB Backup Status Dashboard
# Quick visual check of backup health
# Deploy to: /opt/fairdb/scripts/backup-status.sh

echo "======================================"
echo "  FairDB Backup Status"
echo "  $(date +'%Y-%m-%d %H:%M:%S')"
echo "======================================"
echo ""

# Backup repository status
echo "Repository Status:"
echo "-----------------------------------"
if sudo -u postgres pgbackrest --stanza=main info 2>/dev/null; then
    echo ""
    echo "✅ Backup repository accessible"
else
    echo ""
    echo "❌ ERROR: Cannot access backup repository"
    echo "   Check Wasabi connectivity and credentials"
fi

echo ""
echo "======================================"

# Recent backups from logs
echo "Recent Backup Activity:"
echo "-----------------------------------"

if [ -f /var/log/pgbackrest/main-backup.log ]; then
    echo ""
    echo "Last Full Backup:"
    grep "full backup size" /var/log/pgbackrest/main-backup.log | tail -1 || echo "  No full backups found"
    echo ""
    echo "Last Differential Backup:"
    grep "diff backup size" /var/log/pgbackrest/main-backup.log | tail -1 || echo "  No differential backups found"
    echo ""
    echo "Recent Errors:"
    if grep -i "error" /var/log/pgbackrest/main-backup.log | tail -5 | grep -q "error"; then
        grep -i "error" /var/log/pgbackrest/main-backup.log | tail -5
        echo "  ⚠️  Errors detected - investigate!"
    else
        echo "  ✅ No recent errors"
    fi
else
    echo "  ⚠️  No backup logs found"
fi

echo ""
echo "======================================"

# Storage usage
echo "Storage Usage:"
echo "-----------------------------------"
echo ""
echo "PostgreSQL Data Directory:"
du -sh /var/lib/postgresql/16/main 2>/dev/null || echo "  Cannot access data directory"
echo ""
echo "Local Disk Usage:"
df -h /var/lib/postgresql | grep -v Filesystem

echo ""
echo "======================================"

# WAL archive status
echo "WAL Archive Status:"
echo "-----------------------------------"
sudo -u postgres psql -t -c "
SELECT
    'Archived: ' || archived_count || ' | Failed: ' || failed_count || ' | Last: ' || last_archived_time
FROM pg_stat_archiver;
" 2>/dev/null || echo "  Cannot check WAL status"

echo ""
echo "======================================"

# Recent backup verification
if [ -f /opt/fairdb/logs/backup-verification.log ]; then
    echo "Last Backup Verification:"
    echo "-----------------------------------"
    tail -5 /opt/fairdb/logs/backup-verification.log | grep -E "Verification Complete|SUCCESS|FAILED" || echo "  No recent verification"
else
    echo "Backup Verification: Not configured"
fi

echo ""
echo "======================================"

# Backup age check
echo "Backup Age Analysis:"
echo "-----------------------------------"
if command -v jq &> /dev/null; then
    LAST_BACKUP_TIME=$(sudo -u postgres pgbackrest --stanza=main info --output=json 2>/dev/null | jq -r '.[0].backup[-1].timestamp.stop' 2>/dev/null)
    if [ -n "$LAST_BACKUP_TIME" ] && [ "$LAST_BACKUP_TIME" != "null" ]; then
        BACKUP_AGE_HOURS=$(( ($(date +%s) - $(date -d "$LAST_BACKUP_TIME" +%s 2>/dev/null || echo 0)) / 3600 ))
        echo "Last backup: $BACKUP_AGE_HOURS hours ago"
        if [ "$BACKUP_AGE_HOURS" -gt 48 ]; then
            echo "⚠️  WARNING: Backup is over 48 hours old!"
        elif [ "$BACKUP_AGE_HOURS" -gt 24 ]; then
            echo "⚠️  Backup is over 24 hours old"
        else
            echo "✅ Backup is recent"
        fi
    else
        echo "Cannot determine backup age (jq parsing failed)"
    fi
else
    echo "jq not installed - cannot calculate backup age"
    echo "Install with: sudo apt install jq"
fi

echo ""
echo "======================================"
echo ""

# Exit with status based on critical checks
if sudo -u postgres pgbackrest --stanza=main info &>/dev/null; then
    exit 0
else
    exit 1
fi
