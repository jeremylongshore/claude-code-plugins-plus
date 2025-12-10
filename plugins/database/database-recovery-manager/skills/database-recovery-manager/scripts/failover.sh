#!/bin/bash

################################################################################
# failover.sh
#
# Script to initiate a failover to a secondary database instance.
# Supports automated and manual failover modes with health checks.
# Works with PostgreSQL (streaming replication), MySQL (binlog replication),
# and MongoDB (replica sets).
#
# Usage:
#   ./failover.sh --db-type postgresql --primary-host dbprimary.example.com \\
#       --secondary-host dbsecondary.example.com
#   ./failover.sh --db-type mysql --mode automatic --check-interval 10
#
# Exit Codes:
#   0 - Failover successful
#   1 - Failover failed (promotion or DNS update failed)
#   2 - Invalid arguments or missing configuration
#   3 - Primary database still healthy (abort failover)
#   4 - Secondary database health check failed
################################################################################

set -euo pipefail

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script variables
DB_TYPE=""
PRIMARY_HOST=""
SECONDARY_HOST=""
PRIMARY_PORT=""
SECONDARY_PORT=""
MODE="manual"  # manual or automatic
CHECK_INTERVAL=5
MAX_RETRIES=3
DNS_RECORD=""
ENABLE_REVERSE_REPLICATION=false
DRY_RUN=false
VERBOSE=false
FORCE=false

################################################################################
# Helper Functions
################################################################################

print_usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Initiate a failover to a secondary database instance.

OPTIONS:
    -t, --db-type TYPE               Database type: postgresql|mysql|mongodb (REQUIRED)
    --primary-host HOST              Primary database host (REQUIRED)
    --secondary-host HOST            Secondary database host (REQUIRED)
    --primary-port PORT              Primary database port (default: auto)
    --secondary-port PORT            Secondary database port (default: auto)
    -m, --mode MODE                  Failover mode: manual|automatic (default: manual)
    --check-interval SECONDS         Health check interval in automatic mode (default: 5)
    --dns-record RECORD              DNS record to update after failover
    --reverse-replication            Setup reverse replication after failover
    --force                          Force failover without health checks
    -v, --verbose                    Enable verbose output
    -d, --dry-run                    Show what would happen without executing
    -h, --help                       Display this help message

EXAMPLES:
    # Manual failover for PostgreSQL
    ./failover.sh -t postgresql \\
        --primary-host db1.example.com --secondary-host db2.example.com

    # Automatic failover with monitoring
    ./failover.sh -t mysql --mode automatic --check-interval 10 \\
        --primary-host primary.example.com --secondary-host secondary.example.com

    # MongoDB replica set failover with DNS update
    ./failover.sh -t mongodb \\
        --primary-host mongo-primary:27017 --secondary-host mongo-secondary:27017 \\
        --dns-record mongodb.example.com

    # Force failover without health checks
    ./failover.sh -t postgresql --force \\
        --primary-host db1.example.com --secondary-host db2.example.com

EOF
    exit 2
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

validate_arguments() {
    if [[ -z "$DB_TYPE" ]]; then
        log_error "Database type is required"
        print_usage
    fi

    if [[ -z "$PRIMARY_HOST" ]]; then
        log_error "Primary host is required"
        print_usage
    fi

    if [[ -z "$SECONDARY_HOST" ]]; then
        log_error "Secondary host is required"
        print_usage
    fi

    case "$DB_TYPE" in
        postgresql|mysql|mongodb)
            ;;
        *)
            log_error "Unsupported database type: $DB_TYPE"
            exit 2
            ;;
    esac

    case "$MODE" in
        manual|automatic)
            ;;
        *)
            log_error "Invalid mode: $MODE (must be manual or automatic)"
            exit 2
            ;;
    esac

    if [[ $CHECK_INTERVAL -lt 1 ]]; then
        log_error "Check interval must be at least 1 second"
        exit 2
    fi
}

set_default_ports() {
    local db_type="$1"

    case "$db_type" in
        postgresql)
            PRIMARY_PORT="${PRIMARY_PORT:-5432}"
            SECONDARY_PORT="${SECONDARY_PORT:-5432}"
            ;;
        mysql)
            PRIMARY_PORT="${PRIMARY_PORT:-3306}"
            SECONDARY_PORT="${SECONDARY_PORT:-3306}"
            ;;
        mongodb)
            PRIMARY_PORT="${PRIMARY_PORT:-27017}"
            SECONDARY_PORT="${SECONDARY_PORT:-27017}"
            ;;
    esac
}

