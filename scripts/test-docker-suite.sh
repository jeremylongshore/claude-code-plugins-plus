#!/bin/bash

# Docker-based Test Suite Runner
# Manages Docker test environments for comprehensive testing

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTS_RESULTS_DIR="$PROJECT_DIR/test-results"
DOCKER_IMAGE_BASE="claude-plugins"
DOCKER_REGISTRY="local"

# Default values
TEST_TARGET="full"
BUILD_ONLY=false
CLEANUP=false
VERBOSE=false

print_header() {
    echo ""
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Docker-based test suite for claude-code-plugins

OPTIONS:
    -t, --target TESTNAME    Test target: full|production|validation|all (default: full)
    -b, --build-only         Build images without running tests
    -c, --cleanup            Cleanup old containers/images after tests
    -v, --verbose            Verbose output
    --docker-compose         Use docker-compose instead of docker build
    -h, --help               Show this help message

EXAMPLES:
    # Run full test suite
    $0

    # Run production test only
    $0 --target production

    # Run all test targets
    $0 --target all

    # Build images and cleanup
    $0 --build-only --cleanup

    # Use docker-compose
    $0 --docker-compose

EOF
    exit 0
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--target)
                TEST_TARGET="$2"
                shift 2
                ;;
            -b|--build-only)
                BUILD_ONLY=true
                shift
                ;;
            -c|--cleanup)
                CLEANUP=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            --docker-compose)
                USE_DOCKER_COMPOSE=true
                shift
                ;;
            -h|--help)
                usage
                ;;
            *)
                print_error "Unknown option: $1"
                usage
                ;;
        esac
    done
}

check_docker() {
    print_header "Checking Docker Installation"

    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        print_info "https://docs.docker.com/get-docker/"
        return 1
    fi

    print_success "Docker found: $(docker --version)"

    if [[ "${USE_DOCKER_COMPOSE:-false}" == "true" ]]; then
        if ! command -v docker-compose &> /dev/null; then
            print_error "docker-compose not found. Please install Docker Compose."
            print_info "https://docs.docker.com/compose/install/"
            return 1
        fi
        print_success "Docker Compose found: $(docker-compose --version)"
    fi

    if ! docker ps &> /dev/null; then
        print_error "Docker daemon is not running or you don't have permission"
        return 1
    fi

    print_success "Docker daemon is running"
    return 0
}

build_images() {
    print_header "Building Docker Images"

    local dockerfile="$PROJECT_DIR/Dockerfile.test"

    if [[ ! -f "$dockerfile" ]]; then
        print_error "Dockerfile.test not found at $dockerfile"
        return 1
    fi

    print_info "Building from: $dockerfile"

    # Build test image
    print_info "Building test image..."
    if docker build \
        -f "$dockerfile" \
        -t "$DOCKER_REGISTRY/$DOCKER_IMAGE_BASE:test-latest" \
        --target test \
        "$PROJECT_DIR" \
        ${VERBOSE:+-v}; then
        print_success "Built: $DOCKER_REGISTRY/$DOCKER_IMAGE_BASE:test-latest"
    else
        print_error "Failed to build test image"
        return 1
    fi

    # Build production test image
    print_info "Building production test image..."
    if docker build \
        -f "$dockerfile" \
        -t "$DOCKER_REGISTRY/$DOCKER_IMAGE_BASE:test-prod-latest" \
        --target production-test \
        "$PROJECT_DIR" \
        ${VERBOSE:+-v}; then
        print_success "Built: $DOCKER_REGISTRY/$DOCKER_IMAGE_BASE:test-prod-latest"
    else
        print_error "Failed to build production test image"
        return 1
    fi

    return 0
}

run_docker_compose_tests() {
    print_header "Running Tests with Docker Compose"

    local compose_file="$PROJECT_DIR/docker-compose.test.yml"

    if [[ ! -f "$compose_file" ]]; then
        print_error "docker-compose.test.yml not found"
        return 1
    fi

    mkdir -p "$TESTS_RESULTS_DIR"

    case "$TEST_TARGET" in
        full)
            print_info "Running full test suite..."
            docker-compose -f "$compose_file" run --rm test-full
            ;;
        production)
            print_info "Running production test..."
            docker-compose -f "$compose_file" run --rm test-production
            ;;
        validation)
            print_info "Running validation suite..."
            docker-compose -f "$compose_file" run --rm test-validation
            ;;
        all)
            print_info "Running all test targets..."
            docker-compose -f "$compose_file" run --rm test-full
            docker-compose -f "$compose_file" run --rm test-production
            docker-compose -f "$compose_file" run --rm test-validation
            ;;
        *)
            print_error "Unknown test target: $TEST_TARGET"
            return 1
            ;;
    esac

    return $?
}

