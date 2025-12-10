#!/bin/bash
#
# Service mesh configuration rollback script
#
# Rolls back service mesh configuration to previous version including:
# - Kubernetes rollout undo for deployments
# - Custom resource version restoration
# - Health check verification
# - Rollback confirmation
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="default"
CONTEXT=""
RESOURCE_KIND=""
RESOURCE_NAME=""
REVISION=""
BACKUP_FILE=""
CONFIRM=false

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Rollback service mesh configuration to previous version

OPTIONS:
    -n, --namespace NS        Target namespace (default: default)
    -c, --context CTX         Kubernetes context to use
    -k, --kind KIND           Resource kind (Deployment, StatefulSet, etc.)
    -r, --resource NAME       Resource name to rollback
    -v, --revision NUM        Revision number to rollback to
    -b, --backup FILE         Backup file to restore from
    -y, --yes                 Skip confirmation prompt
    -h, --help                Show this help message

EXAMPLES:
    $0 -k Deployment -r my-service -n production
    $0 -b backup/deployment-backup.yaml
    $0 --kind StatefulSet --resource mesh-controller -v 2 --yes

EOF
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -c|--context)
            CONTEXT="$2"
            shift 2
            ;;
        -k|--kind)
            RESOURCE_KIND="$2"
            shift 2
            ;;
        -r|--resource)
            RESOURCE_NAME="$2"
            shift 2
            ;;
        -v|--revision)
            REVISION="$2"
            shift 2
            ;;
        -b|--backup)
            BACKUP_FILE="$2"
            shift 2
            ;;
        -y|--yes)
            CONFIRM=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Function: Log message
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Function: Success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function: Error message
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function: Warning message
warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function: Confirmation prompt
confirm() {
    local prompt="$1"
    local response

    if [[ "$CONFIRM" == true ]]; then
        return 0
    fi

    echo -ne "${YELLOW}${prompt} (yes/no): ${NC}"
    read -r response
    [[ "$response" == "yes" || "$response" == "y" ]]
}

# Function: Check kubectl
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        error "kubectl not found in PATH"
        exit 1
    fi
    success "kubectl found: $(kubectl version --client --short)"
}

# Function: Set context
set_context() {
    if [[ -n "$CONTEXT" ]]; then
        log "Setting Kubernetes context to: $CONTEXT"
        if kubectl config use-context "$CONTEXT" &>/dev/null; then
            success "Context set to: $CONTEXT"
        else
            error "Failed to set context: $CONTEXT"
            exit 1
        fi
    fi
}

# Function: Rollback deployment using kubectl rollout
rollback_deployment() {
    if [[ -z "$RESOURCE_KIND" ]] || [[ -z "$RESOURCE_NAME" ]]; then
        error "Resource kind and name required for rollout rollback"
        exit 1
    fi

    log "Checking rollout history for: $RESOURCE_KIND/$RESOURCE_NAME"

    # Get history
    if ! kubectl rollout history "$RESOURCE_KIND" "$RESOURCE_NAME" \
        -n "$NAMESPACE" &>/dev/null; then
        error "No rollout history available for $RESOURCE_KIND/$RESOURCE_NAME"
        exit 1
    fi

    # Display history
    echo ""
    echo "Rollout History:"
    kubectl rollout history "$RESOURCE_KIND" "$RESOURCE_NAME" \
        -n "$NAMESPACE"
    echo ""

    # Determine revision
    if [[ -z "$REVISION" ]]; then
        # Get previous revision
        REVISION=$(kubectl rollout history "$RESOURCE_KIND" "$RESOURCE_NAME" \
            -n "$NAMESPACE" | tail -2 | head -1 | awk '{print $1}')
    fi

    if [[ -z "$REVISION" ]]; then
        error "Could not determine revision to rollback to"
        exit 1
    fi

    # Confirm rollback
    if ! confirm "Rollback $RESOURCE_KIND/$RESOURCE_NAME to revision $REVISION?"; then
        error "Rollback cancelled"
        exit 1
    fi

    # Perform rollback
    log "Rolling back to revision: $REVISION"
    if kubectl rollout undo "$RESOURCE_KIND" "$RESOURCE_NAME" \
        --to-revision="$REVISION" -n "$NAMESPACE"; then
        success "Rollback initiated for $RESOURCE_KIND/$RESOURCE_NAME"
    else
        error "Failed to rollback $RESOURCE_KIND/$RESOURCE_NAME"
        exit 1
    fi

    # Wait for rollback to complete
    log "Waiting for rollback to complete..."
    if kubectl rollout status "$RESOURCE_KIND" "$RESOURCE_NAME" \
        -n "$NAMESPACE" --timeout=300s; then
        success "Rollback completed successfully"
    else
        warning "Rollback may still be in progress"
    fi
}

