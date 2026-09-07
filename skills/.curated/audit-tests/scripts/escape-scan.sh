#!/usr/bin/env bash
# escape-scan.sh — detect AI escape attempts in a proposed diff.
#
# Scans a unified diff (from git or a patch file) for patterns that indicate
# the AI is trying to lower a wall instead of meeting the bar.
#
# Severity grammar:
#   FLAG      → logged, does not halt (printed on stderr)
#   CHALLENGE → require engineer-approved reason (exit 1)
#   REFUSE    → halt the pipeline (exit 2)
#
# Exit codes:
#   0 — clean
#   1 — CHALLENGE (at least one must-challenge pattern matched)
#   2 — REFUSE (at least one refuse pattern matched, or hash mismatch)
#
# Usage:
#   git diff | bash escape-scan.sh -
#   bash escape-scan.sh path/to/change.patch
#   bash escape-scan.sh --staged          # git diff --cached
#   bash escape-scan.sh --range HEAD~1..HEAD

set -euo pipefail

DIFF_SRC=""
VERIFY_HASH=1
ROOT="${ROOT:-$(pwd)}"
HASH_SCRIPT="$(dirname "$0")/harness-hash.sh"

if [[ "$#" -eq 0 ]]; then
  echo "escape-scan: pass a diff source (- for stdin, --staged, --range, or a patch file)" >&2
  exit 2
fi

case "$1" in
  -) DIFF_SRC="/dev/stdin" ;;
  --staged) DIFF_SRC=$(mktemp); git diff --cached > "$DIFF_SRC" ;;
  --range) DIFF_SRC=$(mktemp); git diff "$2" > "$DIFF_SRC"; shift ;;
  --no-hash) VERIFY_HASH=0; shift; DIFF_SRC="$1" ;;
  --help|-h)
    sed -n '2,22p' "$0"; exit 0 ;;
  *) DIFF_SRC="$1" ;;
esac

if [[ ! -r "$DIFF_SRC" ]]; then
  echo "escape-scan: cannot read $DIFF_SRC" >&2
  exit 2
fi

REFUSE=0
CHALLENGE=0
FLAG=0

# --- Load floor thresholds from tests/TESTING.md (fallback to defaults) ---
# Reads canonical thresholds so audits enforce the repo's policy, not a
# hardcoded script-level guess. Format expected in TESTING.md (policy section):
#   coverage.line: 80
#   coverage.branch: 70
#   mutation.kill_rate: 70
COVERAGE_LINE_FLOOR=80
COVERAGE_BRANCH_FLOOR=70
MUTATION_FLOOR=70
TESTING_MD="$ROOT/tests/TESTING.md"
if [[ -f "$TESTING_MD" ]]; then
  v=$(grep -Ei '^\s*coverage\.line\s*:' "$TESTING_MD" | head -1 | sed -E 's/.*:\s*([0-9]+).*/\1/')
  [[ -n "$v" ]] && COVERAGE_LINE_FLOOR="$v"
  v=$(grep -Ei '^\s*coverage\.branch\s*:' "$TESTING_MD" | head -1 | sed -E 's/.*:\s*([0-9]+).*/\1/')
  [[ -n "$v" ]] && COVERAGE_BRANCH_FLOOR="$v"
  v=$(grep -Ei '^\s*mutation\.kill_rate\s*:' "$TESTING_MD" | head -1 | sed -E 's/.*:\s*([0-9]+).*/\1/')
  [[ -n "$v" ]] && MUTATION_FLOOR="$v"
fi

# Collect only added lines (prefix + but not +++)
added_lines=$(grep -E '^\+[^+]' "$DIFF_SRC" || true)
file_headers=$(grep -E '^\+\+\+ ' "$DIFF_SRC" || true)

note() {
  local severity="$1" msg="$2"
  echo "[$severity] $msg" >&2
  case "$severity" in
    REFUSE) REFUSE=$((REFUSE + 1)) ;;
    CHALLENGE) CHALLENGE=$((CHALLENGE + 1)) ;;
    FLAG) FLAG=$((FLAG + 1)) ;;
  esac
}

