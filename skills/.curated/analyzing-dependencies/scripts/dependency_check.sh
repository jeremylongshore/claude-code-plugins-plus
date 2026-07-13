#!/bin/bash

###############################################################################
# dependency_check.sh
#
# Execute dependency checks using various package managers
#
# Supports:
#  - npm (Node.js)
#  - pip (Python)
#  - composer (PHP)
#  - bundler (Ruby)
#  - cargo (Rust)
#
# Usage:
#   ./dependency_check.sh
#   ./dependency_check.sh --format json
#   ./dependency_check.sh --tool npm --output report.json
#
# Exit Codes:
#   0 - Check successful
#   1 - Vulnerabilities found
#   2 - Invalid arguments
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Configuration
TOOL=""
OUTPUT_FILE=""
OUTPUT_FORMAT="text"
VERBOSE=false
AUTO_DETECT=true
REPORT_VULNERABILITIES=true
SEVERITY_THRESHOLD="low"

###############################################################################
# Functions
###############################################################################

show_help() {
    cat << EOF
Check project dependencies for vulnerabilities

Usage: $(basename "$0") [OPTIONS]

Options:
    --tool TOOL            Package manager: npm, pip, composer, bundler, cargo
    --format FORMAT        Output format: text, json (default: text)
    --output FILE          Save report to file
    --severity LEVEL       Minimum severity to report: low, moderate, high, critical
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

Examples:
    $(basename "$0")
    $(basename "$0") --tool npm
    $(basename "$0") --format json --output report.json
    $(basename "$0") --tool pip --severity high

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
    echo -e "${BLUE}INFO:${NC} $*"
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${GRAY}DEBUG:${NC} $*" >&2
    fi
}

detect_package_managers() {
    local detected=()

    # Check for npm
    if [[ -f "package.json" ]] && command -v npm &> /dev/null; then
        detected+=(npm)
        log_verbose "Detected npm project"
    fi

    # Check for pip
    if [[ -f "requirements.txt" ]] || [[ -f "Pipfile" ]] || [[ -f "pyproject.toml" ]]; then
        if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
            detected+=(pip)
            log_verbose "Detected Python project"
        fi
    fi

    # Check for composer
    if [[ -f "composer.json" ]] && command -v composer &> /dev/null; then
        detected+=(composer)
        log_verbose "Detected PHP/Composer project"
    fi

    # Check for bundler
    if [[ -f "Gemfile" ]] && command -v bundle &> /dev/null; then
        detected+=(bundler)
        log_verbose "Detected Ruby/Bundler project"
    fi

    # Check for cargo
    if [[ -f "Cargo.toml" ]] && command -v cargo &> /dev/null; then
        detected+=(cargo)
        log_verbose "Detected Rust/Cargo project"
    fi

    echo "${detected[@]}"
}

check_npm_vulnerabilities() {
    log_info "Checking npm dependencies..."

    if ! command -v npm &> /dev/null; then
        log_warning "npm is not installed"
        return 0
    fi

    if [[ ! -f "package.json" ]]; then
        log_verbose "No package.json found"
        return 0
    fi

    # Run npm audit
    local audit_output
    local vulnerabilities=0

    audit_output=$(npm audit --json 2>/dev/null || echo "{}")

    # Parse JSON output
    vulnerabilities=$(echo "$audit_output" | jq '.metadata.vulnerabilities.total // 0' 2>/dev/null || echo 0)

    if [[ $vulnerabilities -gt 0 ]]; then
        log_warning "Found $vulnerabilities npm vulnerability/vulnerabilities"

        if [[ "$OUTPUT_FORMAT" == "json" ]]; then
            echo "$audit_output" >> "${OUTPUT_FILE:-.}"
        else
            echo "$audit_output" | jq '.vulnerabilities // empty' 2>/dev/null | head -50
        fi

        return 1
    else
        log_success "No npm vulnerabilities found"
        return 0
    fi
}

check_pip_vulnerabilities() {
    log_info "Checking Python dependencies..."

    local pip_cmd="pip"
    if ! command -v pip &> /dev/null && command -v pip3 &> /dev/null; then
        pip_cmd="pip3"
    fi

    if ! command -v "$pip_cmd" &> /dev/null; then
        log_warning "pip is not installed"
        return 0
    fi

    # Check for requirements files
    local requirements_file=""
    if [[ -f "requirements.txt" ]]; then
        requirements_file="requirements.txt"
    fi

    if [[ -z "$requirements_file" ]]; then
        log_verbose "No requirements.txt found"
        return 0
    fi

    # Use safety to check for vulnerabilities (if available)
    if command -v safety &> /dev/null; then
        log_verbose "Using safety tool for vulnerability check"

        local safety_output
        safety_output=$(safety check --json 2>/dev/null || echo "[]")

        local vulnerability_count
        vulnerability_count=$(echo "$safety_output" | jq 'length' 2>/dev/null || echo 0)

        if [[ $vulnerability_count -gt 0 ]]; then
            log_warning "Found $vulnerability_count Python dependency vulnerability/vulnerabilities"

            if [[ "$OUTPUT_FORMAT" == "json" ]]; then
                echo "$safety_output" >> "${OUTPUT_FILE:-.}"
            else
                echo "$safety_output" | jq '.' | head -50
            fi

            return 1
        else
            log_success "No Python vulnerabilities found"
            return 0
        fi
    else
        log_verbose "safety tool not found (install with: pip install safety)"
    fi

    return 0
}

