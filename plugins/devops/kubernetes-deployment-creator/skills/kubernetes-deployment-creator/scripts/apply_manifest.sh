#!/bin/bash

###############################################################################
# apply_manifest.sh
#
# Applies a Kubernetes manifest file to the cluster
#
# Usage:
#   ./apply_manifest.sh --file deployment.yaml
#   ./apply_manifest.sh --file deployment.yaml --namespace prod
#   ./apply_manifest.sh --directory manifests/ --wait
#
# Exit Codes:
#   0 - Apply successful
#   1 - Apply failed
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
NAMESPACE=""
DRY_RUN=false
WAIT_FOR_READY=false
VERBOSE=false
FORCE=false

###############################################################################
# Functions
###############################################################################

show_help() {
    cat << EOF
Apply Kubernetes manifest files to the cluster

Usage: $(basename "$0") [OPTIONS]

Options:
    -f, --file FILE         Path to Kubernetes manifest file
    -d, --directory DIR     Directory containing manifest files
    -n, --namespace NS      Kubernetes namespace
    --dry-run              Show what would be applied without executing
    --wait                 Wait for resources to be ready
    --force                Force apply (overwrite conflicts)
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

Examples:
    $(basename "$0") --file deployment.yaml
    $(basename "$0") --file deployment.yaml --namespace production
    $(basename "$0") --directory manifests/ --wait
    $(basename "$0") --file deployment.yaml --dry-run

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

run_kubectl() {
    local args=("$@")

    if [[ "$DRY_RUN" == "true" ]]; then
        args+=(--dry-run=client)
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        log_verbose "kubectl ${args[*]}"
    fi

    kubectl "${args[@]}"
}

check_dependencies() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        return 1
    fi

    log_verbose "kubectl found"
    return 0
}

check_cluster_connection() {
    log_info "Checking cluster connection..."

    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        log_info "Check kubeconfig: kubectl cluster-info"
        return 1
    fi

    log_success "Connected to cluster"
    return 0
}

ensure_namespace_exists() {
    local ns="$1"

    if [[ -z "$ns" ]]; then
        return 0
    fi

    log_verbose "Checking namespace: $ns"

    if ! kubectl get namespace "$ns" &> /dev/null; then
        log_warning "Namespace does not exist: $ns"

        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would create namespace: $ns"
        else
            log_info "Creating namespace: $ns"
            if ! kubectl create namespace "$ns"; then
                log_error "Failed to create namespace: $ns"
                return 1
            fi
            log_success "Created namespace: $ns"
        fi
    fi

    return 0
}

apply_manifest_file() {
    local file="$1"
    local ns="${2:-}"

    if [[ ! -f "$file" ]]; then
        log_error "Manifest file not found: $file"
        return 1
    fi

    log_info "Applying manifest: $file"

    # Validate manifest first
    log_verbose "Validating manifest syntax..."
    if ! kubectl apply -f "$file" --dry-run=client -o yaml > /dev/null 2>&1; then
        log_error "Manifest validation failed: $file"
        kubectl apply -f "$file" --dry-run=client 2>&1 | head -20
        return 1
    fi

    # Build kubectl apply command
    local kubectl_args=(apply -f "$file")

    if [[ -n "$ns" ]]; then
        kubectl_args+=(-n "$ns")
    fi

    if [[ "$FORCE" == "true" ]]; then
        kubectl_args+=(--overwrite=true)
    fi

    # Apply the manifest
    if run_kubectl "${kubectl_args[@]}" > /dev/null; then
        log_success "Applied: $file"

        # Show applied resources
        log_verbose "Resources applied:"
        if [[ "$DRY_RUN" != "true" ]]; then
            kubectl apply -f "$file" ${ns:+-n "$ns"} -o wide 2>/dev/null | tail -n +2 | sed 's/^/  /'
        fi

        return 0
    else
        log_error "Failed to apply: $file"
        return 1
    fi
}