# --- REFUSE: coverage threshold edits ---
# Floor is policy-driven (tests/TESTING.md coverage.line). Any explicit
# threshold lower than the floor is an escape attempt.
check_below_floor() {
  local line="$1" floor="$2"
  local n
  n=$(printf '%s\n' "$line" | grep -oE '[0-9]+' | head -1)
  [[ -n "$n" ]] && [[ "$n" -lt "$floor" ]]
}
while IFS= read -r line; do
  if [[ "$line" =~ fail_under[[:space:]]*=[[:space:]]*[0-9] ]] || [[ "$line" =~ --cov-fail-under=[0-9] ]]; then
    if check_below_floor "$line" "$COVERAGE_LINE_FLOOR"; then
      note REFUSE "coverage fail_under lowered below policy floor ($COVERAGE_LINE_FLOOR) — escape attempt"
    fi
  fi
  if [[ "$line" =~ \"(branches|lines|functions|statements)\"[[:space:]]*:[[:space:]]*[0-9] ]]; then
    if check_below_floor "$line" "$COVERAGE_LINE_FLOOR"; then
      note REFUSE "Jest/c8 coverageThreshold lowered below policy floor ($COVERAGE_LINE_FLOOR) — escape attempt"
    fi
  fi
done <<< "$added_lines"
if echo "$added_lines" | grep -Eq 'coverageThreshold[[:space:]]*:[[:space:]]*0'; then
  note REFUSE "coverageThreshold set to 0 (escape attempt)"
fi
if echo "$added_lines" | grep -Eq 'minimum[[:space:]]*=[[:space:]]*0\.[0-7]'; then
  note REFUSE "JaCoCo minimum lowered (escape attempt)"
fi

# --- REFUSE: architecture bypasses ---
if echo "$added_lines" | grep -Eq 'depcruise-disable|@ArchIgnore|skip_violations|ignore_imports[[:space:]]*=|severity[[:space:]]*:[[:space:]]*"warn"'; then
  note REFUSE "architecture rule bypass (depcruise-disable / @ArchIgnore / skip_violations / ignore_imports / severity downgrade)"
fi

# --- REFUSE: wholesale test deletion (file headers only) ---
# Detect deleted test files with no compensating additions
deleted_tests=$(grep -E '^--- a/.*test.*|^--- a/.*spec.*' "$DIFF_SRC" | grep -v 'test.*\.md$' || true)
added_tests=$(echo "$file_headers" | grep -E '\+\+\+ b/.*test.*|\+\+\+ b/.*spec.*' || true)
if [[ -n "$deleted_tests" && -z "$added_tests" ]]; then
  note REFUSE "test file(s) deleted without compensating additions"
fi

# --- REFUSE: .feature file mutation (hash check) ---
if [[ "$VERIFY_HASH" -eq 1 && -f "$ROOT/.harness-hash" && -x "$HASH_SCRIPT" ]]; then
  if ! (cd "$ROOT" && bash "$HASH_SCRIPT" --verify >/dev/null 2>&1); then
    note REFUSE "HARNESS_TAMPERED — pinned .feature or rule-config file changed"
  fi
fi
# Also REFUSE if the diff itself touches .feature files
if echo "$file_headers" | grep -Eq '\+\+\+ b/.*\.feature'; then
  note REFUSE ".feature file modified (human-owned artifact)"
fi

# --- CHALLENGE: test skip markers ---
if echo "$added_lines" | grep -Eq '@pytest\.mark\.skip|\.skip\(|\.only\(|@Ignore\b|@Disabled\b|@SkipTest\b'; then
  note CHALLENGE "test skip marker added (requires engineer-approved reason)"
fi

# --- CHALLENGE: mutation bypass markers ---
if echo "$added_lines" | grep -Eq 'pragma:[[:space:]]*no[[:space:]]*mutate|Stryker[[:space:]]*disable|@DoNotMutate'; then
  note CHALLENGE "mutation bypass marker added"
fi

# --- CHALLENGE: assertion weakening (diff-aware) ---
# Look at removed+added pairs: old was a strong assertion, new is weak
# Heuristic: new line contains assertTrue(True) / toBeDefined() / is not None
if echo "$added_lines" | grep -Eq 'assertTrue\(True\)|assertEquals\(true,[[:space:]]*true\)'; then
  note CHALLENGE "trivially-true assertion added (assertTrue(True) equivalent)"
fi

# --- FLAG: weak-assertion patterns (informational) ---
if echo "$added_lines" | grep -Eq 'toBeDefined\(\)|\.is not None'; then
  note FLAG "smoke-only assertion pattern (consider tightening)"
fi

# --- Summary & exit ---
echo "escape-scan: REFUSE=$REFUSE CHALLENGE=$CHALLENGE FLAG=$FLAG"
if [[ "$REFUSE" -gt 0 ]]; then
  echo "escape-scan: pipeline halted (REFUSE)" >&2
  exit 2
fi
if [[ "$CHALLENGE" -gt 0 ]]; then
  echo "escape-scan: pipeline needs engineer approval (CHALLENGE)" >&2
  exit 1
fi
exit 0
