#!/bin/bash

###############################################################################
# deploy.sh
#
# Deploy Docker Compose file to Docker Swarm or Kubernetes cluster
#
# Usage:
#   ./deploy.sh --compose docker-compose.yml --target swarm
#   ./deploy.sh --compose docker-compose.yml --target kubernetes --namespace prod
#   ./deploy.sh --compose docker-compose.yml --target docker
#
# Exit Codes:
#   0 - Deployment successful
#   1 - Deployment failed
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
COMPOSE_FILE=""
TARGET_PLATFORM=""
NAMESPACE="default"
STACK_NAME=""
DRY_RUN=false
VERBOSE=false
WAIT_FOR_READY=false

###############################################################################
# Functions
###############################################################################

show_help() {
    cat << EOF
Deploy Docker Compose files to Docker Swarm or Kubernetes

Usage: $(basename "$0") [OPTIONS]

Options:
    -c, --compose FILE       Path to Docker Compose file (required)
    -t, --target PLATFORM    Target platform: docker, swarm, kubernetes (required)
    -n, --namespace NS       Kubernetes namespace (default: default)
    -s, --stack-name NAME    Stack name for Swarm deployment
    --dry-run               Show what would be deployed without executing
    --wait                  Wait for deployment to be ready
    -v, --verbose           Enable verbose output
    -h, --help              Show this help message

Examples:
    $(basename "$0") --compose docker-compose.yml --target docker
    $(basename "$0") --compose docker-compose.yml --target swarm --stack-name myapp
    $(basename "$0") --compose docker-compose.yml --target kubernetes --namespace production

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

log_step() {
    echo -e "${BLUE}>>>${NC} $*"
}

run_command() {
    local cmd="$*"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] $cmd"
        return 0
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Executing: $cmd"
    fi

    if eval "$cmd"; then
        return 0
    else
        return 1
    fi
}

check_dependencies() {
    local platform="$1"
    local missing_deps=0

    log_step "Checking dependencies..."

    case "$platform" in
        docker)
            if ! command -v docker &> /dev/null; then
                log_error "docker is not installed"
                missing_deps=$((missing_deps + 1))
            fi
            if ! command -v docker-compose &> /dev/null; then
                log_error "docker-compose is not installed"
                missing_deps=$((missing_deps + 1))
            fi
            ;;
        swarm)
            if ! command -v docker &> /dev/null; then
                log_error "docker is not installed"
                missing_deps=$((missing_deps + 1))
            fi
            if ! command -v docker-compose &> /dev/null; then
                log_error "docker-compose is not installed"
                missing_deps=$((missing_deps + 1))
            fi
            ;;
        kubernetes)
            if ! command -v kubectl &> /dev/null; then
                log_error "kubectl is not installed"
                missing_deps=$((missing_deps + 1))
            fi
            if ! command -v kompose &> /dev/null; then
                log_warning "kompose is not installed (required for docker-compose conversion)"
                log_info "Install with: curl -L https://github.com/kubernetes/kompose/releases/download/v1.28.0/kompose-linux-amd64 -o kompose"
                # Don't fail yet - might have manual manifests
            fi
            ;;
    esac

    if [[ $missing_deps -gt 0 ]]; then
        log_error "Missing $missing_deps required dependencies"
        return 1
    fi

    log_success "All dependencies available"
    return 0
}

validate_compose_file() {
    log_step "Validating Docker Compose file..."

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        return 1
    fi

    if ! docker-compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
        log_error "Compose file validation failed"
        docker-compose -f "$COMPOSE_FILE" config 2>&1 | head -20
        return 1
    fi

    log_success "Compose file is valid"
    return 0
}

deploy_docker() {
    log_step "Deploying to Docker (local)..."

    if ! run_command "docker-compose -f '$COMPOSE_FILE' up -d"; then
        log_error "Failed to start services"
        return 1
    fi

    log_success "Services started successfully"

    if [[ "$WAIT_FOR_READY" == "true" ]]; then
        sleep 5
        log_step "Checking service status..."
        docker-compose -f "$COMPOSE_FILE" ps
    fi

    return 0
}