apply_manifest_directory() {
    local dir="$1"
    local ns="${2:-}"

    if [[ ! -d "$dir" ]]; then
        log_error "Directory not found: $dir"
        return 1
    fi

    log_info "Applying manifests from: $dir"

    local total=0
    local applied=0
    local failed=0

    # Process all YAML files
    while IFS= read -r -d '' file; do
        total=$((total + 1))

        if apply_manifest_file "$file" "$ns"; then
            applied=$((applied + 1))
        else
            failed=$((failed + 1))
        fi
    done < <(find "$dir" -type f \( -name "*.yaml" -o -name "*.yml" \) -print0 | sort -z)

    log_info "Summary:"
    log_info "  Total files: $total"
    log_success "  Applied: $applied"
    [[ $failed -gt 0 ]] && log_error "  Failed: $failed"

    if [[ $failed -gt 0 ]]; then
        return 1
    fi

    return 0
}

get_resource_kind_and_name() {
    local file="$1"
    local kind
    local name

    kind=$(kubectl apply -f "$file" --dry-run=client -o jsonpath='{.kind}' 2>/dev/null || echo "")
    name=$(kubectl apply -f "$file" --dry-run=client -o jsonpath='{.metadata.name}' 2>/dev/null || echo "")

    echo "$kind:$name"
}

wait_for_resources() {
    local file="$1"
    local ns="${2:-default}"
    local timeout=300
    local elapsed=0
    local check_interval=5

    log_info "Waiting for resources to be ready (timeout: ${timeout}s)..."

    # Try to wait for deployments
    if kubectl wait --for=condition=available --timeout=${timeout}s deployment --all -n "$ns" 2>/dev/null; then
        log_success "All deployments are ready"
        return 0
    fi

    # Try to wait for statefulsets
    if kubectl wait --for=condition=Ready pod --all -n "$ns" --timeout=${timeout}s 2>/dev/null; then
        log_success "All pods are ready"
        return 0
    fi

    log_warning "Timeout waiting for resources to be ready"
    return 0  # Don't fail on timeout
}

show_resource_status() {
    local file="$1"
    local ns="${2:-default}"

    log_info "Resource status:"

    if [[ "$DRY_RUN" != "true" ]]; then
        kubectl get all -f "$file" -n "$ns" -o wide 2>/dev/null || true
    fi
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
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --wait)
                WAIT_FOR_READY=true
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

    log_info "Kubernetes Manifest Apply"
    log_verbose "Dry run: $DRY_RUN"
    log_verbose "Namespace: ${NAMESPACE:-default}"
    log_verbose "Wait for ready: $WAIT_FOR_READY"

    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi

    # Check cluster connection
    if [[ "$DRY_RUN" != "true" ]]; then
        if ! check_cluster_connection; then
            exit 1
        fi
    fi

    # Ensure namespace exists
    if ! ensure_namespace_exists "${NAMESPACE:-default}"; then
        exit 1
    fi

    # Apply manifests
    if [[ -n "$MANIFEST_FILE" ]]; then
        if ! apply_manifest_file "$MANIFEST_FILE" "$NAMESPACE"; then
            exit 1
        fi

        if [[ "$WAIT_FOR_READY" == "true" ]]; then
            wait_for_resources "$MANIFEST_FILE" "${NAMESPACE:-default}"
        fi

        show_resource_status "$MANIFEST_FILE" "${NAMESPACE:-default}"
    fi

    if [[ -n "$MANIFEST_DIR" ]]; then
        if ! apply_manifest_directory "$MANIFEST_DIR" "$NAMESPACE"; then
            exit 1
        fi

        if [[ "$WAIT_FOR_READY" == "true" ]]; then
            wait_for_resources "$MANIFEST_DIR" "${NAMESPACE:-default}"
        fi
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "This was a dry run - no changes were applied"
    fi

    log_success "Manifest apply completed"
    exit 0
}

main "$@"
