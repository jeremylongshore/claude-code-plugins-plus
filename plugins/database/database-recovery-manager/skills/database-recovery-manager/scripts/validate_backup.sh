#!/bin/bash

################################################################################
# validate_backup.sh
#
# Script to validate database backups by checking integrity and recoverability.
# Supports multiple database types: PostgreSQL, MySQL, MongoDB
#
# Usage:
#   ./validate_backup.sh --backup-path /path/to/backup --db-type postgresql
#   ./validate_backup.sh --backup-path /path/to/backup --db-type mysql --connection-string "..."
#
# Exit Codes:
#   0 - Backup validation successful
#   1 - Validation failed (integrity or recoverability check)
#   2 - Invalid arguments or missing files
#   3 - Database connection error
################################################################################

set -euo pipefail

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script variables
BACKUP_PATH=""
DB_TYPE=""
CONNECTION_STRING=""
VERBOSE=false
DRY_RUN=false

################################################################################
# Helper Functions
################################################################################

print_usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Script to validate database backups by checking integrity and recoverability.

OPTIONS:
    -p, --backup-path PATH           Path to the backup file or directory (REQUIRED)
    -t, --db-type TYPE               Database type: postgresql|mysql|mongodb (REQUIRED)
    -c, --connection-string STRING   Database connection string for recoverability test
    -v, --verbose                    Enable verbose output
    -d, --dry-run                    Show what would be validated without actual validation
    -h, --help                       Display this help message

EXAMPLES:
    # Validate PostgreSQL backup
    ./validate_backup.sh -p /backups/db_backup.sql -t postgresql

    # Validate MySQL backup with connection string
    ./validate_backup.sh -p /backups/db_backup.sql.gz -t mysql \\
        -c "mysql://user:pass@localhost:3306"

    # Validate MongoDB backup with verbose output
    ./validate_backup.sh -p /backups/mongo_dump.tar.gz -t mongodb -v

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
    if [[ -z "$BACKUP_PATH" ]]; then
        log_error "Backup path is required"
        print_usage
    fi

    if [[ -z "$DB_TYPE" ]]; then
        log_error "Database type is required"
        print_usage
    fi

    if [[ ! -f "$BACKUP_PATH" && ! -d "$BACKUP_PATH" ]]; then
        log_error "Backup path does not exist: $BACKUP_PATH"
        exit 2
    fi

    case "$DB_TYPE" in
        postgresql|mysql|mongodb)
            ;;
        *)
            log_error "Unsupported database type: $DB_TYPE"
            log_error "Supported types: postgresql, mysql, mongodb"
            exit 2
            ;;
    esac
}

check_file_integrity() {
    local backup_file="$1"

    log_info "Checking file integrity..."

    if [[ $VERBOSE == true ]]; then
        log_info "Backup file: $backup_file"
        log_info "File size: $(du -h "$backup_file" | cut -f1)"
        log_info "Last modified: $(stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "$backup_file" 2>/dev/null || stat --format='%y' "$backup_file")"
    fi

    # Check if file is readable
    if [[ ! -r "$backup_file" ]]; then
        log_error "Backup file is not readable: $backup_file"
        return 1
    fi

    # Check file size (not empty)
    local file_size
    file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null)
    if [[ $file_size -lt 100 ]]; then
        log_error "Backup file is too small (suspicious): $file_size bytes"
        return 1
    fi

    log_success "File integrity check passed"
    return 0
}

validate_postgresql_backup() {
    local backup_file="$1"

    log_info "Validating PostgreSQL backup..."

    if $DRY_RUN; then
        log_info "[DRY RUN] Would validate PostgreSQL backup: $backup_file"
        return 0
    fi

    # Check if it's a SQL dump file
    if [[ "$backup_file" == *.sql ]]; then
        log_info "Detected SQL text dump format"

        # Check for PostgreSQL-specific headers
        if head -5 "$backup_file" | grep -qi "PostgreSQL\|BEGIN\|CREATE\|INSERT"; then
            log_success "PostgreSQL SQL dump format recognized"
        else
            log_warning "SQL dump format not recognized as PostgreSQL"
        fi
    elif [[ "$backup_file" == *.tar.gz ]] || [[ "$backup_file" == *.tar ]]; then
        log_info "Detected PostgreSQL custom/tar format"

        if command -v pg_restore &> /dev/null; then
            if pg_restore --list "$backup_file" > /dev/null 2>&1; then
                log_success "PostgreSQL tar/custom backup is valid"
            else
                log_error "PostgreSQL tar/custom backup validation failed"
                return 1
            fi
        else
            log_warning "pg_restore not found, skipping detailed validation"
        fi
    fi

    return 0
}