deploy_swarm() {
    log_step "Deploying to Docker Swarm..."

    # Check if Swarm is initialized
    if ! docker info --format='{{.Swarm.LocalNodeState}}' | grep -q "active"; then
        log_error "Docker Swarm is not initialized"
        log_info "Initialize with: docker swarm init"
        return 1
    fi

    local stack_name="${STACK_NAME:-compose_app}"

    log_info "Stack name: $stack_name"

    if ! run_command "docker stack deploy -c '$COMPOSE_FILE' '$stack_name'"; then
        log_error "Failed to deploy stack"
        return 1
    fi

    log_success "Stack deployed: $stack_name"

    if [[ "$WAIT_FOR_READY" == "true" ]]; then
        log_step "Waiting for services to be ready..."
        local max_attempts=30
        local attempt=0

        while [[ $attempt -lt $max_attempts ]]; do
            local replicas
            replicas=$(docker stack services "$stack_name" | grep -v "Replicas" | awk '{sum += $3} END {print sum}')

            if [[ -n "$replicas" ]] && [[ "$replicas" -gt 0 ]]; then
                log_success "Services are ready (replicas: $replicas)"
                return 0
            fi

            attempt=$((attempt + 1))
            sleep 2
        done

        log_warning "Timeout waiting for services to be ready"
    fi

    return 0
}

deploy_kubernetes() {
    log_step "Deploying to Kubernetes..."

    # Check kubectl connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        log_info "Check kubeconfig: kubectl cluster-info"
        return 1
    fi

    # Check if kompose is available
    if ! command -v kompose &> /dev/null; then
        log_error "kompose is required to convert Docker Compose to Kubernetes"
        log_info "Install: curl -L https://github.com/kubernetes/kompose/releases/download/latest/kompose-linux-amd64 -o kompose"
        return 1
    fi

    # Create namespace if it doesn't exist
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_step "Creating namespace: $NAMESPACE"
        if ! run_command "kubectl create namespace '$NAMESPACE'"; then
            log_error "Failed to create namespace"
            return 1
        fi
    fi

    # Convert Docker Compose to Kubernetes manifests
    log_step "Converting Docker Compose to Kubernetes manifests..."
    local temp_dir
    temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT

    if ! kompose -f "$COMPOSE_FILE" convert -o "$temp_dir" 2>&1; then
        log_error "Failed to convert Docker Compose file"
        return 1
    fi

    # Apply manifests
    log_step "Applying Kubernetes manifests..."
    if ! run_command "kubectl apply -f '$temp_dir' -n '$NAMESPACE'"; then
        log_error "Failed to apply Kubernetes manifests"
        return 1
    fi

    log_success "Kubernetes deployment complete"

    if [[ "$WAIT_FOR_READY" == "true" ]]; then
        log_step "Waiting for deployments to be ready..."
        if run_command "kubectl wait --for=condition=available --timeout=300s deployment --all -n '$NAMESPACE'"; then
            log_success "All deployments are ready"
        else
            log_warning "Timeout waiting for deployments"
        fi
    fi

    # Show deployment status
    log_step "Deployment status:"
    kubectl get all -n "$NAMESPACE"

    return 0
}

show_deployment_status() {
    log_step "Current deployment status..."

    case "$TARGET_PLATFORM" in
        docker)
            docker-compose -f "$COMPOSE_FILE" ps
            ;;
        swarm)
            docker stack ls
            ;;
        kubernetes)
            kubectl get all -n "$NAMESPACE"
            ;;
    esac
}

###############################################################################
# Main
###############################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--compose)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            -t|--target)
                TARGET_PLATFORM="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -s|--stack-name)
                STACK_NAME="$2"
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

    if [[ -z "$TARGET_PLATFORM" ]]; then
        log_error "Target platform is required (docker, swarm, or kubernetes)"
        echo "Use --help for usage information"
        exit 2
    fi

    # Validate platform
    if ! [[ "$TARGET_PLATFORM" =~ ^(docker|swarm|kubernetes)$ ]]; then
        log_error "Invalid target platform: $TARGET_PLATFORM"
        echo "Valid options: docker, swarm, kubernetes"
        exit 2
    fi

    log_info "Deployment Configuration"
    log_info "  Compose file: $COMPOSE_FILE"
    log_info "  Target platform: $TARGET_PLATFORM"
    log_info "  Dry run: $DRY_RUN"
    log_info "  Verbose: $VERBOSE"
    [[ -n "$NAMESPACE" ]] && log_info "  Namespace: $NAMESPACE"
    [[ -n "$STACK_NAME" ]] && log_info "  Stack name: $STACK_NAME"

    # Check dependencies
    if ! check_dependencies "$TARGET_PLATFORM"; then
        exit 1
    fi

    # Validate compose file
    if ! validate_compose_file; then
        exit 1
    fi

    # Deploy based on target platform
    case "$TARGET_PLATFORM" in
        docker)
            if ! deploy_docker; then
                exit 1
            fi
            ;;
        swarm)
            if ! deploy_swarm; then
                exit 1
            fi
            ;;
        kubernetes)
            if ! deploy_kubernetes; then
                exit 1
            fi
            ;;
    esac

    show_deployment_status
    log_success "Deployment completed"
    exit 0
}

main "$@"
