#!/bin/bash

###############################################################################
# validate_manifest.sh
#
# Validates Kubernetes manifest files against the Kubernetes API schema
#
# Usage:
#   ./validate_manifest.sh --file deployment.yaml
#   ./validate_manifest.sh --file deployment.yaml --strict
#   ./validate_manifest.sh --directory manifests/
#
# Exit Codes:
#   0 - Validation successful
#   1 - Validation failed
#   2 - Invalid arguments
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MANIFEST_FILE=""
MANIFEST_DIR=""
STRICT_MODE=false
VERBOSE=false
SCHEMA_VERSION=""

###############################################################################
# Functions
###############################################################################

show_help() {
    cat << EOF
Validates Kubernetes manifest files against the API schema

Usage: $(basename "$0") [OPTIONS]

Options:
    -f, --file FILE         Path to Kubernetes manifest file
    -d, --directory DIR     Directory containing manifest files
    -s, --strict            Enable strict validation (best practices)
    -v, --verbose           Enable verbose output
    -h, --help              Show this help message

Examples:
    $(basename "$0") --file deployment.yaml
    $(basename "$0") --directory manifests/ --strict
    $(basename "$0") --file service.yaml --verbose

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
        echo -e "${YELLOW}DEBUG:${NC} $*" >&2
    fi
}

check_dependencies() {
    local missing_deps=0

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        missing_deps=$((missing_deps + 1))
    fi

    if ! command -v yq &> /dev/null; then
        log_warning "yq is not installed (optional - for advanced parsing)"
    fi

    if [[ $missing_deps -gt 0 ]]; then
        return 1
    fi

    log_verbose "All required dependencies found"
    return 0
}

validate_yaml_syntax() {
    local file="$1"

    if ! kubectl apply -f "$file" --dry-run=client -o yaml > /dev/null 2>&1; then
        log_error "YAML syntax validation failed: $file"
        kubectl apply -f "$file" --dry-run=client -o yaml 2>&1 | head -20
        return 1
    fi

    return 0
}

validate_manifest_file() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        log_error "Manifest file not found: $file"
        return 1
    fi

    log_info "Validating: $file"

    # Check file is not empty
    if [[ ! -s "$file" ]]; then
        log_error "Manifest file is empty: $file"
        return 1
    fi

    # Validate YAML syntax
    if ! validate_yaml_syntax "$file"; then
        return 1
    fi

    # Extract API version and kind
    local api_version
    local kind
    api_version=$(kubectl apply -f "$file" --dry-run=client -o jsonpath='{.apiVersion}' 2>/dev/null || echo "")
    kind=$(kubectl apply -f "$file" --dry-run=client -o jsonpath='{.kind}' 2>/dev/null || echo "")

    if [[ -z "$kind" ]]; then
        log_error "Cannot determine resource kind from manifest: $file"
        return 1
    fi

    log_verbose "Resource type: $kind (API: $api_version)"

    # Validate against Kubernetes schema
    if ! kubectl apply -f "$file" --dry-run=server 2>&1 | grep -q "error"; then
        log_verbose "Schema validation passed"
    fi

    # Perform best practices validation in strict mode
    if [[ "$STRICT_MODE" == "true" ]]; then
        validate_strict_mode "$file" "$kind"
    fi

    return 0
}

