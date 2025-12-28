#!/bin/bash

###############################################################################
# get_resource_status.sh
#
# Retrieves the status of Kubernetes resources
#
# Usage:
#   ./get_resource_status.sh --resource deployment --name my-app
#   ./get_resource_status.sh --resource pod --namespace prod
#   ./get_resource_status.sh --all --namespace default
#
# Exit Codes:
#   0 - Status retrieved successfully
#   1 - Status retrieval failed
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
RESOURCE_TYPE=""
RESOURCE_NAME=""
NAMESPACE="default"
SHOW_ALL=false
SHOW_DETAILS=false
WATCH_MODE=false
OUTPUT_FORMAT="wide"
VERBOSE=false

###############################################################################
# Functions
###############################################################################

show_help() {
    cat << EOF
Retrieve the status of Kubernetes resources

Usage: $(basename "$0") [OPTIONS]

Options:
    -r, --resource TYPE     Resource type (e.g., deployment, pod, service)
    -n, --name NAME         Resource name
    --namespace NS          Kubernetes namespace (default: default)
    --all                   Show all resources in namespace
    -d, --details           Show detailed information
    -w, --watch             Watch resource status in real-time
    -f, --format FORMAT     Output format: wide, json, yaml (default: wide)
    -v, --verbose           Enable verbose output
    -h, --help              Show this help message

Examples:
    $(basename "$0") --resource deployment --name my-app
    $(basename "$0") --resource pod --namespace production
    $(basename "$0") --all --namespace default
    $(basename "$0") --resource deployment --name my-app --watch
    $(basename "$0") --resource pod --details --format json

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

check_namespace_exists() {
    local ns="$1"

    if ! kubectl get namespace "$ns" &> /dev/null; then
        log_warning "Namespace does not exist: $ns"
        return 1
    fi

    return 0
}

check_resource_exists() {
    local resource_type="$1"
    local resource_name="$2"
    local ns="$3"

    if ! kubectl get "$resource_type" "$resource_name" -n "$ns" &> /dev/null; then
        return 1
    fi

    return 0
}

get_resource_status() {
    local resource_type="$1"
    local resource_name="$2"
    local ns="$3"

    log_info "Resource: $resource_type/$resource_name"
    log_info "Namespace: $ns"
    log_info ""

    # Build kubectl command
    local kubectl_args=(get "$resource_type" "$resource_name" -n "$ns")

    if [[ "$OUTPUT_FORMAT" != "wide" ]]; then
        kubectl_args+=(-o "$OUTPUT_FORMAT")
    else
        kubectl_args+=(-o wide)
    fi

    kubectl "${kubectl_args[@]}"
}

get_all_resources_status() {
    local ns="$1"

    log_info "All resources in namespace: $ns"
    log_info ""

    kubectl get all -n "$ns" -o "$OUTPUT_FORMAT"
}

show_resource_details() {
    local resource_type="$1"
    local resource_name="$2"
    local ns="$3"

    log_info ""
    log_info "Detailed Information:"
    log_info "======================="

    # Get basic info
    log_info ""
    log_info "Resource Definition:"
    kubectl get "$resource_type" "$resource_name" -n "$ns" -o yaml | head -30

    # Show related events
    log_info ""
    log_info "Recent Events:"
    kubectl get events -n "$ns" --field-selector involvedObject.name="$resource_name" \
        --sort-by='.lastTimestamp' | tail -10 || log_warning "No recent events found"

    # Show resource-specific status
    case "$resource_type" in
        deployment)
            show_deployment_details "$resource_name" "$ns"
            ;;
        pod)
            show_pod_details "$resource_name" "$ns"
            ;;
        service)
            show_service_details "$resource_name" "$ns"
            ;;
        statefulset)
            show_statefulset_details "$resource_name" "$ns"
            ;;
    esac
}

show_deployment_details() {
    local name="$1"
    local ns="$2"

    log_info ""
    log_info "Deployment Status:"

    # Get replicas info
    kubectl get deployment "$name" -n "$ns" -o jsonpath='{
        .spec.replicas} replicas desired
  {.status.replicas} replicas current
  {.status.updatedReplicas} updated
  {.status.readyReplicas} ready
  {.status.availableReplicas} available' 2>/dev/null || true

    echo ""

    # Get pod status
    log_info "Associated Pods:"
    kubectl get pods -n "$ns" -l "app=$(kubectl get deployment "$name" -n "$ns" -o jsonpath='{.spec.selector.matchLabels.app}')" \
        -o wide 2>/dev/null || true
}