# Function: Restore from backup file
restore_backup() {
    if [[ -z "$BACKUP_FILE" ]]; then
        error "Backup file not specified"
        exit 1
    fi

    if [[ ! -f "$BACKUP_FILE" ]]; then
        error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi

    log "Restoring from backup: $BACKUP_FILE"

    # Confirm restoration
    if ! confirm "Restore from backup file?"; then
        error "Restoration cancelled"
        exit 1
    fi

    # Apply backup
    if kubectl apply -f "$BACKUP_FILE" --namespace="$NAMESPACE"; then
        success "Backup restored successfully"
    else
        error "Failed to restore backup"
        exit 1
    fi

    # Verify resources are running
    log "Verifying restored resources..."
    sleep 5

    local kinds=$(grep "^kind:" "$BACKUP_FILE" 2>/dev/null | awk '{print $2}' | sort -u)
    for kind in $kinds; do
        kubectl get "$kind" -n "$NAMESPACE" 2>/dev/null || true
    done
}

# Function: Get previous configuration
get_previous_config() {
    if [[ -z "$RESOURCE_KIND" ]] || [[ -z "$RESOURCE_NAME" ]]; then
        error "Resource kind and name required"
        exit 1
    fi

    log "Retrieving previous configuration for: $RESOURCE_KIND/$RESOURCE_NAME"

    # Get previous revision info
    local prev_revision=$(kubectl rollout history "$RESOURCE_KIND" "$RESOURCE_NAME" \
        -n "$NAMESPACE" | tail -2 | head -1 | awk '{print $1}')

    if [[ -z "$prev_revision" ]]; then
        error "No previous revision found"
        exit 1
    fi

    log "Previous revision: $prev_revision"
    log "Previous image: $(kubectl rollout history "$RESOURCE_KIND" \
        "$RESOURCE_NAME" -n "$NAMESPACE" --revision="$prev_revision" || echo 'N/A')"
}

# Function: Check health after rollback
check_health() {
    log "Checking health of rolled-back resources..."

    echo ""
    echo "Pod Status:"
    kubectl get pods -n "$NAMESPACE" -o wide

    echo ""
    echo "Service Status:"
    kubectl get svc -n "$NAMESPACE"

    echo ""
    echo "Events (last 10):"
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10
}

# Function: Get comparison with current
compare_versions() {
    if [[ -z "$RESOURCE_KIND" ]] || [[ -z "$RESOURCE_NAME" ]]; then
        return 0
    fi

    log "Current version:"
    kubectl describe "$RESOURCE_KIND" "$RESOURCE_NAME" -n "$NAMESPACE" | grep -E "Image:|Replicas:" || true
}

# Main execution
main() {
    log "=========================================="
    log "Service Mesh Configuration Rollback"
    log "=========================================="
    log "Namespace: $NAMESPACE"
    log "Context: ${CONTEXT:-default}"
    echo ""

    # Pre-rollback checks
    check_kubectl
    set_context

    # Perform rollback
    if [[ -n "$BACKUP_FILE" ]]; then
        restore_backup
    elif [[ -n "$RESOURCE_KIND" && -n "$RESOURCE_NAME" ]]; then
        rollback_deployment
    else
        error "Either --backup or both --kind and --resource must be specified"
        usage
    fi

    # Get version comparison
    compare_versions

    # Check health
    check_health

    echo ""
    success "Rollback process completed"
    log "=========================================="
    exit 0
}

# Run main function
main "$@"