run_docker_tests() {
    print_header "Running Tests with Docker"

    mkdir -p "$TESTS_RESULTS_DIR"

    case "$TEST_TARGET" in
        full)
            print_info "Running full test suite in Docker..."
            docker run --rm \
                -v "$TESTS_RESULTS_DIR:/app/test-results" \
                "$DOCKER_REGISTRY/$DOCKER_IMAGE_BASE:test-latest"
            ;;
        production)
            print_info "Running production test in Docker..."
            docker run --rm \
                -v "$TESTS_RESULTS_DIR:/app/test-results" \
                "$DOCKER_REGISTRY/$DOCKER_IMAGE_BASE:test-prod-latest"
            ;;
        validation)
            print_info "Running validation suite in Docker..."
            docker run --rm \
                -v "$TESTS_RESULTS_DIR:/app/test-results" \
                -v "$PROJECT_DIR/plugins:/app/plugins" \
                -v "$PROJECT_DIR/.claude-plugin:/app/.claude-plugin" \
                "$DOCKER_REGISTRY/$DOCKER_IMAGE_BASE:test-latest" \
                bash -c "bash /app/scripts/validate-all-plugins.sh"
            ;;
        all)
            print_info "Running all test targets..."
            docker run --rm \
                -v "$TESTS_RESULTS_DIR:/app/test-results" \
                "$DOCKER_REGISTRY/$DOCKER_IMAGE_BASE:test-latest"
            docker run --rm \
                -v "$TESTS_RESULTS_DIR:/app/test-results" \
                "$DOCKER_REGISTRY/$DOCKER_IMAGE_BASE:test-prod-latest"
            ;;
        *)
            print_error "Unknown test target: $TEST_TARGET"
            return 1
            ;;
    esac

    return $?
}

cleanup_resources() {
    print_header "Cleaning Up Resources"

    print_info "Stopping containers..."
    docker-compose -f "$PROJECT_DIR/docker-compose.test.yml" down 2>/dev/null || true

    print_info "Removing old test images..."
    docker images | grep "$DOCKER_IMAGE_BASE" | grep "test" | awk '{print $3}' | \
        while read -r image_id; do
            docker rmi "$image_id" 2>/dev/null || true
        done

    print_info "Pruning Docker system (old containers, networks)..."
    docker system prune -f --filter "label!=keep" 2>/dev/null || true

    print_success "Cleanup complete"
}

report_results() {
    print_header "Test Results"

    if [[ ! -d "$TESTS_RESULTS_DIR" ]]; then
        print_warning "No test results directory found"
        return 0
    fi

    local log_files=$(find "$TESTS_RESULTS_DIR" -type f -name "*.log" 2>/dev/null | wc -l)

    if [[ $log_files -eq 0 ]]; then
        print_warning "No test logs found"
        return 0
    fi

    print_info "Found $log_files test log files:"
    echo ""

    find "$TESTS_RESULTS_DIR" -type f -name "*.log" | while read -r logfile; do
        local basename=$(basename "$logfile")
        print_info "Log: $basename"

        # Show last 10 lines of each log
        if [[ -f "$logfile" ]] && [[ $(wc -l < "$logfile") -gt 0 ]]; then
            tail -5 "$logfile" | sed 's/^/  /'
        fi
        echo ""
    done

    print_info "Full results available in: $TESTS_RESULTS_DIR"
}

main() {
    parse_args "$@"

    print_header "Claude Code Plugins - Docker Test Suite"
    print_info "Project Directory: $PROJECT_DIR"
    print_info "Test Target: $TEST_TARGET"

    # Check Docker
    if ! check_docker; then
        print_error "Docker check failed"
        exit 1
    fi

    # Build images
    if ! build_images; then
        print_error "Failed to build Docker images"
        exit 1
    fi

    if [[ "$BUILD_ONLY" == "true" ]]; then
        print_success "Build complete. Skipping tests."
        exit 0
    fi

    # Run tests
    if [[ "${USE_DOCKER_COMPOSE:-false}" == "true" ]]; then
        if ! run_docker_compose_tests; then
            print_error "Docker Compose tests failed"
            exit 1
        fi
    else
        if ! run_docker_tests; then
            print_error "Docker tests failed"
            exit 1
        fi
    fi

    # Report results
    report_results

    # Cleanup
    if [[ "$CLEANUP" == "true" ]]; then
        cleanup_resources
    fi

    print_header "Tests Complete"
    print_success "Test suite execution finished successfully"
    exit 0
}

main "$@"
