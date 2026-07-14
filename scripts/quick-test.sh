#!/bin/bash

# Quick Test Runner
# Fast validation for development workflow
# Faster alternative to full test suite
#
# Covers: dependency install, package build, lint, and a marketplace-tier
# validator sweep. It does NOT run the full CI gate — catalog-sync drift,
# the security scanner, unicode hygiene, markdownlint/eslint/ruff/format,
# the unit-test suites, and the submission-docs gate only run in CI
# (validate-plugins.yml → ci-required). A clean run here is a strong
# signal, not a merge guarantee.

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
if ! command -v pnpm > /dev/null; then
  echo -e "${YELLOW}pnpm not found. Install it with: corepack enable pnpm${NC}"
  echo "See: https://pnpm.io/installation"
  exit 1
fi
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

# Test 5: Validation (marketplace tier — the same bar submissions are graded against)
# Non-fatal by design: the whole-corpus sweep carries pre-existing findings in
# plugins you didn't touch. Check the log for findings in YOUR files — the PR
# pre-screen grades your changed plugins against this same marketplace tier.
echo -e "${BLUE}Validating plugins (marketplace tier)...${NC}"
if python3 scripts/validate-skills-schema.py --marketplace > /tmp/quick-test-validate.log 2>&1; then
    echo -e "${GREEN}✓ Validation passed${NC}"
else
    echo -e "${YELLOW}⚠ Validation findings (whole-corpus sweep; non-fatal here)${NC}"
    echo -e "${YELLOW}  Review /tmp/quick-test-validate.log for findings in files YOU changed.${NC}"
    tail -5 /tmp/quick-test-validate.log
fi
echo ""

echo -e "${BLUE}Quick tests complete!${NC}"
echo ""
echo "Logs:"
echo "  Build:      /tmp/quick-test-build.log"
echo "  Lint:       /tmp/quick-test-lint.log"
echo "  Validation: /tmp/quick-test-validate.log"
