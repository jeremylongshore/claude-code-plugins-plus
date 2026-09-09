#!/bin/sh
# Fixture tests for scripts/hyperfocus-hook.sh and scripts/hyperfocus-state.
# POSIX sh. Exits non-zero on first assertion failure after printing a summary.

set -u

script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "$script_dir/.." && pwd)
hook="$root_dir/scripts/hyperfocus-hook.sh"
state_bin="$root_dir/scripts/hyperfocus-state"

fail_count=0
pass_count=0

pass() {
  pass_count=$((pass_count + 1))
  echo "ok - $1"
}

fail() {
  fail_count=$((fail_count + 1))
  echo "FAIL - $1"
}

assert_eq() {
  desc=$1
  expected=$2
  actual=$3
  if [ "$expected" = "$actual" ]; then
    pass "$desc"
  else
    fail "$desc (expected [$expected], got [$actual])"
  fi
}

assert_empty() {
  desc=$1
  actual=$2
  if [ -z "$actual" ]; then
    pass "$desc"
  else
    fail "$desc (expected empty, got [$actual])"
  fi
}

assert_contains() {
  desc=$1
  haystack=$2
  needle=$3
  case "$haystack" in
    *"$needle"*) pass "$desc" ;;
    *) fail "$desc (missing [$needle])" ;;
  esac
}

tmp_base=$(mktemp -d)
cleanup() {
  rm -rf "$tmp_base"
}
trap cleanup EXIT

# --- Case: absent state -> empty output/exit 0 ---
data_dir="$tmp_base/absent/data"
out=$("$hook" --data "$data_dir" --root "$root_dir" --project "" 2>&1)
rc=$?
assert_empty "absent state produces no output" "$out"
assert_eq "absent state exits 0" 0 "$rc"

# --- Case: enabled=false -> empty ---
data_dir="$tmp_base/disabled/data"
mkdir -p "$data_dir"
printf 'version=1\nenabled=false\nmode=flow\n' > "$data_dir/state"
out=$("$hook" --data "$data_dir" --root "$root_dir" --project "" 2>&1)
rc=$?
assert_empty "enabled=false produces no output" "$out"
assert_eq "enabled=false exits 0" 0 "$rc"

# --- Case: enabled=true mode=flow -> JSON contains flow marker + valid JSON ---
data_dir="$tmp_base/flow/data"
mkdir -p "$data_dir"
printf 'version=1\nenabled=true\nmode=flow\n' > "$data_dir/state"
out=$("$hook" --data "$data_dir" --root "$root_dir" --project "")
rc=$?
assert_eq "enabled=true flow exits 0" 0 "$rc"
assert_contains "flow output contains flow-mode marker" "$out" "What"
if command -v python3 >/dev/null 2>&1; then
  if printf '%s' "$out" | python3 -c 'import json,sys; json.load(sys.stdin)' >/dev/null 2>&1; then
    pass "flow output is valid JSON"
  else
    fail "flow output is valid JSON"
  fi
else
  echo "skip - python3 not available, skipping JSON validation"
fi

# --- Case: unknown mode -> flow fallback ---
data_dir="$tmp_base/unknown-mode/data"
mkdir -p "$data_dir"
printf 'version=1\nenabled=true\nmode=bogus\n' > "$data_dir/state"
out=$("$hook" --data "$data_dir" --root "$root_dir" --project "")
assert_contains "unknown mode falls back to flow" "$out" "What"

# --- Case: corrupt file -> empty ---
data_dir="$tmp_base/corrupt/data"
mkdir -p "$data_dir"
printf '\000\001garbage-not-key-value\n' > "$data_dir/state"
out=$("$hook" --data "$data_dir" --root "$root_dir" --project "" 2>&1)
rc=$?
assert_empty "corrupt state produces no output" "$out"
assert_eq "corrupt state exits 0" 0 "$rc"

# --- Case: project overrides global ---
data_dir="$tmp_base/precedence/data"
project_dir="$tmp_base/precedence/project"
mkdir -p "$data_dir" "$project_dir/.claude"
printf 'version=1\nenabled=true\nmode=zen\n' > "$data_dir/state"
printf 'version=1\nenabled=true\nmode=clean\n' > "$project_dir/.claude/hyperfocus.state"
out=$("$hook" --data "$data_dir" --root "$root_dir" --project "$project_dir")
assert_contains "project state overrides global (clean marker present)" "$out" "quick answers"
case "$out" in
  *"Minto Pyramid"*) fail "project state overrides global (zen marker absent)" ;;
  *) pass "project state overrides global (zen marker absent)" ;;
esac

# --- hyperfocus-state: enable/set-mode/disable round-trip ---
env_data="$tmp_base/cli/data"
env_project="$tmp_base/cli/project"
mkdir -p "$env_data" "$env_project"

run_state() {
  CLAUDE_PLUGIN_DATA="$env_data" CLAUDE_PROJECT_DIR="$env_project" PLUGIN_DATA="" "$state_bin" "$@"
}

run_state enable flow >/dev/null 2>&1
rc=$?
assert_eq "state enable exits 0" 0 "$rc"
content=$(cat "$env_data/state")
assert_contains "state enable wrote enabled=true" "$content" "enabled=true"
assert_contains "state enable wrote mode=flow" "$content" "mode=flow"

run_state set-mode zen >/dev/null 2>&1
content=$(cat "$env_data/state")
assert_contains "set-mode updates mode" "$content" "mode=zen"
assert_contains "set-mode preserves enabled=true" "$content" "enabled=true"

run_state enable clean --project >/dev/null 2>&1
content=$(cat "$env_project/.claude/hyperfocus.state")
assert_contains "project enable wrote enabled=true" "$content" "enabled=true"
assert_contains "project enable wrote mode=clean" "$content" "mode=clean"

run_state disable --all >/dev/null 2>&1
global_content=$(cat "$env_data/state")
project_content=$(cat "$env_project/.claude/hyperfocus.state")
assert_contains "disable --all disables global" "$global_content" "enabled=false"
assert_contains "disable --all disables project" "$project_content" "enabled=false"

# --- hyperfocus-state: invalid mode rejected ---
run_state set-mode bogus >"$tmp_base/invalid-mode.out" 2>&1
rc=$?
assert_eq "invalid mode rejected with exit 1" 1 "$rc"

echo ""
echo "Passed: $pass_count, Failed: $fail_count"
[ "$fail_count" -eq 0 ]
