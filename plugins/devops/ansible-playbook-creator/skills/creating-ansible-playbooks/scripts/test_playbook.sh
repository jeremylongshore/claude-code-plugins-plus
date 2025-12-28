#!/bin/bash
#
# Ansible playbook test script
#
# Executes playbook in test environment (container) including:
# - Container setup
# - Playbook execution
# - Result verification
# - Cleanup
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PLAYBOOK_FILE=""
CONTAINER_IMAGE="ubuntu:22.04"
CONTAINER_NAME="ansible-test-$$"
INVENTORY="localhost"
EXTRA_VARS=""
TAGS=""
SKIP_TAGS=""
KEEP_CONTAINER=false
VERBOSE=false

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Execute Ansible playbook in test container environment

OPTIONS:
    -p, --playbook FILE       Path to playbook file [REQUIRED]
    -i, --image IMAGE         Docker image to use (default: ubuntu:22.04)
    -l, --inventory HOSTS     Inventory or hosts (default: localhost)
    -e, --extra-vars VARS     Extra variables (JSON format)
    -t, --tags TAGS           Only run tasks with these tags
    --skip-tags TAGS          Skip tasks with these tags
    -k, --keep                Keep container after test
    -v, --verbose             Verbose output
    -h, --help                Show this help message

EXAMPLES:
    $0 --playbook site.yml
    $0 -p playbook.yml -i hosts.ini -v
    $0 -p playbook.yml --tags deployment

EOF
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--playbook)
            PLAYBOOK_FILE="$2"
            shift 2
            ;;
        -i|--image)
            CONTAINER_IMAGE="$2"
            shift 2
            ;;
        -l|--inventory)
            INVENTORY="$2"
            shift 2
            ;;
        -e|--extra-vars)
            EXTRA_VARS="$2"
            shift 2
            ;;
        -t|--tags)
            TAGS="$2"
            shift 2
            ;;
        --skip-tags)
            SKIP_TAGS="$2"
            shift 2
            ;;
        -k|--keep)
            KEEP_CONTAINER=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
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

# Validate required arguments
if [[ -z "$PLAYBOOK_FILE" ]]; then
    echo -e "${RED}Error: --playbook argument is required${NC}"
    usage
fi

if [[ ! -f "$PLAYBOOK_FILE" ]]; then
    echo -e "${RED}Error: File not found: $PLAYBOOK_FILE${NC}"
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

# Function: Check dependencies
check_dependencies() {
    local missing=false

    if ! command -v docker &> /dev/null; then
        error "docker not found in PATH"
        missing=true
    fi

    if ! command -v ansible-playbook &> /dev/null; then
        error "ansible-playbook not found in PATH"
        missing=true
    fi

    if [[ "$missing" == true ]]; then
        exit 1
    fi

    success "All dependencies found"
}

# Function: Cleanup container
cleanup_container() {
    if [[ "$KEEP_CONTAINER" == true ]]; then
        log "Container kept for inspection: $CONTAINER_NAME"
        return 0
    fi

    log "Cleaning up container: $CONTAINER_NAME"
    docker rm -f "$CONTAINER_NAME" &>/dev/null || true
}

# Function: Setup container
setup_container() {
    log "Setting up test container: $CONTAINER_NAME"

    # Check if image exists
    if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${CONTAINER_IMAGE}$"; then
        log "Pulling Docker image: $CONTAINER_IMAGE"
        if ! docker pull "$CONTAINER_IMAGE"; then
            error "Failed to pull Docker image: $CONTAINER_IMAGE"
            return 1
        fi
    fi

    # Create container
    log "Creating container from image: $CONTAINER_IMAGE"
    if ! docker create \
        --name "$CONTAINER_NAME" \
        --hostname test-host \
        --entrypoint /bin/bash \
        "$CONTAINER_IMAGE" \
        -c "sleep infinity" &>/dev/null; then
        error "Failed to create container"
        return 1
    fi

    # Start container
    if ! docker start "$CONTAINER_NAME" &>/dev/null; then
        error "Failed to start container"
        docker rm -f "$CONTAINER_NAME" &>/dev/null || true
        return 1
    fi

    success "Container setup complete"
    return 0
}

