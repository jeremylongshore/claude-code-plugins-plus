#!/bin/bash

###############################################################################
# delete_manifest.sh
#
# Deletes Kubernetes resources from the cluster
#
# Usage:
#   ./delete_manifest.sh --file deployment.yaml
#   ./delete_manifest.sh --resource deployment my-app
#   ./delete_manifest.sh --all --namespace production
#
# Exit Codes:
#   0 - Delete successful
#   1 - Delete failed
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
RESOURCE_TYPE=""
RESOURCE_NAME=""
NAMESPACE=""
DELETE_ALL=false
GRACE_PERIOD=30
WAIT=false
VERBOSE=false
CONFIRM=true

###############################################################################
# Functions
###############################################################################

show_help() {
    cat << EOF
Delete Kubernetes resources from the cluster

Usage: $(basename "$0") [OPTIONS]

Options:
    -f, --file FILE         Delete resources defined in manifest file
    -r, --resource TYPE     Resource type (e.g., deployment, pod, service)
    -n, --name NAME         Resource name
    --namespace NS          Kubernetes namespace (default: default)
    --all                   Delete all resources in namespace
    --grace-period SECS     Grace period for shutdown (default: 30)
    --wait                  Wait for deletion to complete
    --force                 Force delete without confirmation
    -v, --verbose           Enable verbose output
    -h, --help              Show this help message

Examples:
    $(basename "$0") --file deployment.yaml
    $(basename "$0") --resource deployment --name my-app
    $(basename "$0") --all --namespace production --wait
    $(basename "$0") --resource pod --name pod-name --grace-period 0

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

prompt_confirmation() {
    local message="$1"
    local response

    echo -n "$(log_warning "$message (y/N): ")" >&2
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
    fi
    return 1
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
    log_verbose "Checking cluster connection..."

    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        return 1
    fi

    return 0
}

get_resources_to_delete() {
    local file="$1"
    local ns="${2:-default}"

    # Get resources from manifest
    kubectl get -f "$file" -n "$ns" -o custom-columns=KIND:.kind,NAME:.metadata.name --no-headers 2>/dev/null || true
}

delete_by_manifest_file() {
    local file="$1"
    local ns="${2:-default}"

    if [[ ! -f "$file" ]]; then
        log_error "Manifest file not found: $file"
        return 1
    fi

    log_info "Resources to delete from: $file"

    # Show resources that will be deleted
    log_info "Listing resources:"
    get_resources_to_delete "$file" "$ns" | sed 's/^/  /'

    # Confirm deletion
    if [[ "$CONFIRM" == "true" ]]; then
        if ! prompt_confirmation "Are you sure you want to delete these resources?"; then
            log_warning "Deletion cancelled"
            return 0
        fi
    fi

    # Delete resources
    log_info "Deleting resources from: $file"

    local kubectl_args=(delete -f "$file" -n "$ns" --grace-period="$GRACE_PERIOD")

    if [[ "$WAIT" == "true" ]]; then
        kubectl_args+=(--wait=true)
    fi

    if kubectl "${kubectl_args[@]}"; then
        log_success "Successfully deleted resources"
        return 0
    else
        log_error "Failed to delete resources"
        return 1
    fi
}

delete_by_resource() {
    local resource_type="$1"
    local resource_name="$2"
    local ns="${3:-default}"

    log_info "Deleting $resource_type: $resource_name (namespace: $ns)"

    # Check if resource exists
    if ! kubectl get "$resource_type" "$resource_name" -n "$ns" &> /dev/null; then
        log_warning "Resource not found: $resource_type/$resource_name in namespace $ns"
        return 0
    fi

    log_info "Resource details:"
    kubectl get "$resource_type" "$resource_name" -n "$ns" -o wide | sed 's/^/  /'

    # Confirm deletion
    if [[ "$CONFIRM" == "true" ]]; then
        if ! prompt_confirmation "Are you sure you want to delete $resource_type/$resource_name?"; then
            log_warning "Deletion cancelled"
            return 0
        fi
    fi

    # Delete resource
    local kubectl_args=(delete "$resource_type" "$resource_name" -n "$ns" --grace-period="$GRACE_PERIOD")

    if [[ "$WAIT" == "true" ]]; then
        kubectl_args+=(--wait=true)
    fi

    if kubectl "${kubectl_args[@]}"; then
        log_success "Successfully deleted $resource_type: $resource_name"
        return 0
    else
        log_error "Failed to delete $resource_type: $resource_name"
        return 1
    fi
}

delete_all_in_namespace() {
    local ns="$1"

    log_warning "Preparing to delete ALL resources in namespace: $ns"

    # List resources
    log_info "Resources in namespace:"
    kubectl get all -n "$ns" -o wide | sed 's/^/  /'

    # Confirm deletion
    if [[ "$CONFIRM" == "true" ]]; then
        if ! prompt_confirmation "Are you ABSOLUTELY SURE you want to delete ALL resources in namespace $ns?"; then
            log_warning "Deletion cancelled"
            return 0
        fi
    fi

    # Delete all resources
    log_info "Deleting all resources in namespace: $ns"

    # Delete in a specific order to avoid dependency issues
    local resources=(
        "deployment"
        "statefulset"
        "daemonset"
        "job"
        "pod"
        "service"
        "configmap"
        "secret"
        "persistentvolumeclaim"
    )

    for resource in "${resources[@]}"; do
        local count
        count=$(kubectl get "$resource" -n "$ns" -o json | jq '.items | length' 2>/dev/null || echo 0)

        if [[ $count -gt 0 ]]; then
            log_info "Deleting $count $resource(s)..."

            kubectl delete "$resource" --all -n "$ns" --grace-period="$GRACE_PERIOD" 2>/dev/null || true
        fi
    done

    log_success "Deletion request sent for all resources in namespace: $ns"
    return 0
}

verify_deletion() {
    local ns="${1:-default}"
    local max_attempts=30
    local attempt=0

    if [[ "$WAIT" != "true" ]]; then
        return 0
    fi

    log_info "Verifying deletion (timeout: 30s)..."

    while [[ $attempt -lt $max_attempts ]]; do
        local resource_count
        resource_count=$(kubectl get pod -n "$ns" -o json 2>/dev/null | jq '.items | length' || echo 0)

        if [[ $resource_count -eq 0 ]]; then
            log_success "All resources deleted"
            return 0
        fi

        log_verbose "Still waiting for deletion... (pods remaining: $resource_count)"
        sleep 1
        attempt=$((attempt + 1))
    done

    log_warning "Timeout waiting for resources to be deleted"
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
            -r|--resource)
                RESOURCE_TYPE="$2"
                shift 2
                ;;
            -n|--name)
                RESOURCE_NAME="$2"
                shift 2
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --all)
                DELETE_ALL=true
                shift
                ;;
            --grace-period)
                GRACE_PERIOD="$2"
                shift 2
                ;;
            --wait)
                WAIT=true
                shift
                ;;
            --force)
                CONFIRM=false
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
    if [[ "$DELETE_ALL" != "true" ]] && [[ -z "$MANIFEST_FILE" ]] && [[ -z "$RESOURCE_TYPE" ]]; then
        log_error "Either --file, --resource, or --all is required"
        echo "Use --help for usage information"
        exit 2
    fi

    if [[ -z "$NAMESPACE" ]]; then
        NAMESPACE="default"
    fi

    log_info "Kubernetes Resource Delete"
    log_verbose "Namespace: $NAMESPACE"
    log_verbose "Grace period: $GRACE_PERIOD seconds"
    log_verbose "Wait for deletion: $WAIT"

    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi

    # Check cluster connection
    if ! check_cluster_connection; then
        exit 1
    fi

    # Perform deletion
    if [[ -n "$MANIFEST_FILE" ]]; then
        if ! delete_by_manifest_file "$MANIFEST_FILE" "$NAMESPACE"; then
            exit 1
        fi
        verify_deletion "$NAMESPACE"
    fi

    if [[ -n "$RESOURCE_TYPE" ]]; then
        if [[ -z "$RESOURCE_NAME" ]]; then
            log_error "Resource name is required when specifying resource type"
            exit 2
        fi

        if ! delete_by_resource "$RESOURCE_TYPE" "$RESOURCE_NAME" "$NAMESPACE"; then
            exit 1
        fi
        verify_deletion "$NAMESPACE"
    fi

    if [[ "$DELETE_ALL" == "true" ]]; then
        if ! delete_all_in_namespace "$NAMESPACE"; then
            exit 1
        fi
        verify_deletion "$NAMESPACE"
    fi

    log_success "Resource deletion completed"
    exit 0
}

main "$@"
