#!/bin/bash

# Quick Test Runner
# Fast validation for development workflow
# Faster alternative to full test suite

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Quick Test Suite${NC}"
echo "================"
echo ""

# Test 1: Check tools
echo -e "${BLUE}Checking tools...${NC}"
command -v pnpm > /dev/null || (echo "Installing pnpm..." && npm install -g pnpm@9.15.9)
echo -e "${GREEN}✓ Tools ready${NC}"
echo ""

# Test 2: Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pnpm install --frozen-lockfile > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Test 3: Build
echo -e "${BLUE}Building packages...${NC}"
if pnpm build > /tmp/quick-test-build.log 2>&1; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    tail -20 /tmp/quick-test-build.log
    exit 1
fi
echo ""

# Test 4: Lint
echo -e "${BLUE}Linting...${NC}"
if pnpm lint > /tmp/quick-test-lint.log 2>&1; then
    echo -e "${GREEN}✓ Lint passed${NC}"
else
    echo -e "${YELLOW}⚠ Lint warnings${NC}"
    tail -5 /tmp/quick-test-lint.log
fi
echo ""

# Test 5: Validation
echo -e "${BLUE}Validating plugins...${NC}"
if bash scripts/validate-all-plugins.sh > /tmp/quick-test-validate.log 2>&1; then
    echo -e "${GREEN}✓ Validation passed${NC}"
else
    echo -e "${YELLOW}⚠ Validation warnings${NC}"
    tail -5 /tmp/quick-test-validate.log
fi
echo ""

echo -e "${BLUE}Quick tests complete!${NC}"
echo ""
echo "Logs:"
echo "  Build:      /tmp/quick-test-build.log"
echo "  Lint:       /tmp/quick-test-lint.log"
echo "  Validation: /tmp/quick-test-validate.log"
