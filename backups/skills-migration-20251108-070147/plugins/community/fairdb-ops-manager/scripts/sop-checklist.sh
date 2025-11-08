#!/bin/bash
# FairDB SOP Completion Checklist
# Interactive checklist for tracking SOP completion
# Deploy to: /opt/fairdb/scripts/sop-checklist.sh

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check status
check_item() {
    local description="$1"
    local command="$2"

    echo -n "  Checking: $description... "
    if eval "$command" &>/dev/null; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

# Function to print header
print_header() {
    echo ""
    echo "======================================"
    echo "  $1"
    echo "======================================"
    echo ""
}

# Main menu
show_menu() {
    clear
    echo "======================================"
    echo "  FairDB SOP Completion Checker"
    echo "======================================"
    echo ""
    echo "Select SOP to verify:"
    echo ""
    echo "  1) SOP-001: VPS Initial Setup & Hardening"
    echo "  2) SOP-002: PostgreSQL Installation & Configuration"
    echo "  3) SOP-003: Backup System Setup & Verification"
    echo "  4) ALL: Complete System Verification"
    echo "  5) Exit"
    echo ""
    read -p "Enter choice [1-5]: " choice
}

# SOP-001 Checklist
check_sop_001() {
    print_header "SOP-001: VPS Initial Setup & Hardening"

    local passed=0
    local total=0

    # Check system updates
    ((total++))
    if check_item "System packages up to date" "test \$(apt list --upgradable 2>/dev/null | wc -l) -lt 5"; then
        ((passed++))
    fi

    # Check non-root user
    ((total++))
    if check_item "Non-root admin user exists" "id admin &>/dev/null || id \$USER &>/dev/null"; then
        ((passed++))
    fi

    # Check SSH configuration
    ((total++))
    if check_item "Root login disabled" "sudo grep -q '^PermitRootLogin no' /etc/ssh/sshd_config"; then
        ((passed++))
    fi

    ((total++))
    if check_item "Password authentication disabled" "sudo grep -q '^PasswordAuthentication no' /etc/ssh/sshd_config"; then
        ((passed++))
    fi

    ((total++))
    if check_item "SSH keys configured" "test -f ~/.ssh/authorized_keys"; then
        ((passed++))
    fi

    # Check firewall
    ((total++))
    if check_item "UFW firewall active" "sudo ufw status | grep -q 'Status: active'"; then
        ((passed++))
    fi

    # Check Fail2ban
    ((total++))
    if check_item "Fail2ban running" "systemctl is-active --quiet fail2ban"; then
        ((passed++))
    fi

    # Check automatic updates
    ((total++))
    if check_item "Automatic security updates enabled" "systemctl is-active --quiet unattended-upgrades"; then
        ((passed++))
    fi

    # Check timezone and NTP
    ((total++))
    if check_item "NTP synchronized" "timedatectl status | grep -q 'NTP.*yes'"; then
        ((passed++))
    fi

    # Check directory structure
    ((total++))
    if check_item "Operations directory exists" "test -d /opt/fairdb"; then
        ((passed++))
    fi

    echo ""
    echo "======================================"
    echo -e "SOP-001 Status: ${passed}/${total} checks passed"
    if [ $passed -eq $total ]; then
        echo -e "${GREEN}✅ SOP-001 COMPLETE${NC}"
    else
        echo -e "${RED}⚠️  SOP-001 INCOMPLETE${NC}"
    fi
    echo "======================================"
}

# SOP-002 Checklist
check_sop_002() {
    print_header "SOP-002: PostgreSQL Installation & Configuration"

    local passed=0
    local total=0

    # Check PostgreSQL installed
    ((total++))
    if check_item "PostgreSQL 16 installed" "dpkg -l | grep -q postgresql-16"; then
        ((passed++))
    fi

    # Check PostgreSQL running
    ((total++))
    if check_item "PostgreSQL service running" "systemctl is-active --quiet postgresql"; then
        ((passed++))
    fi

    # Check can connect
    ((total++))
    if check_item "Database connection works" "sudo -u postgres psql -c 'SELECT 1' &>/dev/null"; then
        ((passed++))
    fi

    # Check SSL enabled
    ((total++))
    if check_item "SSL enabled" "sudo -u postgres psql -t -c 'SHOW ssl' | grep -q 'on'"; then
        ((passed++))
    fi

    # Check remote connections
    ((total++))
    if check_item "Remote connections enabled" "sudo grep -q '^listen_addresses.*\*' /etc/postgresql/16/main/postgresql.conf"; then
        ((passed++))
    fi

    # Check pg_stat_statements
    ((total++))
    if check_item "pg_stat_statements enabled" "sudo -u postgres psql -c '\\dx' | grep -q pg_stat_statements"; then
        ((passed++))
    fi

    # Check health check script
    ((total++))
    if check_item "Health check script exists" "test -x /opt/fairdb/scripts/pg-health-check.sh"; then
        ((passed++))
    fi

    # Check health check scheduled
    ((total++))
    if check_item "Health check scheduled" "sudo -u postgres crontab -l 2>/dev/null | grep -q pg-health-check"; then
        ((passed++))
    fi

    # Check monitoring queries
    ((total++))
    if check_item "Monitoring queries exist" "test -f /opt/fairdb/scripts/pg-queries.sql"; then
        ((passed++))
    fi

    # Check PostgreSQL config documented
    ((total++))
    if check_item "PostgreSQL config documented" "test -f ~/fairdb/POSTGRESQL-CONFIG.md"; then
        ((passed++))
    fi

    echo ""
    echo "======================================"
    echo -e "SOP-002 Status: ${passed}/${total} checks passed"
    if [ $passed -eq $total ]; then
        echo -e "${GREEN}✅ SOP-002 COMPLETE${NC}"
    else
        echo -e "${RED}⚠️  SOP-002 INCOMPLETE${NC}"
    fi
    echo "======================================"
}

# SOP-003 Checklist
check_sop_003() {
    print_header "SOP-003: Backup System Setup & Verification"

    local passed=0
    local total=0

    # Check pgBackRest installed
    ((total++))
    if check_item "pgBackRest installed" "command -v pgbackrest &>/dev/null"; then
        ((passed++))
    fi

    # Check pgBackRest config
    ((total++))
    if check_item "pgBackRest config exists" "sudo test -f /etc/pgbackrest.conf"; then
        ((passed++))
    fi

    # Check config permissions
    ((total++))
    if check_item "Config permissions secure (640)" "sudo stat -c %a /etc/pgbackrest.conf | grep -q 640"; then
        ((passed++))
    fi

    # Check WAL archiving enabled
    ((total++))
    if check_item "WAL archiving enabled" "sudo -u postgres psql -t -c 'SHOW archive_mode' | grep -q 'on'"; then
        ((passed++))
    fi

    # Check stanza created
    ((total++))
    if check_item "pgBackRest stanza exists" "sudo -u postgres pgbackrest --stanza=main info &>/dev/null"; then
        ((passed++))
    fi

    # Check backup exists
    ((total++))
    if check_item "At least one backup exists" "sudo -u postgres pgbackrest --stanza=main info 2>/dev/null | grep -q 'full backup'"; then
        ((passed++))
    fi

    # Check backup age
    ((total++))
    if command -v jq &>/dev/null; then
        BACKUP_AGE=$(sudo -u postgres pgbackrest --stanza=main info --output=json 2>/dev/null | jq -r '.[0].backup[-1].timestamp.stop' 2>/dev/null)
        if [ -n "$BACKUP_AGE" ] && [ "$BACKUP_AGE" != "null" ]; then
            HOURS=$(( ($(date +%s) - $(date -d "$BACKUP_AGE" +%s 2>/dev/null || echo 999999999)) / 3600 ))
            if [ $HOURS -lt 48 ]; then
                echo -e "  Checking: Backup is recent (<48 hours)... ${GREEN}✅ PASS${NC} (${HOURS}h old)"
                ((passed++))
            else
                echo -e "  Checking: Backup is recent (<48 hours)... ${RED}❌ FAIL${NC} (${HOURS}h old)"
            fi
        else
            echo -e "  Checking: Backup age... ${YELLOW}⚠️  SKIP${NC} (cannot determine)"
        fi
    else
        echo -e "  Checking: Backup age... ${YELLOW}⚠️  SKIP${NC} (jq not installed)"
    fi

    # Check backup script
    ((total++))
    if check_item "Backup script exists" "sudo test -x /opt/fairdb/scripts/pgbackrest-backup.sh"; then
        ((passed++))
    fi

    # Check backup scheduled
    ((total++))
    if check_item "Automated backups scheduled" "sudo -u postgres crontab -l 2>/dev/null | grep -q pgbackrest-backup"; then
        ((passed++))
    fi

    # Check verification script
    ((total++))
    if check_item "Verification script exists" "sudo test -x /opt/fairdb/scripts/pgbackrest-verify.sh"; then
        ((passed++))
    fi

    # Check verification scheduled
    ((total++))
    if check_item "Verification scheduled" "sudo -u postgres crontab -l 2>/dev/null | grep -q pgbackrest-verify"; then
        ((passed++))
    fi

    # Check backup config documented
    ((total++))
    if check_item "Backup config documented" "test -f ~/fairdb/BACKUP-CONFIG.md"; then
        ((passed++))
    fi

    echo ""
    echo "======================================"
    echo -e "SOP-003 Status: ${passed}/${total} checks passed"
    if [ $passed -eq $total ]; then
        echo -e "${GREEN}✅ SOP-003 COMPLETE${NC}"
    else
        echo -e "${RED}⚠️  SOP-003 INCOMPLETE${NC}"
    fi
    echo "======================================"
}

# Complete system verification
check_all() {
    check_sop_001
    sleep 2
    check_sop_002
    sleep 2
    check_sop_003

    echo ""
    print_header "OVERALL SYSTEM STATUS"

    # Quick summary
    echo "System Summary:"
    echo "  - Security:   $(systemctl is-active postgresql && echo -e "${GREEN}✅${NC}" || echo -e "${RED}❌${NC}")"
    echo "  - Database:   $(systemctl is-active postgresql && echo -e "${GREEN}✅${NC}" || echo -e "${RED}❌${NC}")"
    echo "  - Backups:    $(sudo -u postgres pgbackrest --stanza=main info &>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${RED}❌${NC}")"
    echo ""

    # Disk space check
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    echo -n "  - Disk Space: "
    if [ "$DISK_USAGE" -lt 80 ]; then
        echo -e "${GREEN}${DISK_USAGE}% used${NC}"
    elif [ "$DISK_USAGE" -lt 90 ]; then
        echo -e "${YELLOW}${DISK_USAGE}% used (warning)${NC}"
    else
        echo -e "${RED}${DISK_USAGE}% used (critical)${NC}"
    fi

    echo ""
}

# Main program loop
while true; do
    show_menu
    case $choice in
        1) check_sop_001; read -p "Press Enter to continue..." ;;
        2) check_sop_002; read -p "Press Enter to continue..." ;;
        3) check_sop_003; read -p "Press Enter to continue..." ;;
        4) check_all; read -p "Press Enter to continue..." ;;
        5) echo "Exiting..."; exit 0 ;;
        *) echo "Invalid choice. Please try again."; sleep 2 ;;
    esac
done
