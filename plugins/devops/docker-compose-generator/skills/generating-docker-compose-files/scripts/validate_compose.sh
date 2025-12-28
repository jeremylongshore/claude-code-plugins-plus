#!/bin/bash

###############################################################################
# validate_compose.sh
#
# Validates Docker Compose files against docker-compose config schema
#
# Usage:
#   ./validate_compose.sh --file docker-compose.yml
#   ./validate_compose.sh --file docker-compose.yml --strict
#
# Exit Codes:
#   0 - Validation successful
#   1 - Validation failed or missing dependencies
#   2 - Invalid arguments
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE=""
STRICT_MODE=false
VERBOSE=false

###############################################################################
# Functions
###############################################################################

show_help() {
    cat << EOF
Validates Docker Compose files using docker-compose config

Usage: $(basename "$0") [OPTIONS]

Options:
    -f, --file FILE      Path to Docker Compose file (required)
    -s, --strict         Enable strict validation mode
    -v, --verbose        Enable verbose output
    -h, --help          Show this help message

Examples:
    $(basename "$0") --file docker-compose.yml
    $(basename "$0") --file docker-compose.prod.yml --strict --verbose

EOF
    exit 0
}

log_error() {
    echo -e "${RED}ERROR:${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}SUCCESS:${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}WARNING:${NC} $*"
}

log_info() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${YELLOW}INFO:${NC} $*"
    fi
}

check_dependencies() {
    local missing_deps=0

    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed"
        missing_deps=$((missing_deps + 1))
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed"
        missing_deps=$((missing_deps + 1))
    fi

    if [[ $missing_deps -gt 0 ]]; then
        log_error "Missing $missing_deps required dependencies"
        return 1
    fi

    log_info "All dependencies found"
    return 0
}

validate_file_exists() {
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        return 1
    fi

    log_info "Found compose file: $COMPOSE_FILE"
    return 0
}

validate_yaml_syntax() {
    log_info "Validating YAML syntax..."

    # Use docker-compose config to validate
    if ! docker-compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
        log_error "YAML syntax validation failed"
        docker-compose -f "$COMPOSE_FILE" config 2>&1 | head -20
        return 1
    fi

    log_success "YAML syntax is valid"
    return 0
}

validate_services() {
    log_info "Validating services configuration..."

    local service_count
    service_count=$(docker-compose -f "$COMPOSE_FILE" config | grep -c "^  [a-zA-Z_]" || echo 0)

    if [[ $service_count -eq 0 ]]; then
        log_warning "No services found in compose file"
    else
        log_info "Found $service_count service(s)"
    fi

    return 0
}

validate_images() {
    log_info "Validating image references..."

    local invalid_images=0

    # Check for images that reference local Dockerfiles
    while IFS= read -r line; do
        if [[ $line =~ build: ]]; then
            log_info "Build context detected: $line"
        elif [[ $line =~ image: ]]; then
            log_info "Image reference: $line"
        fi
    done < <(docker-compose -f "$COMPOSE_FILE" config | grep -E "^\s*(build:|image:)" || true)

    return 0
}

validate_ports() {
    log_info "Validating port configurations..."

    local port_conflicts=0
    local ports_list=""

    ports_list=$(docker-compose -f "$COMPOSE_FILE" config | grep -E "^\s+-\s+[0-9]+:" || true)

    if [[ -z "$ports_list" ]]; then
        log_info "No ports explicitly mapped"
    else
        log_info "Port mappings found:"
        echo "$ports_list" | sed 's/^/  /'
    fi

    return 0
}

validate_volumes() {
    log_info "Validating volume configurations..."

    local volume_count=0
    volume_count=$(docker-compose -f "$COMPOSE_FILE" config | grep -c "^\s*-\s*/" || echo 0)

    if [[ $volume_count -eq 0 ]]; then
        log_info "No volume mounts configured"
    else
        log_info "Found $volume_count volume mount(s)"
    fi

    return 0
}

validate_environment_vars() {
    log_info "Validating environment variables..."

    local undefined_vars=0

    # Check for undefined variables referenced in the compose file
    while IFS= read -r line; do
        if [[ $line =~ \${[A-Z_]+} ]]; then
            log_warning "Variable reference found: $line"
        fi
    done < <(docker-compose -f "$COMPOSE_FILE" config | grep '\${' || true)

    return 0
}

validate_strict_mode() {
    if [[ "$STRICT_MODE" != "true" ]]; then
        return 0
    fi

    log_info "Running strict validation checks..."

    local errors=0

    # Check for recommended best practices
    local config
    config=$(docker-compose -f "$COMPOSE_FILE" config)

    # Check for health checks
    if ! echo "$config" | grep -q "healthcheck:"; then
        log_warning "No health checks defined (strict mode)"
        errors=$((errors + 1))
    fi

    # Check for restart policies
    if ! echo "$config" | grep -q "restart_policy:"; then
        log_warning "No restart policies defined (strict mode)"
        errors=$((errors + 1))
    fi

    # Check for logging configuration
    if ! echo "$config" | grep -q "logging:"; then
        log_warning "No logging configuration defined (strict mode)"
        errors=$((errors + 1))
    fi

    if [[ $errors -gt 0 ]]; then
        log_warning "Strict mode found $errors warning(s)"
        return 0  # Don't fail on strict warnings
    fi

    return 0
}

###############################################################################
# Main
###############################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            -s|--strict)
                STRICT_MODE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 2
                ;;
        esac
    done

    # Validate arguments
    if [[ -z "$COMPOSE_FILE" ]]; then
        log_error "Docker Compose file is required"
        echo "Use --help for usage information"
        exit 2
    fi

    log_info "Starting Docker Compose validation"
    log_info "File: $COMPOSE_FILE"
    log_info "Strict mode: $STRICT_MODE"

    # Run validation checks
    if ! check_dependencies; then
        exit 1
    fi

    if ! validate_file_exists; then
        exit 1
    fi

    if ! validate_yaml_syntax; then
        exit 1
    fi

    validate_services
    validate_images
    validate_ports
    validate_volumes
    validate_environment_vars
    validate_strict_mode

    log_success "Docker Compose file validation complete"
    exit 0
}

main "$@"
