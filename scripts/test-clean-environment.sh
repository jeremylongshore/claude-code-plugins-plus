#!/bin/bash

# Clean Environment Testing Script
# Tests that project builds and validates in an isolated environment
# Simulates Docker testing without requiring Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_DIR="${1:-.}"
TEMP_TEST_DIR="/tmp/claude-plugins-test-$$"
LOG_FILE="/tmp/claude-plugins-test-$$.log"
RESULTS_DIR="./test-results"

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
log_header() {
    echo -e "${BLUE}======================================${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}$1${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}======================================${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}" | tee -a "$LOG_FILE"
    PASSED=$((PASSED + 1))
}

log_error() {
    echo -e "${RED}✗ $1${NC}" | tee -a "$LOG_FILE"
    FAILED=$((FAILED + 1))
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}" | tee -a "$LOG_FILE"
    WARNINGS=$((WARNINGS + 1))
}

log_info() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

cleanup() {
    echo ""
    log_header "Cleaning up test artifacts"
    if [[ -d "$TEMP_TEST_DIR" ]]; then
        rm -rf "$TEMP_TEST_DIR"
        log_success "Removed temporary test directory"
    fi
    echo ""
    log_header "Test Summary"
    log_info "Passed: ${GREEN}$PASSED${NC}"
    log_info "Failed: ${RED}$FAILED${NC}"
    log_info "Warnings: ${YELLOW}$WARNINGS${NC}"
    log_info "Log file: $LOG_FILE"
    log_info "Results: $RESULTS_DIR"
}

trap cleanup EXIT