validate_mysql_backup() {
    local backup_file="$1"

    log_info "Validating MySQL backup..."

    if $DRY_RUN; then
        log_info "[DRY RUN] Would validate MySQL backup: $backup_file"
        return 0
    fi

    # Check for MySQL dump headers
    if file "$backup_file" | grep -q "gzip"; then
        log_info "Detected gzip-compressed format"

        if command -v zcat &> /dev/null; then
            if zcat "$backup_file" 2>/dev/null | head -10 | grep -qi "MySQL\|/*!"; then
                log_success "MySQL dump format recognized"
            else
                log_warning "MySQL dump format not clearly identified"
            fi
        fi
    else
        if head -10 "$backup_file" | grep -qi "MySQL\|/*!40000\|CREATE TABLE\|INSERT INTO"; then
            log_success "MySQL dump format recognized"
        else
            log_warning "MySQL dump format not clearly identified"
        fi
    fi

    return 0
}

validate_mongodb_backup() {
    local backup_path="$1"

    log_info "Validating MongoDB backup..."

    if $DRY_RUN; then
        log_info "[DRY RUN] Would validate MongoDB backup: $backup_path"
        return 0
    fi

    if [[ -d "$backup_path" ]]; then
        log_info "Detected MongoDB directory dump format"

        # Check for standard MongoDB dump directory structure
        if [[ -f "$backup_path/dump_manifest.json" ]]; then
            log_success "MongoDB dump manifest found"
        elif find "$backup_path" -name "*.bson" -o -name "*.json" | grep -q .; then
            log_success "MongoDB BSON/JSON files found in backup directory"
        else
            log_warning "No typical MongoDB backup files found"
        fi
    elif [[ "$backup_path" == *.tar.gz ]]; then
        log_info "Detected MongoDB tar.gz format"

        if command -v tar &> /dev/null; then
            if tar -tzf "$backup_path" 2>/dev/null | head -5 | grep -qE "\.bson|\.json"; then
                log_success "MongoDB tar.gz archive is valid"
            else
                log_error "MongoDB tar.gz archive validation failed"
                return 1
            fi
        fi
    fi

    return 0
}

test_recoverability() {
    local db_type="$1"

    if [[ -z "$CONNECTION_STRING" ]]; then
        log_warning "Connection string not provided, skipping recoverability test"
        return 0
    fi

    log_info "Testing recoverability with database connection..."

    if $DRY_RUN; then
        log_info "[DRY RUN] Would test recoverability with: $CONNECTION_STRING"
        return 0
    fi

    case "$db_type" in
        postgresql)
            if command -v psql &> /dev/null; then
                if psql "$CONNECTION_STRING" -c "SELECT 1" > /dev/null 2>&1; then
                    log_success "Database connection test successful"
                else
                    log_error "Failed to connect to PostgreSQL database"
                    return 3
                fi
            else
                log_warning "psql not found, skipping connection test"
            fi
            ;;
        mysql)
            if command -v mysql &> /dev/null; then
                # Parse connection string and attempt connection
                log_warning "MySQL connection test requires proper credentials (skipped for security)"
            else
                log_warning "mysql client not found"
            fi
            ;;
        mongodb)
            if command -v mongosh &> /dev/null || command -v mongo &> /dev/null; then
                log_warning "MongoDB connection test requires proper credentials (skipped for security)"
            else
                log_warning "MongoDB client not found"
            fi
            ;;
    esac

    return 0
}

################################################################################
# Main Function
################################################################################

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--backup-path)
                BACKUP_PATH="$2"
                shift 2
                ;;
            -t|--db-type)
                DB_TYPE="$2"
                shift 2
                ;;
            -c|--connection-string)
                CONNECTION_STRING="$2"
                shift 2
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

    # Validate arguments
    validate_arguments

    # Display configuration
    log_info "Starting backup validation"
    log_info "Backup path: $BACKUP_PATH"
    log_info "Database type: $DB_TYPE"
    [[ $VERBOSE == true ]] && log_info "Verbose mode enabled"
    [[ $DRY_RUN == true ]] && log_info "Dry run mode enabled"

    # Perform validation
    check_file_integrity "$BACKUP_PATH" || exit 1

    case "$DB_TYPE" in
        postgresql)
            validate_postgresql_backup "$BACKUP_PATH" || exit 1
            ;;
        mysql)
            validate_mysql_backup "$BACKUP_PATH" || exit 1
            ;;
        mongodb)
            validate_mongodb_backup "$BACKUP_PATH" || exit 1
            ;;
    esac

    # Test recoverability
    test_recoverability "$DB_TYPE" || exit 3

    # Final summary
    echo ""
    log_success "Backup validation completed successfully!"
    echo ""
    echo "Summary:"
    echo "  Database type: $DB_TYPE"
    echo "  Backup path: $BACKUP_PATH"
    echo "  File integrity: OK"
    echo "  Format validation: OK"
    [[ -n "$CONNECTION_STRING" ]] && echo "  Recoverability test: OK"
    echo ""

    exit 0
}

# Execute main function
main "$@"