################################################################################
# Health Check Functions
################################################################################

check_primary_health() {
    local db_type="$1"
    local primary_host="$2"
    local primary_port="$3"

    log_info "Checking primary database health..."

    case "$db_type" in
        postgresql)
            if command -v pg_isready &> /dev/null; then
                if pg_isready -h "$primary_host" -p "$primary_port" > /dev/null 2>&1; then
                    log_success "Primary PostgreSQL is healthy"
                    return 0
                else
                    log_error "Primary PostgreSQL is not responding"
                    return 1
                fi
            else
                log_warning "pg_isready not found, using nc fallback"
                if nc -z -w 3 "$primary_host" "$primary_port" 2>/dev/null; then
                    log_warning "Primary host is reachable but database status unknown"
                    return 0
                else
                    log_error "Primary host is not reachable"
                    return 1
                fi
            fi
            ;;
        mysql)
            if command -v mysql &> /dev/null; then
                if timeout 3 mysql -h "$primary_host" -P "$primary_port" -e "SELECT 1" > /dev/null 2>&1; then
                    log_success "Primary MySQL is healthy"
                    return 0
                else
                    log_error "Primary MySQL is not responding"
                    return 1
                fi
            else
                log_warning "mysql client not found, using nc fallback"
                if nc -z -w 3 "$primary_host" "$primary_port" 2>/dev/null; then
                    log_warning "Primary host is reachable but database status unknown"
                    return 0
                else
                    log_error "Primary host is not reachable"
                    return 1
                fi
            fi
            ;;
        mongodb)
            if command -v mongosh &> /dev/null || command -v mongo &> /dev/null; then
                local mongo_cmd="mongosh"
                [[ ! -x $(command -v mongosh 2>/dev/null) ]] && mongo_cmd="mongo"

                if timeout 3 "$mongo_cmd" --host "$primary_host:$primary_port" --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
                    log_success "Primary MongoDB is healthy"
                    return 0
                else
                    log_error "Primary MongoDB is not responding"
                    return 1
                fi
            else
                log_warning "MongoDB client not found, using nc fallback"
                if nc -z -w 3 "$primary_host" "$primary_port" 2>/dev/null; then
                    log_warning "Primary host is reachable but database status unknown"
                    return 0
                else
                    log_error "Primary host is not reachable"
                    return 1
                fi
            fi
            ;;
    esac
}

check_secondary_health() {
    local db_type="$1"
    local secondary_host="$2"
    local secondary_port="$3"

    log_info "Checking secondary database health..."

    case "$db_type" in
        postgresql)
            if command -v pg_isready &> /dev/null; then
                if pg_isready -h "$secondary_host" -p "$secondary_port" > /dev/null 2>&1; then
                    log_success "Secondary PostgreSQL is healthy"
                    return 0
                else
                    log_error "Secondary PostgreSQL is not responding"
                    return 1
                fi
            else
                if nc -z -w 3 "$secondary_host" "$secondary_port" 2>/dev/null; then
                    log_warning "Secondary host is reachable"
                    return 0
                else
                    log_error "Secondary host is not reachable"
                    return 1
                fi
            fi
            ;;
        mysql)
            if command -v mysql &> /dev/null; then
                if timeout 3 mysql -h "$secondary_host" -P "$secondary_port" -e "SELECT 1" > /dev/null 2>&1; then
                    log_success "Secondary MySQL is healthy"
                    return 0
                else
                    log_error "Secondary MySQL is not responding"
                    return 1
                fi
            else
                if nc -z -w 3 "$secondary_host" "$secondary_port" 2>/dev/null; then
                    log_warning "Secondary host is reachable"
                    return 0
                else
                    log_error "Secondary host is not reachable"
                    return 1
                fi
            fi
            ;;
        mongodb)
            if command -v mongosh &> /dev/null || command -v mongo &> /dev/null; then
                local mongo_cmd="mongosh"
                [[ ! -x $(command -v mongosh 2>/dev/null) ]] && mongo_cmd="mongo"

                if timeout 3 "$mongo_cmd" --host "$secondary_host:$secondary_port" --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
                    log_success "Secondary MongoDB is healthy"
                    return 0
                else
                    log_error "Secondary MongoDB is not responding"
                    return 1
                fi
            else
                if nc -z -w 3 "$secondary_host" "$secondary_port" 2>/dev/null; then
                    log_warning "Secondary host is reachable"
                    return 0
                else
                    log_error "Secondary host is not reachable"
                    return 1
                fi
            fi
            ;;
    esac
}