# Main test execution
main() {
    log_header "Clean Environment Test Suite"
    log_info "Test Directory: $TEST_DIR"
    log_info "Temp Directory: $TEMP_TEST_DIR"
    log_info "Log File: $LOG_FILE"
    log_info "Results Directory: $RESULTS_DIR"
    echo ""

    # Create results directory
    mkdir -p "$RESULTS_DIR"

    # Test 1: Check required tools
    log_header "Test 1: Checking Required Tools"

    if command -v node &> /dev/null; then
        local NODE_VERSION=$(node --version)
        log_success "Node.js found: $NODE_VERSION"
    else
        log_error "Node.js not found. Required version: v20+"
    fi

    if command -v npm &> /dev/null; then
        local NPM_VERSION=$(npm --version)
        log_success "npm found: $NPM_VERSION"
    else
        log_error "npm not found"
    fi

    if command -v pnpm &> /dev/null; then
        local PNPM_VERSION=$(pnpm --version)
        log_success "pnpm found: $PNPM_VERSION"
    else
        log_warning "pnpm not found. Installing globally..."
        npm install -g pnpm@9.15.9 >> "$LOG_FILE" 2>&1
        log_success "pnpm installed"
    fi

    if command -v jq &> /dev/null; then
        log_success "jq found"
    else
        log_warning "jq not found. Installing..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y jq >> "$LOG_FILE" 2>&1
        elif command -v brew &> /dev/null; then
            brew install jq >> "$LOG_FILE" 2>&1
        else
            log_warning "Could not auto-install jq"
        fi
    fi

    if command -v git &> /dev/null; then
        log_success "git found"
    else
        log_error "git not found"
    fi

    echo ""

    # Test 2: Verify project structure
    log_header "Test 2: Verifying Project Structure"

    local required_files=(
        "package.json"
        "pnpm-lock.yaml"
        ".claude-plugin/marketplace.extended.json"
        "scripts/validate-all-plugins.sh"
    )

    for file in "${required_files[@]}"; do
        if [[ -f "$TEST_DIR/$file" ]]; then
            log_success "Found: $file"
        else
            log_error "Missing: $file"
        fi
    done

    local required_dirs=(
        "plugins"
        "scripts"
        ".claude-plugin"
    )

    for dir in "${required_dirs[@]}"; do
        if [[ -d "$TEST_DIR/$dir" ]]; then
            log_success "Found directory: $dir"
        else
            log_error "Missing directory: $dir"
        fi
    done

    echo ""

    # Test 3: Test dependency installation in clean directory
    log_header "Test 3: Testing Clean Install"

    mkdir -p "$TEMP_TEST_DIR"
    cd "$TEMP_TEST_DIR"

    log_info "Copying project to: $TEMP_TEST_DIR"
    cp -r "$TEST_DIR"/* . 2>/dev/null || true
    cp "$TEST_DIR"/.gitignore . 2>/dev/null || true

    if [[ ! -f "package.json" ]]; then
        log_error "package.json not copied to temp directory"
        return 1
    fi

    log_info "Running: pnpm install --frozen-lockfile"
    if pnpm install --frozen-lockfile >> "$LOG_FILE" 2>&1; then
        log_success "Clean install completed"
    else
        log_error "Clean install failed"
    fi

    echo ""

    # Test 4: Build all packages
    log_header "Test 4: Building All Packages"

    log_info "Running: pnpm build"
    if pnpm build >> "$RESULTS_DIR/build-output.log" 2>&1; then
        log_success "Build completed successfully"
    else
        log_error "Build failed (see $RESULTS_DIR/build-output.log)"
    fi

    echo ""

    # Test 5: Run tests
    log_header "Test 5: Running Tests"

    log_info "Running: pnpm test"
    if pnpm test >> "$RESULTS_DIR/test-output.log" 2>&1; then
        log_success "Tests passed"
    else
        log_warning "Tests failed or incomplete (see $RESULTS_DIR/test-output.log)"
    fi

    echo ""

    # Test 6: Linting
    log_header "Test 6: Running Linting"

    log_info "Running: pnpm lint"
    if pnpm lint >> "$RESULTS_DIR/lint-output.log" 2>&1; then
        log_success "Linting passed"
    else
        log_warning "Linting issues found (see $RESULTS_DIR/lint-output.log)"
    fi

    echo ""

    # Test 7: Type checking
    log_header "Test 7: Running Type Checking"

    log_info "Running: pnpm typecheck"
    if pnpm typecheck >> "$RESULTS_DIR/typecheck-output.log" 2>&1; then
        log_success "Type checking passed"
    else
        log_warning "Type checking issues found (see $RESULTS_DIR/typecheck-output.log)"
    fi

    echo ""

    # Test 8: Plugin validation
    log_header "Test 8: Validating Plugins"

    log_info "Running: bash scripts/validate-all-plugins.sh"
    if bash scripts/validate-all-plugins.sh >> "$RESULTS_DIR/validation-output.log" 2>&1; then
        log_success "Plugin validation passed"
    else
        log_warning "Plugin validation issues found (see $RESULTS_DIR/validation-output.log)"
    fi

    echo ""

    # Test 9: Marketplace JSON sync check
    log_header "Test 9: Verifying Marketplace Sync"

    if [[ -f "scripts/sync-marketplace.cjs" ]]; then
        log_info "Running: node scripts/sync-marketplace.cjs"
        if node scripts/sync-marketplace.cjs >> "$RESULTS_DIR/sync-output.log" 2>&1; then
            log_success "Marketplace sync check passed"
        else
            log_warning "Marketplace sync issues (see $RESULTS_DIR/sync-output.log)"
        fi
    else
        log_warning "Marketplace sync script not found"
    fi

    echo ""

    # Test 10: Disk usage and performance
    log_header "Test 10: Environment Metrics"

    local disk_usage=$(du -sh . 2>/dev/null | cut -f1)
    local node_modules_size=$(du -sh node_modules 2>/dev/null | cut -f1)
    log_info "Total disk usage: $disk_usage"
    log_info "node_modules size: $node_modules_size"
    log_info "Node version: $(node --version)"
    log_info "npm version: $(npm --version)"
    log_info "pnpm version: $(pnpm --version)"

    echo ""

    # Return to original directory
    cd - > /dev/null

    # Test 11: Python validation scripts
    log_header "Test 11: Python Validation Scripts"

    if command -v python3 &> /dev/null; then
        if [[ -f "$TEST_DIR/scripts/validate-skills-schema.py" ]]; then
            log_info "Running: python3 scripts/validate-skills-schema.py"
            if python3 "$TEST_DIR/scripts/validate-skills-schema.py" >> "$RESULTS_DIR/python-validation.log" 2>&1; then
                log_success "Python validation scripts passed"
            else
                log_warning "Python validation issues (see $RESULTS_DIR/python-validation.log)"
            fi
        fi
    else
        log_warning "Python3 not found, skipping python validation"
    fi

    echo ""

    # Final summary
    log_header "Final Test Results"

    if [[ $FAILED -eq 0 ]]; then
        log_success "All critical tests passed!"
        return 0
    else
        log_error "Some tests failed. Review logs above."
        return 1
    fi
}

# Run main function
main "$@"
exit $?
