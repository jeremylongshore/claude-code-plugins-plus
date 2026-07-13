#!/usr/bin/env bash
# Shared preamble for every gate script. Sourced as the first line of every
# gate. Eliminates the per-script bug surface that Slice 1's scout-discover.sh
# already showed (empty-array failures under set -u, jq parse errors on
# malformed gh output, etc.).
#
# Per-script gate authors: source this file FIRST, then implement the gate.
# Use the helpers below for output. NEVER `echo "{...}"` your verdict directly
# — use gate_pass / gate_warn / gate_block / gate_inform.

set -euo pipefail

# Global error trap — any uncaught error dumps a BLOCK verdict + exits 0.
# (Per gate contract: exit code is always 0; runner reads stdout JSON.)
_GATE_ID="${0##*/}"
_GATE_ID="${_GATE_ID%.sh}"

_gate_err_trap() {
  local exit_code=$?
  local line_no=$1
  /usr/bin/cat <<EOF
{"severity":"BLOCK","gate":"$_GATE_ID","reason":"gate $_GATE_ID crashed at line $line_no (exit $exit_code) — fail-closed","fix_hint":"check ~/.contribute-system/check-runs/gate-debug.log; this is a bug in the gate itself"}
EOF
  exit 0
}
trap '_gate_err_trap $LINENO' ERR

# Emit a verdict and exit. Use these — never raw echo.
#
# Reason / fix_hint are JSON-escaped via jq -nc. Earlier versions used
# printf '%s' which dropped raw text into the JSON body and produced
# invalid output whenever any message contained a literal `"`. Caught by
# the e02-ai-strike-track unit tests on 2026-05-03.
gate_pass()   { jq -nc --arg g "$_GATE_ID" --arg r "${1:-ok}" '{severity:"PASS",gate:$g,reason:$r}'; exit 0; }
gate_warn()   { jq -nc --arg g "$_GATE_ID" --arg r "${1:-warning}" --arg f "${2:-}" '{severity:"WARN",gate:$g,reason:$r,fix_hint:$f}'; exit 0; }
gate_block()  { jq -nc --arg g "$_GATE_ID" --arg r "${1:-blocked}" --arg f "${2:-}" '{severity:"BLOCK",gate:$g,reason:$r,fix_hint:$f}'; exit 0; }
gate_inform() { jq -nc --arg g "$_GATE_ID" --arg r "${1:-noted}" '{severity:"INFORM",gate:$g,reason:$r}'; exit 0; }
gate_skip()   { jq -nc --arg g "$_GATE_ID" --arg r "${1:-not applicable}" '{severity:"SKIP",gate:$g,reason:$r}'; exit 0; }

# Read stdin JSON contract. Sets:
#   GATE_CANDIDATE_PATH — path to candidate .md file
#   GATE_DOSSIER_PATH — path to dossier .md (or empty if no dossier)
#   GATE_ACTION — transition name (e.g., "shortlist→claimed")
#   GATE_REPO — owner/repo
#   GATE_INPUT_JSON — raw stdin for any extra fields
gate_read_input() {
  GATE_INPUT_JSON=$(/usr/bin/cat)
  GATE_CANDIDATE_PATH=$(/usr/bin/printf '%s' "$GATE_INPUT_JSON" | jq -r '.candidate // ""')
  GATE_DOSSIER_PATH=$(/usr/bin/printf '%s' "$GATE_INPUT_JSON" | jq -r '.dossier // ""')
  GATE_ACTION=$(/usr/bin/printf '%s' "$GATE_INPUT_JSON" | jq -r '.action // ""')
  GATE_REPO=$(/usr/bin/printf '%s' "$GATE_INPUT_JSON" | jq -r '.env.repo // ""')
  export GATE_INPUT_JSON GATE_CANDIDATE_PATH GATE_DOSSIER_PATH GATE_ACTION GATE_REPO
}

# Read a frontmatter field from a markdown file. Returns empty if missing.
# Usage: val=$(fm_field /path/to/file.md "key")
fm_field() {
  local file="$1" key="$2"
  [[ -f "$file" ]] || { /usr/bin/printf ''; return; }
  /usr/bin/awk -v k="$key" '
    /^---$/ { fm = !fm ? 1 : 2; next }
    fm == 1 && $0 ~ "^"k":" {
      sub("^"k":[[:space:]]*", "")
      gsub(/^"|"$/, "")
      print
      exit
    }
  ' "$file"
}

# gh wrapper with bounded retry.
#
# Constraint: gate-runner enforces a 10s wall-clock timeout per gate. gh_safe
# must finish well under that to leave room for jq/awk downstream.
# Tuning: 2 attempts, 0.5s sleep between, 4s per-call timeout.
# Worst case ≈ 4 + 0.5 + 4 = 8.5s — leaves headroom.
#
# Permanent 404s (issue/repo doesn't exist) fail on the first call's HTTP error
# and don't usefully retry. Transient blips get one retry. That's enough for
# the read-only gh queries gates make.
#
# On final failure returns non-zero with empty stdout — caller decides what
# missing data means (usually `gate_pass`/`gate_inform`/`gate_skip`).
gh_safe() {
  local attempt=1 max=2
  while (( attempt <= max )); do
    if /usr/bin/timeout 4 gh "$@" 2>/dev/null; then return 0; fi
    /usr/bin/sleep 0.5
    attempt=$(( attempt + 1 ))
  done
  return 1
}

# Helper: log a gate run for observability. Append-only.
gate_log_run() {
  local verdict="$1"
  /usr/bin/printf '%s\n' "$(jq -nc \
    --arg ts "$(/usr/bin/date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg gate "$_GATE_ID" \
    --arg action "$GATE_ACTION" \
    --arg repo "$GATE_REPO" \
    --arg verdict "$verdict" \
    '{ts: $ts, event: "gate_run", details: {gate: $gate, action: $action, repo: $repo, verdict: $verdict}}')" \
    >> ~/.contribute-system/log.jsonl 2>/dev/null || true
}
