#!/usr/bin/env bash
#
# smoke_docx_build.sh
#
# Smoke test for DOCX build system.
# Runs build_standards_docx.py and verifies outputs.
#
# Success criteria:
#   - Script completes within 90 seconds
#   - All 5 DOCX files created
#   - Each file is >10KB (non-trivial content)
#
# Exit codes:
#   0 - Success
#   1 - Failure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/000-docs"

TIMEOUT=90  # seconds
MIN_FILE_SIZE=10240  # 10KB

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Expected DOCX files
EXPECTED_FILES=(
    "6767-c-DR-STND-claude-code-extensions-standard.docx"
    "6767-d-AT-STND-claude-code-extensions-schema.docx"
    "6767-e-WA-STND-extensions-validation-and-ci-gates.docx"
    "6767-f-AT-ARCH-plugin-scaffold-diagrams.docx"
    "6767-g-AT-ARCH-skill-scaffold-diagrams.docx"
)

echo "=============================================================================="
echo "Standard of Truth DOCX Build - Smoke Test"
echo "=============================================================================="
echo ""
echo "Timeout: ${TIMEOUT}s"
echo "Min file size: ${MIN_FILE_SIZE} bytes ($(echo "scale=1; $MIN_FILE_SIZE/1024" | bc)KB)"
echo ""

# Clean up any previous DOCX files to ensure fresh build
echo "Cleaning up previous DOCX files..."
for file in "${EXPECTED_FILES[@]}"; do
    if [[ -f "$DOCS_DIR/$file" ]]; then
        rm "$DOCS_DIR/$file"
        echo "  Removed: $file"
    fi
done
echo ""

# Run the build script with timeout
echo "Running build_standards_docx.py (timeout: ${TIMEOUT}s)..."
echo ""

START_TIME=$(date +%s)

if timeout "$TIMEOUT" python3 "$SCRIPT_DIR/build_standards_docx.py"; then
    BUILD_EXIT_CODE=0
else
    BUILD_EXIT_CODE=$?
fi

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "Build completed in ${ELAPSED}s (exit code: $BUILD_EXIT_CODE)"
echo ""

# Check if build failed
if [[ $BUILD_EXIT_CODE -ne 0 ]]; then
    echo -e "${RED}✗ FAILED: Build script exited with code $BUILD_EXIT_CODE${NC}"
    exit 1
fi

# Verify all 5 DOCX files were created
echo "Verifying outputs..."
echo ""

MISSING=0
TOO_SMALL=0

for file in "${EXPECTED_FILES[@]}"; do
    FILE_PATH="$DOCS_DIR/$file"

    if [[ ! -f "$FILE_PATH" ]]; then
        echo -e "${RED}✗ MISSING: $file${NC}"
        MISSING=$((MISSING + 1))
    else
        FILE_SIZE=$(stat -c%s "$FILE_PATH" 2>/dev/null || stat -f%z "$FILE_PATH" 2>/dev/null)

        if [[ $FILE_SIZE -lt $MIN_FILE_SIZE ]]; then
            echo -e "${YELLOW}✗ TOO SMALL: $file (${FILE_SIZE} bytes < ${MIN_FILE_SIZE} bytes)${NC}"
            TOO_SMALL=$((TOO_SMALL + 1))
        else
            echo -e "${GREEN}✓ VALID: $file (${FILE_SIZE} bytes)${NC}"
        fi
    fi
done

echo ""
echo "=============================================================================="
echo "Summary"
echo "=============================================================================="
echo "Elapsed time: ${ELAPSED}s / ${TIMEOUT}s"
echo "Files created: $((5 - MISSING))/5"
echo "Files valid: $((5 - MISSING - TOO_SMALL))/5"

if [[ $MISSING -gt 0 ]]; then
    echo -e "${RED}Missing files: $MISSING${NC}"
fi

if [[ $TOO_SMALL -gt 0 ]]; then
    echo -e "${YELLOW}Undersized files: $TOO_SMALL${NC}"
fi

echo ""

# Final verdict
if [[ $MISSING -eq 0 && $TOO_SMALL -eq 0 ]]; then
    echo -e "${GREEN}✓ SMOKE TEST PASSED${NC}"
    exit 0
else
    echo -e "${RED}✗ SMOKE TEST FAILED${NC}"
    exit 1
fi
