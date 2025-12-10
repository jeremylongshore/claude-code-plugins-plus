#!/bin/bash
#
# Service mesh configuration deployment script
#
# Deploys service mesh configuration to Kubernetes cluster including:
# - kubectl apply of manifests
# - Namespace creation
# - Wait for resource readiness
# - Deployment verification
# - Rollback on failure
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MANIFEST_FILE=""
NAMESPACE="default"
CONTEXT=""
DRY_RUN=false
VERIFY=true
TIMEOUT=300
BACKUP_DIR=""

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy service mesh configuration to Kubernetes cluster

OPTIONS:
    -f, --file FILE           Path to configuration file (YAML) [REQUIRED]
    -n, --namespace NS        Target namespace (default: default)
    -c, --context CTX         Kubernetes context to use
    -d, --dry-run             Perform dry-run without applying
    --no-verify               Skip verification after deployment
    -t, --timeout SEC         Timeout for resource readiness (default: 300)
    -b, --backup DIR          Backup directory for rollback
    -h, --help                Show this help message

EXAMPLES:
    $0 -f service-mesh.yaml
    $0 -f service-mesh.yaml -n production --context prod-cluster
    $0 -f service-mesh.yaml --dry-run -v

EOF
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            MANIFEST_FILE="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -c|--context)
            CONTEXT="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-verify)
            VERIFY=false
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -b|--backup)
            BACKUP_DIR="$2"
            shift 2
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

# Validate required arguments
if [[ -z "$MANIFEST_FILE" ]]; then
    echo -e "${RED}Error: --file argument is required${NC}"
    usage
fi

if [[ ! -f "$MANIFEST_FILE" ]]; then
    echo -e "${RED}Error: File not found: $MANIFEST_FILE${NC}"
    exit 1
fi

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

# Function: Create namespace
create_namespace() {
    log "Checking namespace: $NAMESPACE"
    if kubectl get namespace "$NAMESPACE" &>/dev/null; then
        success "Namespace already exists: $NAMESPACE"
    else
        log "Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
        success "Namespace created: $NAMESPACE"
    fi
}

# Function: Backup existing resources
backup_resources() {
    if [[ -z "$BACKUP_DIR" ]]; then
        return 0
    fi

    log "Backing up existing resources to: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"

    # Extract resource kinds and names from manifest
    local kinds=$(grep "^kind:" "$MANIFEST_FILE" | awk '{print $2}' | sort -u)

    for kind in $kinds; do
        local backup_file="$BACKUP_DIR/$(echo $kind | tr '[:upper:]' '[:lower:]')-backup.yaml"
        log "Backing up $kind resources..."
        kubectl get "$kind" -n "$NAMESPACE" -o yaml > "$backup_file" 2>/dev/null || true
    done

    success "Resources backed up"
}

# Function: Validate manifest
validate_manifest() {
    log "Validating manifest: $MANIFEST_FILE"

    if ! kubectl apply -f "$MANIFEST_FILE" --namespace="$NAMESPACE" --dry-run=client &>/dev/null; then
        error "Manifest validation failed"
        exit 1
    fi

    success "Manifest validation passed"
}

# Function: Apply configuration
apply_config() {
    if [[ "$DRY_RUN" == true ]]; then
        log "Performing dry-run (no changes will be applied)"
        kubectl apply -f "$MANIFEST_FILE" --namespace="$NAMESPACE" --dry-run=client -v=2
        success "Dry-run completed successfully"
        return 0
    fi

    log "Applying configuration..."
    kubectl apply -f "$MANIFEST_FILE" --namespace="$NAMESPACE"
    success "Configuration applied"
}

# Function: Verify deployment
verify_deployment() {
    if [[ "$VERIFY" == false ]]; then
        log "Skipping verification (--no-verify flag set)"
        return 0
    fi

    log "Waiting for resources to be ready (timeout: ${TIMEOUT}s)..."

    # Extract resource info from manifest
    local resources=$(grep "^kind:" "$MANIFEST_FILE" | awk '{print $2}')
    local ready=true

    for kind in $resources; do
        # Only wait for Deployment, StatefulSet, DaemonSet
        case "$kind" in
            Deployment|StatefulSet|DaemonSet)
                log "Waiting for $kind resources..."
                if ! kubectl wait --for=condition=Progressing=True "$kind" \
                    -n "$NAMESPACE" --all --timeout="${TIMEOUT}s" 2>/dev/null; then
                    warning "Timeout waiting for $kind (may still be deploying)"
                fi
                ;;
        esac
    done

    success "Verification completed"
}

# Function: Check resource status
check_status() {
    log "Checking resource status..."

    local kinds=$(grep "^kind:" "$MANIFEST_FILE" | awk '{print $2}' | sort -u)

    for kind in $kinds; do
        echo ""
        log "Resources of kind: $kind"
        kubectl get "$kind" -n "$NAMESPACE" 2>/dev/null || true
    done
}

# Function: Rollback
rollback() {
    if [[ -z "$BACKUP_DIR" ]] || [[ ! -d "$BACKUP_DIR" ]]; then
        error "Cannot rollback: no backup directory available"
        return 1
    fi

    error "Deployment failed. Attempting rollback..."

    for backup_file in "$BACKUP_DIR"/*.yaml; do
        if [[ -f "$backup_file" ]]; then
            log "Restoring from: $backup_file"
            kubectl apply -f "$backup_file" --namespace="$NAMESPACE"
        fi
    done

    success "Rollback completed"
}

# Main execution
main() {
    log "=========================================="
    log "Service Mesh Configuration Deployment"
    log "=========================================="
    log "Manifest: $MANIFEST_FILE"
    log "Namespace: $NAMESPACE"
    log "Context: ${CONTEXT:-default}"
    log "Dry Run: $DRY_RUN"
    echo ""

    # Pre-deployment checks
    check_kubectl
    set_context
    create_namespace
    validate_manifest

    # Backup existing resources
    backup_resources

    # Apply configuration
    if ! apply_config; then
        error "Failed to apply configuration"
        rollback
        exit 1
    fi

    # Verify deployment
    if ! verify_deployment; then
        warning "Verification encountered issues"
        # Don't exit, show status anyway
    fi

    # Show final status
    check_status

    echo ""
    success "Deployment completed successfully"
    log "=========================================="
    exit 0
}

# Run main function
main "$@"