# Function: Install Ansible in container
install_ansible() {
    log "Installing Ansible in container..."

    # Update package manager
    docker exec "$CONTAINER_NAME" \
        bash -c "apt-get update && apt-get install -y python3 python3-pip openssh-client" \
        &>/dev/null || {
            warning "apt-get update failed, trying without update"
        }

    # Install Ansible
    docker exec "$CONTAINER_NAME" \
        bash -c "pip install ansible" \
        &>/dev/null || {
            error "Failed to install Ansible"
            cleanup_container
            return 1
        }

    success "Ansible installed"
    return 0
}

# Function: Copy playbook to container
copy_playbook() {
    local playbook_dir=$(dirname "$PLAYBOOK_FILE")
    local playbook_name=$(basename "$PLAYBOOK_FILE")

    log "Copying playbook to container..."

    # Copy entire directory to container
    if ! docker cp "$playbook_dir" "$CONTAINER_NAME:/playbooks" &>/dev/null; then
        error "Failed to copy playbook to container"
        return 1
    fi

    success "Playbook copied to container"
}

# Function: Create inventory
create_inventory() {
    log "Creating inventory..."

    # Create inventory file in container
    docker exec "$CONTAINER_NAME" \
        bash -c "mkdir -p /etc/ansible && echo 'localhost ansible_connection=local' > /etc/ansible/hosts" \
        &>/dev/null

    success "Inventory created"
}

# Function: Run playbook
run_playbook() {
    log "Running playbook: $PLAYBOOK_FILE"

    local playbook_name=$(basename "$PLAYBOOK_FILE")
    local ansible_cmd="ansible-playbook /playbooks/$playbook_name"

    # Add inventory
    if [[ "$INVENTORY" != "localhost" ]]; then
        ansible_cmd="$ansible_cmd -i $INVENTORY"
    fi

    # Add tags
    if [[ -n "$TAGS" ]]; then
        ansible_cmd="$ansible_cmd --tags $TAGS"
    fi

    # Add skip tags
    if [[ -n "$SKIP_TAGS" ]]; then
        ansible_cmd="$ansible_cmd --skip-tags $SKIP_TAGS"
    fi

    # Add extra variables
    if [[ -n "$EXTRA_VARS" ]]; then
        ansible_cmd="$ansible_cmd -e '$EXTRA_VARS'"
    fi

    # Add verbose flag
    if [[ "$VERBOSE" == true ]]; then
        ansible_cmd="$ansible_cmd -vvv"
    fi

    # Run playbook
    local output=$(docker exec "$CONTAINER_NAME" bash -c "$ansible_cmd" 2>&1 || echo "FAILED")

    if echo "$output" | grep -q "FAILED\|ERROR"; then
        error "Playbook execution failed"
        echo ""
        echo "$output"
        return 1
    fi

    if [[ "$VERBOSE" == true ]]; then
        echo ""
        echo "$output"
    fi

    success "Playbook executed successfully"
    return 0
}

# Function: Get execution report
get_report() {
    log "Generating execution report..."

    local report=$(docker exec "$CONTAINER_NAME" \
        bash -c "ansible-playbook /playbooks/$(basename "$PLAYBOOK_FILE") --list-tasks" 2>/dev/null || echo "")

    if [[ -n "$report" ]]; then
        echo ""
        echo "Task List:"
        echo "$report"
    fi
}

# Function: Verify execution
verify_execution() {
    log "Verifying playbook execution..."

    # Check container status
    local status=$(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")

    if [[ "$status" == "running" ]]; then
        success "Container is running"
        return 0
    else
        error "Container is not running (status: $status)"
        return 1
    fi
}

# Cleanup on exit
trap cleanup_container EXIT

# Main execution
main() {
    log "=========================================="
    log "Ansible Playbook Test"
    log "=========================================="
    log "Playbook: $PLAYBOOK_FILE"
    log "Container Image: $CONTAINER_IMAGE"
    echo ""

    # Pre-test checks
    check_dependencies

    # Setup environment
    if ! setup_container; then
        error "Container setup failed"
        exit 1
    fi

    # Install Ansible
    if ! install_ansible; then
        error "Ansible installation failed"
        exit 1
    fi

    # Prepare for execution
    copy_playbook
    create_inventory

    # Execute playbook
    if ! run_playbook; then
        error "Playbook test failed"
        exit 1
    fi

    # Verify and report
    get_report
    verify_execution

    echo ""
    success "Test completed successfully"
    log "=========================================="
    exit 0
}

# Run main function
main "$@"
