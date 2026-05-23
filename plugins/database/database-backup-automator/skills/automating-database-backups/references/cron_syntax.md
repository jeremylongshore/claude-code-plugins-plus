# Cron Syntax Quick Reference

## Cron Expression Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * * command to execute
```

## Special Characters

| Character | Meaning | Example |
|-----------|---------|---------|
| `*` | Any value | `* * * * *` = every minute |
| `,` | List of values | `0,30 * * * *` = :00 and :30 |
| `-` | Range of values | `0-5 * * * *` = :00 to :05 |
| `/` | Step values | `*/15 * * * *` = every 15 min |

## Common Backup Schedules

### Daily Backups

```bash
# Every day at 2:00 AM
0 2 * * * /opt/backup/backup.sh

# Every day at 2:30 AM
30 2 * * * /opt/backup/backup.sh

# Every day at midnight
0 0 * * * /opt/backup/backup.sh
```

### Multiple Times Per Day

```bash
# Every 6 hours
0 */6 * * * /opt/backup/backup.sh

# Every 4 hours
0 */4 * * * /opt/backup/backup.sh

# Every hour
0 * * * * /opt/backup/backup.sh

# Every 30 minutes
*/30 * * * * /opt/backup/backup.sh
```

### Weekly Backups

```bash
# Every Sunday at 2:00 AM
0 2 * * 0 /opt/backup/weekly-backup.sh

# Every Saturday at 3:00 AM
0 3 * * 6 /opt/backup/weekly-backup.sh

# Every Monday at 1:00 AM
0 1 * * 1 /opt/backup/weekly-backup.sh
```

### Monthly Backups

```bash
# First day of month at 2:00 AM
0 2 1 * * /opt/backup/monthly-backup.sh

# Last day of month (28th-31st, safer approach)
0 2 28-31 * * [ "$(date +\%d -d tomorrow)" == "01" ] && /opt/backup/monthly-backup.sh

# 15th of each month
0 2 15 * * /opt/backup/mid-month-backup.sh
```

### Quarterly/Yearly

```bash
# First day of each quarter
0 2 1 1,4,7,10 * /opt/backup/quarterly-backup.sh

# First day of year
0 2 1 1 * /opt/backup/yearly-backup.sh
```

## Special Strings (If Supported)

| String | Equivalent | Description |
|--------|------------|-------------|
| `@yearly` | `0 0 1 1 *` | January 1st midnight |
| `@monthly` | `0 0 1 * *` | 1st of month midnight |
| `@weekly` | `0 0 * * 0` | Sunday midnight |
| `@daily` | `0 0 * * *` | Every day midnight |
| `@hourly` | `0 * * * *` | Every hour |
| `@reboot` | N/A | At system startup |

## Backup Strategy Schedule

```bash
# Hourly incremental backups (business hours)
0 9-17 * * 1-5 /opt/backup/incremental.sh

# Daily full backup at 2 AM
0 2 * * * /opt/backup/daily-full.sh

# Weekly full backup on Sunday at 1 AM
0 1 * * 0 /opt/backup/weekly-full.sh

# Monthly archive on 1st at midnight
0 0 1 * * /opt/backup/monthly-archive.sh

# Cleanup old backups at 4 AM daily
0 4 * * * /opt/backup/cleanup.sh
```

## Environment Setup

### Setting PATH and Environment

```bash
# At top of crontab
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=admin@example.com

# Database credentials (avoid plaintext)
PGPASSWORD=secret
MYSQL_PWD=secret

# Then your jobs
0 2 * * * /opt/backup/backup.sh
```

### Using Environment Files

```bash
# Crontab entry that sources env file
0 2 * * * . /etc/backup/env && /opt/backup/backup.sh

# Or wrap in script
0 2 * * * /opt/backup/run-backup.sh
```

`/opt/backup/run-backup.sh`:

```bash
#!/bin/bash
source /etc/backup/env
/opt/backup/backup.sh
```

## Logging Output

```bash
# Log stdout and stderr
0 2 * * * /opt/backup/backup.sh >> /var/log/backup.log 2>&1

# Log with timestamp
0 2 * * * /opt/backup/backup.sh 2>&1 | while read line; do echo "$(date): $line"; done >> /var/log/backup.log

# Separate error log
0 2 * * * /opt/backup/backup.sh >> /var/log/backup.log 2>> /var/log/backup-error.log

# Discard output (not recommended for backups)
0 2 * * * /opt/backup/backup.sh > /dev/null 2>&1
```

## Managing Crontab

```bash
# Edit current user's crontab
crontab -e

# List current user's crontab
crontab -l

# Edit specific user's crontab (as root)
crontab -e -u postgres

# Remove all cron jobs (dangerous!)
crontab -r

# Install from file
crontab /path/to/crontab-file
```

## System Crontab vs User Crontab

### User Crontab (`crontab -e`)

```bash
# Format: minute hour day month weekday command
0 2 * * * /home/user/backup.sh
```

### System Crontab (`/etc/crontab`)

```bash
# Format: minute hour day month weekday USER command
0 2 * * * root /opt/backup/backup.sh
0 3 * * * postgres /opt/backup/pg-backup.sh
```

### Cron Directories

```bash
/etc/cron.d/       # Custom cron files
/etc/cron.daily/   # Daily scripts
/etc/cron.hourly/  # Hourly scripts
/etc/cron.weekly/  # Weekly scripts
/etc/cron.monthly/ # Monthly scripts
```

## Preventing Overlap

### Using flock

```bash
# Prevent concurrent execution
0 * * * * flock -n /tmp/backup.lock /opt/backup/backup.sh
```

### Using PID File

```bash
#!/bin/bash
PIDFILE=/var/run/backup.pid

if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
    echo "Backup already running"
    exit 1
fi

echo $$ > "$PIDFILE"
trap "rm -f $PIDFILE" EXIT

# Backup logic here
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Job not running | Check cron service: `systemctl status cron` |
| Permission denied | Check script permissions: `chmod +x script.sh` |
| Environment issues | Define PATH in crontab or source env file |
| No output/email | Check MAILTO, add explicit logging |
| Wrong timezone | Set TZ in crontab or use UTC |

### Debug Tips

```bash
# Check if cron is running
systemctl status cron

# View cron logs
grep CRON /var/log/syslog
journalctl -u cron

# Test command manually first
/opt/backup/backup.sh

# Verify crontab syntax
crontab -l | crontab -
```

## Time Zone Considerations

```bash
# Set timezone in crontab
TZ=America/New_York
0 2 * * * /opt/backup/backup.sh

# Or use UTC (recommended for servers)
TZ=UTC
0 7 * * * /opt/backup/backup.sh  # 7 AM UTC = 2 AM EST
```
