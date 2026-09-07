#!/usr/bin/env bash
# gherkin-lint.sh — Advisory Gherkin quality check for Wall 1.
#
# If gherkin-lint is installed (npm i -g gherkin-lint) it is used. Otherwise
# falls back to awk-based rubric checks for imperative verbs, CSS selectors
# in steps, missing Background, and overlong scenarios.
#
# Non-blocking by default (exit 0 on warnings). Use --strict to turn warnings
# into failures.
#
# Usage:
#   bash gherkin-lint.sh [--path features/] [--strict]

set -euo pipefail

PATH_ARG="features/"
STRICT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --path) PATH_ARG="$2"; shift 2 ;;
    --strict) STRICT=1; shift ;;
    --help|-h)
      sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "gherkin-lint: unknown flag $1" >&2; exit 2 ;;
  esac
done

if [[ ! -d "$PATH_ARG" ]]; then
  echo "gherkin-lint: path not found: $PATH_ARG" >&2
  exit 2
fi

WARN_COUNT=0
ERROR_COUNT=0

warn() { echo "WARN  $1:$2 $3"; WARN_COUNT=$((WARN_COUNT + 1)); }
err()  { echo "ERROR $1:$2 $3"; ERROR_COUNT=$((ERROR_COUNT + 1)); }

# 1. Prefer official gherkin-lint if available
if command -v gherkin-lint >/dev/null 2>&1; then
  echo "gherkin-lint: using installed linter"
  if ! gherkin-lint "$PATH_ARG"; then
    ERROR_COUNT=1
  fi
else
  echo "gherkin-lint: falling back to awk rubric (install gherkin-lint for full rules)"

  while IFS= read -r -d '' feature; do
    # Imperative verbs / CSS selectors in steps (declarative warning)
    awk -v file="$feature" '
      /^[[:space:]]*(Given|When|Then|And|But)/ {
        line = $0
        if (line ~ /click|type|fill[ _]in|press|select.*from[ _]dropdown/) {
          printf "WARN  %s:%d imperative verb in step (prefer declarative)\n", file, NR
        }
        if (line ~ /#[a-zA-Z][-a-zA-Z0-9_]*|\.[a-zA-Z][-a-zA-Z0-9_]*[[:space:]]|xpath/) {
          printf "WARN  %s:%d CSS selector / xpath in step (prefer business language)\n", file, NR
        }
      }
    ' "$feature"

    # Scenario length (> 10 steps)
    awk -v file="$feature" '
      /^[[:space:]]*Scenario/ { sc = NR; steps = 0; sn = $0; next }
      /^[[:space:]]*(Given|When|Then|And|But)/ { if (sc) steps++ }
      /^[[:space:]]*Scenario|^[[:space:]]*Feature|^$/ {
        if (sc && steps > 10) {
          printf "WARN  %s:%d scenario has %d steps (>10 is too long)\n", file, sc, steps
        }
        if (NR != sc) { sc = 0; steps = 0 }
      }
      END {
        if (sc && steps > 10) {
          printf "WARN  %s:%d scenario has %d steps (>10 is too long)\n", file, sc, steps
        }
      }
    ' "$feature"

    # Repeated Givens without Background (3+ identical Given lines)
    dupe=$(awk '/^[[:space:]]*Given/ { print }' "$feature" | sort | uniq -c | awk '$1 >= 3 { print }')
    if [[ -n "$dupe" ]] && ! grep -q "^[[:space:]]*Background:" "$feature"; then
      warn "$feature" 0 "repeated Given lines without Background block"
    fi

    # "And" at scenario start (grammar error)
    awk -v file="$feature" '
      prev_blank = 1
      /^[[:space:]]*$/ { prev_blank = 1; next }
      /^[[:space:]]*Scenario/ { in_scenario = 1; step_count = 0; next }
      /^[[:space:]]*(Given|When|Then|And|But)/ {
        if (in_scenario && step_count == 0 && /^[[:space:]]*And/) {
          printf "ERROR %s:%d scenario starts with And (use Given/When/Then)\n", file, NR
        }
        step_count++
      }
    ' "$feature"

  done < <(find "$PATH_ARG" -name "*.feature" -print0)
fi

echo ""
echo "gherkin-lint summary: $WARN_COUNT warning(s), $ERROR_COUNT error(s)"

if [[ "$ERROR_COUNT" -gt 0 ]]; then
  exit 1
fi
if [[ "$STRICT" -eq 1 && "$WARN_COUNT" -gt 0 ]]; then
  exit 1
fi
exit 0
