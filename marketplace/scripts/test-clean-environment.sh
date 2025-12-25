#!/bin/bash
# Test in completely clean environment (no node_modules, fresh install)

set -e

echo "==========================================="
echo "Testing in CLEAN environment..."
echo "==========================================="

cd "$(dirname "$0")/.."

# Create temp directory
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"

# Copy project files
echo "Copying project files..."
cp -r . "$TEMP_DIR/"
cd "$TEMP_DIR"

# Remove existing dependencies
echo "Removing existing dependencies..."
rm -rf node_modules package-lock.json

# Fresh install
echo "Fresh npm install..."
npm install --ignore-scripts

# Install Playwright
echo "Installing Playwright..."
npm install -D @playwright/test
npx playwright install chromium

# Build
echo "Building site..."
npm run build

# Run tests
echo "Running tests..."
npx playwright test --project=chromium-desktop --reporter=list

# Cleanup
cd -
rm -rf "$TEMP_DIR"

echo "==========================================="
echo "Clean environment test completed!"
echo "==========================================="