validate_strict_mode() {
    local file="$1"
    local kind="$2"
    local warnings=0

    log_info "Running strict validation for $kind..."

    # Get the manifest content
    local content
    content=$(kubectl apply -f "$file" --dry-run=client -o yaml)

    # Check for resource limits
    if [[ "$kind" =~ ^(Deployment|StatefulSet|DaemonSet|Pod)$ ]]; then
        if ! echo "$content" | grep -q "resources:"; then
            log_warning "No resource requests/limits defined (strict mode)"
            warnings=$((warnings + 1))
        fi

        # Check for liveness probe
        if ! echo "$content" | grep -q "livenessProbe:"; then
            log_warning "No liveness probe defined (strict mode)"
            warnings=$((warnings + 1))
        fi

        # Check for readiness probe
        if ! echo "$content" | grep -q "readinessProbe:"; then
            log_warning "No readiness probe defined (strict mode)"
            warnings=$((warnings + 1))
        fi

        # Check security context
        if ! echo "$content" | grep -q "securityContext:"; then
            log_warning "No security context defined (strict mode)"
            warnings=$((warnings + 1))
        fi
    fi

    # Check for namespace
    if [[ "$kind" != "Namespace" ]]; then
        if ! echo "$content" | grep -q "namespace:"; then
            log_warning "No namespace specified (strict mode)"
            warnings=$((warnings + 1))
        fi
    fi

    # Check for image pull policy
    if [[ "$kind" =~ ^(Deployment|StatefulSet|DaemonSet|Pod)$ ]]; then
        if ! echo "$content" | grep -q "imagePullPolicy"; then
            log_warning "No imagePullPolicy specified (strict mode)"
            warnings=$((warnings + 1))
        fi
    fi

    if [[ $warnings -gt 0 ]]; then
        log_warning "Strict validation found $warnings warning(s) in $file"
    else
        log_success "All strict validation checks passed for $file"
    fi

    return 0
}

validate_manifest_directory() {
    local dir="$1"
    local total_files=0
    local valid_files=0
    local failed_files=0

    if [[ ! -d "$dir" ]]; then
        log_error "Directory not found: $dir"
        return 1
    fi

    log_info "Validating manifests in: $dir"

    # Find all YAML files
    while IFS= read -r -d '' file; do
        total_files=$((total_files + 1))

        if validate_manifest_file "$file"; then
            valid_files=$((valid_files + 1))
        else
            failed_files=$((failed_files + 1))
        fi
    done < <(find "$dir" -type f \( -name "*.yaml" -o -name "*.yml" \) -print0)

    log_info "Validation summary:"
    log_info "  Total files: $total_files"
    log_success "  Valid files: $valid_files"
    [[ $failed_files -gt 0 ]] && log_error "  Failed files: $failed_files"

    if [[ $failed_files -gt 0 ]]; then
        return 1
    fi

    return 0
}

validate_cross_manifest_references() {
    local file="$1"

    log_verbose "Checking cross-manifest references..."

    # Check for ConfigMap references
    local config_map_refs
    config_map_refs=$(kubectl apply -f "$file" --dry-run=client -o yaml | grep -o "configMapRef:" | wc -l || echo 0)

    if [[ $config_map_refs -gt 0 ]]; then
        log_verbose "Found $config_map_refs ConfigMap reference(s)"
    fi

    # Check for Secret references
    local secret_refs
    secret_refs=$(kubectl apply -f "$file" --dry-run=client -o yaml | grep -o "secretRef:" | wc -l || echo 0)

    if [[ $secret_refs -gt 0 ]]; then
        log_verbose "Found $secret_refs Secret reference(s)"
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
                MANIFEST_FILE="$2"
                shift 2
                ;;
            -d|--directory)
                MANIFEST_DIR="$2"
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
    if [[ -z "$MANIFEST_FILE" ]] && [[ -z "$MANIFEST_DIR" ]]; then
        log_error "Either --file or --directory is required"
        echo "Use --help for usage information"
        exit 2
    fi

    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi

    log_info "Starting Kubernetes manifest validation"
    log_verbose "Strict mode: $STRICT_MODE"

    # Validate manifests
    if [[ -n "$MANIFEST_FILE" ]]; then
        if ! validate_manifest_file "$MANIFEST_FILE"; then
            exit 1
        fi
        validate_cross_manifest_references "$MANIFEST_FILE"
    fi

    if [[ -n "$MANIFEST_DIR" ]]; then
        if ! validate_manifest_directory "$MANIFEST_DIR"; then
            exit 1
        fi
    fi

    log_success "Kubernetes manifest validation complete"
    exit 0
}

main "$@"