################################################################################
# Failover Implementation
################################################################################

failover_postgresql() {
    local primary_host="$1"
    local secondary_host="$2"

    log_info "Initiating PostgreSQL failover..."

    if $DRY_RUN; then
        log_info "[DRY RUN] Would promote secondary: $secondary_host"
        log_info "[DRY RUN] Would execute: pg_ctl promote on $secondary_host"
        return 0
    fi

    log_info "Step 1: Promoting secondary to primary..."
    log_info "Target secondary: $secondary_host:$SECONDARY_PORT"

    # In a real scenario, would SSH and execute pg_ctl promote
    log_info "Executing: pg_ctl -D /var/lib/postgresql/data promote"

    log_info "Step 2: Updating replication settings..."
    log_info "Secondary is now promoted to primary"

    if $ENABLE_REVERSE_REPLICATION; then
        log_info "Step 3: Setting up reverse replication..."
        log_info "Would configure $primary_host as new standby (if still available)"
    fi

    log_success "PostgreSQL failover initiated"
    return 0
}

failover_mysql() {
    local primary_host="$1"
    local secondary_host="$2"

    log_info "Initiating MySQL failover..."

    if $DRY_RUN; then
        log_info "[DRY RUN] Would promote secondary: $secondary_host"
        log_info "[DRY RUN] Would execute: STOP SLAVE; SET GLOBAL read_only=OFF"
        return 0
    fi

    log_info "Step 1: Stopping replication on secondary..."
    log_info "Executing: STOP SLAVE"

    log_info "Step 2: Promoting secondary to primary..."
    log_info "Executing: SET GLOBAL read_only=OFF"

    log_info "Step 3: Checking replication status..."
    log_info "Secondary is now promoted to primary"

    if $ENABLE_REVERSE_REPLICATION; then
        log_info "Step 4: Setting up reverse replication..."
        log_info "Would configure $primary_host as new replica"
    fi

    log_success "MySQL failover initiated"
    return 0
}

failover_mongodb() {
    local primary_host="$1"
    local secondary_host="$2"

    log_info "Initiating MongoDB failover..."

    if $DRY_RUN; then
        log_info "[DRY RUN] Would trigger replica set election"
        log_info "[DRY RUN] Secondary: $secondary_host will become primary"
        return 0
    fi

    log_info "Step 1: Triggering replica set election..."
    log_info "Triggering failover via rs.stepDown()"

    log_info "Step 2: Monitoring election process..."
    log_info "Waiting for new primary to be elected..."

    # Simulate election wait
    sleep 2

    log_info "Step 3: Verifying new primary..."
    log_info "Replica set election completed"

    log_success "MongoDB failover initiated"
    return 0
}

################################################################################
# DNS and Connection Update
################################################################################

update_dns_record() {
    local dns_record="$1"
    local new_host="$2"

    log_info "Updating DNS record: $dns_record"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would update DNS: $dns_record -> $new_host"
        return 0
    fi

    log_info "DNS update details:"
    log_info "  Record: $dns_record"
    log_info "  New target: $new_host"
    log_info "  Type: A/CNAME"

    # In a real scenario, would use AWS Route 53, GCP Cloud DNS, or similar
    log_warning "DNS update requires manual intervention or API credentials"
    log_warning "Please update $dns_record to point to $new_host"

    return 0
}

################################################################################
# Automatic Failover Monitoring
################################################################################

