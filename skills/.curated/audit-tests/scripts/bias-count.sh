#!/usr/bin/env bash
# Quick test bias pattern counter
# Usage: bash bias-count.sh [test-directory]
#
# Scans test files for common bias patterns that weaken test suites.
# See references/test-quality-deep-audit.md Section 1 for full details.

set -euo pipefail

TEST_DIR="${1:-tests}"

if [ ! -d "$TEST_DIR" ]; then
  echo "ERROR: Test directory '$TEST_DIR' not found"
  echo "Usage: bash bias-count.sh [test-directory]"
  exit 1
fi

echo "═══════════════════════════════════════"
echo "  TEST BIAS SCAN — $TEST_DIR"
echo "═══════════════════════════════════════"
echo

TOTAL_BIAS=0

count_pattern() {
  local label="$1"
  local pattern="$2"
  local count
  count=$(grep -rn "$pattern" "$TEST_DIR" 2>/dev/null | wc -l)
  TOTAL_BIAS=$((TOTAL_BIAS + count))
  printf "  %-30s %d\n" "$label" "$count"
}

echo "BIAS PATTERNS"
echo "─────────────────────────────────────"
count_pattern "Smoke-only (is not None)" "is not None$"
count_pattern "Smoke-only (assertIsNotNone)" "assertIsNotNone"
count_pattern "Smoke-only (toBeDefined)" "toBeDefined()"
count_pattern "Tautological (sorted==sorted)" "sorted.*==.*sorted"
count_pattern "Tautological (len==len)" "len.*==.*len"
count_pattern "Symmetric input (0,0)" "(0, 0)"
count_pattern "Symmetric input (1,1)" "(1, 1)"
count_pattern "Symmetric input (100,100)" "(100, 100)"
count_pattern "Range-only assertion" "assert.*<=.*<="
count_pattern 'Substring check (in str)' '" in '
echo

# Count test functions
TEST_COUNT=$(grep -rn "def test_\|it('\|it(\"\\|test('\|test(\"" "$TEST_DIR" 2>/dev/null | wc -l)

# Count total assertions
ASSERT_COUNT=$(grep -rn "assert\b\|assertEqual\|expect(" "$TEST_DIR" 2>/dev/null | wc -l)

# Assertion density
if [ "$TEST_COUNT" -gt 0 ]; then
  DENSITY=$(echo "scale=2; $ASSERT_COUNT / $TEST_COUNT" | bc)
else
  DENSITY="0"
fi

# Per-100 bias rate
if [ "$TEST_COUNT" -gt 0 ]; then
  RATE=$(echo "scale=1; $TOTAL_BIAS * 100 / $TEST_COUNT" | bc)
else
  RATE="0"
fi

echo "SUMMARY"
echo "─────────────────────────────────────"
printf "  %-30s %d\n" "Test functions" "$TEST_COUNT"
printf "  %-30s %d\n" "Total assertions" "$ASSERT_COUNT"
printf "  %-30s %s\n" "Assertion density" "$DENSITY per test"
printf "  %-30s %d\n" "Bias patterns found" "$TOTAL_BIAS"
printf "  %-30s %s\n" "Per-100-tests rate" "$RATE"
echo

# Grade
if [ "$(echo "$RATE <= 5" | bc)" -eq 1 ]; then
  echo "  Grade: LOW — no action needed"
elif [ "$(echo "$RATE <= 15" | bc)" -eq 1 ]; then
  echo "  Grade: MODERATE — review flagged tests"
elif [ "$(echo "$RATE <= 30" | bc)" -eq 1 ]; then
  echo "  Grade: HIGH — systematic remediation needed"
else
  echo "  Grade: CRITICAL — full rewrite of flagged tests"
fi
echo
echo "═══════════════════════════════════════"
