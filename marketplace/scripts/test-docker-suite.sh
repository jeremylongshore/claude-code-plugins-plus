#!/bin/bash
# Run Playwright tests in Docker for clean environment testing

set -e

echo "===========================================" echo "Building Docker test environment..."
echo "==========================================="

cd "$(dirname "$0")/.."

# Build Docker image
docker-compose -f docker-compose.test.yml build playwright-tests

echo "==========================================="
echo "Running Playwright tests in Docker..."
echo "==========================================="

# Run tests and capture exit code
docker-compose -f docker-compose.test.yml run --rm playwright-tests || TEST_EXIT=$?

echo "==========================================="
echo "Tests completed. Exit code: ${TEST_EXIT:-0}"
echo "==========================================="

# Copy results from container
echo "Test results saved to:"
echo "  - test-results/screenshots/"
echo "  - playwright-report/"

exit ${TEST_EXIT:-0}