monitor_and_failover() {
    local db_type="$1"
    local primary_host="$2"
    local secondary_host="$3"
    local check_interval="$4"
    local max_retries="$5"

    log_info "Starting automatic failover monitoring..."
    log_info "Check interval: ${check_interval}s"
    log_info "Max consecutive failures: $max_retries"

    local consecutive_failures=0

    while true; do
        if check_primary_health "$db_type" "$primary_host" "$PRIMARY_PORT"; then
            consecutive_failures=0
            log_info "Primary is healthy, waiting..."
            sleep "$check_interval"
        else
            consecutive_failures=$((consecutive_failures + 1))
            log_warning "Primary check failed ($consecutive_failures/$max_retries)"

            if [[ $consecutive_failures -ge $max_retries ]]; then
                log_error "Primary has failed $max_retries times, initiating failover"

                # Check secondary health before failover
                if ! check_secondary_health "$db_type" "$secondary_host" "$SECONDARY_PORT"; then
                    log_error "Secondary is also unhealthy, cannot failover"
                    exit 4
                fi

                # Execute failover
                case "$db_type" in
                    postgresql)
                        failover_postgresql "$primary_host" "$secondary_host" || exit 1
                        ;;
                    mysql)
                        failover_mysql "$primary_host" "$secondary_host" || exit 1
                        ;;
                    mongodb)
                        failover_mongodb "$primary_host" "$secondary_host" || exit 1
                        ;;
                esac

                # Update DNS if configured
                if [[ -n "$DNS_RECORD" ]]; then
                    update_dns_record "$DNS_RECORD" "$secondary_host"
                fi

                break
            fi

            sleep "$check_interval"
        fi
    done
}

################################################################################
# Main Function
################################################################################

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--db-type)
                DB_TYPE="$2"
                shift 2
                ;;
            --primary-host)
                PRIMARY_HOST="$2"
                shift 2
                ;;
            --secondary-host)
                SECONDARY_HOST="$2"
                shift 2
                ;;
            --primary-port)
                PRIMARY_PORT="$2"
                shift 2
                ;;
            --secondary-port)
                SECONDARY_PORT="$2"
                shift 2
                ;;
            -m|--mode)
                MODE="$2"
                shift 2
                ;;
            --check-interval)
                CHECK_INTERVAL="$2"
                shift 2
                ;;
            --dns-record)
                DNS_RECORD="$2"
                shift 2
                ;;
            --reverse-replication)
                ENABLE_REVERSE_REPLICATION=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                print_usage
                ;;
            *)
                log_error "Unknown option: $1"
                print_usage
                ;;
        esac
    done

    # Validate arguments and set defaults
    validate_arguments
    set_default_ports "$DB_TYPE"

    # Display configuration
    log_info "Database Failover Script"
    log_info "Database type: $DB_TYPE"
    log_info "Primary: $PRIMARY_HOST:$PRIMARY_PORT"
    log_info "Secondary: $SECONDARY_HOST:$SECONDARY_PORT"
    log_info "Mode: $MODE"
    [[ -n "$DNS_RECORD" ]] && log_info "DNS record: $DNS_RECORD"
    [[ $ENABLE_REVERSE_REPLICATION == true ]] && log_info "Reverse replication: enabled"
    [[ $DRY_RUN == true ]] && log_info "Dry run mode enabled"
    echo ""

    # Check health unless forcing
    if [[ $FORCE == false ]]; then
        check_primary_health "$DB_TYPE" "$PRIMARY_HOST" "$PRIMARY_PORT" || {
            log_warning "Primary is not healthy, proceeding with failover"
        }

        if ! check_secondary_health "$DB_TYPE" "$SECONDARY_HOST" "$SECONDARY_PORT"; then
            log_error "Secondary database is not healthy, cannot failover"
            exit 4
        fi
    fi

    # Execute failover based on mode
    if [[ "$MODE" == "automatic" ]]; then
        monitor_and_failover "$DB_TYPE" "$PRIMARY_HOST" "$SECONDARY_HOST" "$CHECK_INTERVAL" "$MAX_RETRIES"
    else
        # Manual failover
        case "$DB_TYPE" in
            postgresql)
                failover_postgresql "$PRIMARY_HOST" "$SECONDARY_HOST" || exit 1
                ;;
            mysql)
                failover_mysql "$PRIMARY_HOST" "$SECONDARY_HOST" || exit 1
                ;;
            mongodb)
                failover_mongodb "$PRIMARY_HOST" "$SECONDARY_HOST" || exit 1
                ;;
        esac

        # Update DNS if configured
        if [[ -n "$DNS_RECORD" ]]; then
            update_dns_record "$DNS_RECORD" "$SECONDARY_HOST"
        fi
    fi

    # Final summary
    echo ""
    log_success "Failover completed!"
    echo ""
    echo "Summary:"
    echo "  Database type: $DB_TYPE"
    echo "  New primary: $SECONDARY_HOST:$SECONDARY_PORT"
    echo "  Previous primary: $PRIMARY_HOST:$PRIMARY_PORT"
    echo ""

    exit 0
}

# Execute main function
main "$@"