show_pod_details() {
    local name="$1"
    local ns="$2"

    log_info ""
    log_info "Pod Status:"

    # Get pod phase
    local phase
    phase=$(kubectl get pod "$name" -n "$ns" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")

    log_info "  Phase: $phase"

    # Get container status
    log_info "  Containers:"
    kubectl get pod "$name" -n "$ns" -o jsonpath='{.status.containerStatuses[*].name}' 2>/dev/null || true
    echo ""

    # Get pod logs if available
    log_info ""
    log_info "Recent Logs (last 20 lines):"
    kubectl logs "$name" -n "$ns" --tail=20 2>/dev/null || log_warning "Cannot retrieve logs"
}

show_service_details() {
    local name="$1"
    local ns="$2"

    log_info ""
    log_info "Service Endpoints:"

    kubectl get endpoints "$name" -n "$ns" -o wide 2>/dev/null || log_warning "No endpoints found"

    # Get service details
    log_info ""
    log_info "Service Ports:"
    kubectl get service "$name" -n "$ns" -o jsonpath='{.spec.ports[*]}' 2>/dev/null || true
    echo ""
}

show_statefulset_details() {
    local name="$1"
    local ns="$2"

    log_info ""
    log_info "StatefulSet Status:"

    # Get replica info
    kubectl get statefulset "$name" -n "$ns" -o jsonpath='{
        .spec.replicas} replicas desired
  {.status.replicas} replicas current
  {.status.readyReplicas} ready' 2>/dev/null || true

    echo ""

    # Get associated pods
    log_info "Associated Pods:"
    kubectl get pods -n "$ns" -l "app=$(kubectl get statefulset "$name" -n "$ns" -o jsonpath='{.spec.selector.matchLabels.app}')" \
        -o wide 2>/dev/null || true
}

watch_resource_status() {
    local resource_type="$1"
    local resource_name="$2"
    local ns="$3"

    log_info "Watching $resource_type/$resource_name in namespace $ns"
    log_info "Press Ctrl+C to stop watching"
    log_info ""

    # Use kubectl watch
    kubectl get "$resource_type" "$resource_name" -n "$ns" -o "$OUTPUT_FORMAT" --watch
}

show_status_summary() {
    local ns="$1"

    log_info ""
    log_info "Status Summary for namespace: $ns"
    log_info "=================================="

    # Count resources by status
    local deployments
    local pods
    local running_pods
    local failed_pods

    deployments=$(kubectl get deployment -n "$ns" -o json | jq '.items | length' 2>/dev/null || echo 0)
    pods=$(kubectl get pod -n "$ns" -o json | jq '.items | length' 2>/dev/null || echo 0)
    running_pods=$(kubectl get pod -n "$ns" -o json | jq '[.items[] | select(.status.phase=="Running")] | length' 2>/dev/null || echo 0)
    failed_pods=$(kubectl get pod -n "$ns" -o json | jq '[.items[] | select(.status.phase=="Failed")] | length' 2>/dev/null || echo 0)

    log_info "  Deployments: $deployments"
    log_info "  Pods: $pods (Running: $running_pods, Failed: $failed_pods)"

    # Show problematic resources
    if [[ $failed_pods -gt 0 ]]; then
        log_warning "Failed pods detected:"
        kubectl get pod -n "$ns" --field-selector=status.phase=Failed -o wide | tail -n +2 | sed 's/^/    /'
    fi
}

###############################################################################
# Main
###############################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
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
                SHOW_ALL=true
                shift
                ;;
            -d|--details)
                SHOW_DETAILS=true
                shift
                ;;
            -w|--watch)
                WATCH_MODE=true
                shift
                ;;
            -f|--format)
                OUTPUT_FORMAT="$2"
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

    # Validate arguments
    if [[ "$SHOW_ALL" != "true" ]] && [[ -z "$RESOURCE_TYPE" ]]; then
        log_error "Either --resource or --all is required"
        echo "Use --help for usage information"
        exit 2
    fi

    if [[ "$SHOW_ALL" != "true" ]] && [[ -z "$RESOURCE_NAME" ]]; then
        log_error "Resource name is required when specifying resource type"
        echo "Use --help for usage information"
        exit 2
    fi

    log_verbose "Namespace: $NAMESPACE"
    log_verbose "Format: $OUTPUT_FORMAT"

    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi

    # Check cluster connection
    if ! check_cluster_connection; then
        exit 1
    fi

    # Check namespace exists
    if ! check_namespace_exists "$NAMESPACE"; then
        exit 1
    fi

    # Get status
    if [[ "$SHOW_ALL" == "true" ]]; then
        get_all_resources_status "$NAMESPACE"
        show_status_summary "$NAMESPACE"
    else
        # Check resource exists
        if ! check_resource_exists "$RESOURCE_TYPE" "$RESOURCE_NAME" "$NAMESPACE"; then
            log_error "Resource not found: $RESOURCE_TYPE/$RESOURCE_NAME in namespace $NAMESPACE"
            exit 1
        fi

        # Get status
        if [[ "$WATCH_MODE" == "true" ]]; then
            watch_resource_status "$RESOURCE_TYPE" "$RESOURCE_NAME" "$NAMESPACE"
        else
            get_resource_status "$RESOURCE_TYPE" "$RESOURCE_NAME" "$NAMESPACE"

            # Show details if requested
            if [[ "$SHOW_DETAILS" == "true" ]]; then
                show_resource_details "$RESOURCE_TYPE" "$RESOURCE_NAME" "$NAMESPACE"
            fi
        fi
    fi

    log_success "Status retrieved successfully"
    exit 0
}

main "$@"