check_composer_vulnerabilities() {
    log_info "Checking PHP/Composer dependencies..."

    if ! command -v composer &> /dev/null; then
        log_warning "composer is not installed"
        return 0
    fi

    if [[ ! -f "composer.json" ]]; then
        log_verbose "No composer.json found"
        return 0
    fi

    # Run composer audit
    local audit_output
    local vulnerabilities=0

    if composer audit --format=json &> /dev/null; then
        audit_output=$(composer audit --format=json 2>/dev/null || echo "{}")
        vulnerabilities=$(echo "$audit_output" | jq '.vulnerabilities // 0' 2>/dev/null || echo 0)

        if [[ $vulnerabilities -gt 0 ]]; then
            log_warning "Found $vulnerabilities Composer vulnerability/vulnerabilities"

            if [[ "$OUTPUT_FORMAT" == "json" ]]; then
                echo "$audit_output" >> "${OUTPUT_FILE:-.}"
            else
                echo "$audit_output" | jq '.' | head -50
            fi

            return 1
        else
            log_success "No Composer vulnerabilities found"
            return 0
        fi
    else
        log_verbose "composer audit not available"
    fi

    return 0
}

check_bundler_vulnerabilities() {
    log_info "Checking Ruby/Bundler dependencies..."

    if ! command -v bundle &> /dev/null; then
        log_warning "bundler is not installed"
        return 0
    fi

    if [[ ! -f "Gemfile" ]]; then
        log_verbose "No Gemfile found"
        return 0
    fi

    # Use bundler-audit if available
    if command -v bundler-audit &> /dev/null || gem list | grep -q bundler-audit; then
        log_verbose "Using bundler-audit for vulnerability check"

        local audit_output
        audit_output=$(bundler-audit check --json 2>/dev/null || echo "[]")

        local vulnerability_count
        vulnerability_count=$(echo "$audit_output" | jq 'length' 2>/dev/null || echo 0)

        if [[ $vulnerability_count -gt 0 ]]; then
            log_warning "Found $vulnerability_count Bundler vulnerability/vulnerabilities"

            if [[ "$OUTPUT_FORMAT" == "json" ]]; then
                echo "$audit_output" >> "${OUTPUT_FILE:-.}"
            else
                echo "$audit_output" | jq '.' | head -50
            fi

            return 1
        else
            log_success "No Bundler vulnerabilities found"
            return 0
        fi
    else
        log_verbose "bundler-audit not found (install with: gem install bundler-audit)"
    fi

    return 0
}

check_cargo_vulnerabilities() {
    log_info "Checking Rust/Cargo dependencies..."

    if ! command -v cargo &> /dev/null; then
        log_warning "cargo is not installed"
        return 0
    fi

    if [[ ! -f "Cargo.toml" ]]; then
        log_verbose "No Cargo.toml found"
        return 0
    fi

    # Use cargo-audit if available
    if command -v cargo-audit &> /dev/null || cargo audit --version &> /dev/null; then
        log_verbose "Using cargo-audit for vulnerability check"

        local audit_output
        audit_output=$(cargo audit --json 2>/dev/null || echo "{}")

        local vulnerability_count
        vulnerability_count=$(echo "$audit_output" | jq '.vulnerabilities | length' 2>/dev/null || echo 0)

        if [[ $vulnerability_count -gt 0 ]]; then
            log_warning "Found $vulnerability_count Cargo vulnerability/vulnerabilities"

            if [[ "$OUTPUT_FORMAT" == "json" ]]; then
                echo "$audit_output" >> "${OUTPUT_FILE:-.}"
            else
                echo "$audit_output" | jq '.' | head -50
            fi

            return 1
        else
            log_success "No Cargo vulnerabilities found"
            return 0
        fi
    else
        log_verbose "cargo-audit not found"
    fi

    return 0
}

run_all_checks() {
    local detected_tools
    local overall_status=0

    detected_tools=$(detect_package_managers)

    if [[ -z "$detected_tools" ]]; then
        log_warning "No package managers detected"
        return 0
    fi

    log_info "Running dependency checks..."

    for tool in $detected_tools; do
        case "$tool" in
            npm)
                check_npm_vulnerabilities || overall_status=1
                ;;
            pip)
                check_pip_vulnerabilities || overall_status=1
                ;;
            composer)
                check_composer_vulnerabilities || overall_status=1
                ;;
            bundler)
                check_bundler_vulnerabilities || overall_status=1
                ;;
            cargo)
                check_cargo_vulnerabilities || overall_status=1
                ;;
        esac
    done

    return $overall_status
}

generate_report() {
    local output="$1"

    log_info "Generating report..."

    if [[ -n "$output" ]]; then
        log_info "Report saved to: $output"
    fi
}

###############################################################################
# Main
###############################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --tool)
                TOOL="$2"
                AUTO_DETECT=false
                shift 2
                ;;
            --format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            --severity)
                SEVERITY_THRESHOLD="$2"
                shift 2
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

    log_info "Dependency Vulnerability Check"
    log_verbose "Format: $OUTPUT_FORMAT"
    log_verbose "Severity threshold: $SEVERITY_THRESHOLD"
    [[ -n "$OUTPUT_FILE" ]] && log_verbose "Output file: $OUTPUT_FILE"

    # Run checks
    if [[ "$AUTO_DETECT" == "true" ]]; then
        if ! run_all_checks; then
            generate_report "$OUTPUT_FILE"
            exit 1
        fi
    else
        case "$TOOL" in
            npm)
                check_npm_vulnerabilities || exit 1
                ;;
            pip)
                check_pip_vulnerabilities || exit 1
                ;;
            composer)
                check_composer_vulnerabilities || exit 1
                ;;
            bundler)
                check_bundler_vulnerabilities || exit 1
                ;;
            cargo)
                check_cargo_vulnerabilities || exit 1
                ;;
            *)
                log_error "Unknown tool: $TOOL"
                exit 2
                ;;
        esac
    fi

    generate_report "$OUTPUT_FILE"
    log_success "Dependency check completed"
    exit 0
}

main "$@"
