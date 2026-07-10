#!/usr/bin/env bash
#
# verify-downstreams.sh — check the RELEASING.md §3 dependents registry against
# the local manifest version.
#
# For every checkable row (vendored marketplace copies, doctrine embeds) the
# script queries the downstream's recorded hyperflow version via read-only
# `gh api` calls and prints a DEPENDENT | EXPECTED | ACTUAL | STATUS table.
# Rows with no sync contract (transitive mirrors, hand-vendored snapshots,
# self-healing doctrine embeds) are listed as INFO and never gate.
#
# Exit codes:
#   0 — nothing stale, or gh/network unavailable (check skipped with a warning)
#   1 — at least one checkable row is STALE
#   2 — usage / local-parse error
#
# Usage: ./scripts/verify-downstreams.sh [--json]
#   --json   machine-readable output (same exit-code semantics)
#
# The registry array below mirrors RELEASING.md §3 — keep the two in sync when
# a dependent is added or retired. Remediation stays human (unfreeze PRs,
# /hyperflow:bridge refresh); this script only reports.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Colors (match release.sh; disabled when stdout is not a tty) ─────────────
if [[ -t 1 ]]; then
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  YELLOW='\033[1;33m'
  CYAN='\033[0;36m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; CYAN=''; BOLD=''; RESET=''
fi

# Per-call timeout for gh queries (seconds); override with HYPERFLOW_GH_TIMEOUT.
GH_TIMEOUT="${HYPERFLOW_GH_TIMEOUT:-15}"

# ── Args ──────────────────────────────────────────────────────────────────────
JSON_MODE=false
for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    -h|--help)
      cat <<'USAGE'
Usage: ./scripts/verify-downstreams.sh [--json]

Checks every dependent in the RELEASING.md section-3 registry against the
local manifest version (package.json) using read-only gh api queries.

  --json   emit machine-readable JSON instead of the table

Exit codes: 0 = fresh or check skipped (no gh / no network), 1 = stale row
found, 2 = usage or local-parse error.
USAGE
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Try '$0 --help'" >&2
      exit 2
      ;;
  esac
done

# ── Registry (mirror of RELEASING.md §3 — copy dependent names exactly) ──────
# Format: name|method|repo|path|remediation
#   vendored-manifest  → gh: read the vendored .claude-plugin/plugin.json version
#   doctrine-remote    → gh: read the hyperflow:doctrine:start version marker
#   doctrine-local     → local file: same marker, no network needed
#   info               → no sync contract; listed for completeness, never gates
REGISTRY=(
  'jeremylongshore/claude-code-plugins-plus-skills|vendored-manifest|jeremylongshore/claude-code-plugins-plus-skills|plugins/ai-agency/hyperflow/.claude-plugin/plugin.json|Open the unfreeze PR from RELEASING.md section 3 (drop curated: true in their sources.yaml), or a courtesy resync issue'
  'Mohammed-Abdelhady/forgepath|doctrine-remote|Mohammed-Abdelhady/forgepath|CLAUDE.md|Run /hyperflow:bridge refresh in that repo and commit'
  "this repo's own CLAUDE.md|doctrine-local||CLAUDE.md|Auto-refreshed by release.sh — if stale, the doctrine content changed without the block being re-stamped: run python3 scripts/auto-bridge.py . . and commit"
  'gabrielmoreira/agent-skills-mirror|info|||Transitive daily mirror — inherits automatically once the upstream marketplace resyncs'
  'kota-kawa/Marmo-Core + TuYv/ccpm|info|||Hand-vendored third-hand snapshots — no sync contract to honor'
  'crossaitools.com|info|||Community directory — follows the marketplaces it crawls'
  'third-party CLAUDE.md doctrine embeds|info|||Self-healing — auto-bridge refreshes the block on their next session'
  'caissonhq/forgebench|info|||Historical reference only'
)

# ── Helpers ───────────────────────────────────────────────────────────────────
warn() {
  echo -e "${YELLOW}⚠  $1${RESET}" >&2
}

json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  printf '%s' "$s"
}

# Graceful degradation — a release must never hard-depend on network/gh.
skip_out() {
  if [[ "$JSON_MODE" == "true" ]]; then
    printf '{"skipped":true,"reason":"%s","expected":"%s","rows":[]}\n' \
      "$(json_escape "$1")" "$(json_escape "$EXPECTED")"
  else
    warn "downstream check skipped — $1"
  fi
  exit 0
}

# Portable per-call timeout: coreutils timeout, gtimeout, or a perl alarm.
with_timeout() {
  local secs="$1"
  shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$secs" "$@"
  elif command -v perl >/dev/null 2>&1; then
    perl -e 'alarm shift; exec @ARGV' "$secs" "$@"
  else
    "$@"
  fi
}

ERRFILE="$(mktemp)"
trap 'rm -f "$ERRFILE"' EXIT

# Fetch one file from a GitHub repo (read-only) and decode it to stdout.
gh_file() {
  local raw
  if ! raw=$(with_timeout "$GH_TIMEOUT" gh api "repos/$1/contents/$2" --jq '.content' 2>"$ERRFILE"); then
    return 1
  fi
  printf '%s\n' "$raw" | base64 -d 2>/dev/null
}

# Version extractors (read stdin, print the version or nothing).
manifest_version() {
  grep '"version"' | head -1 | sed 's/.*"version": *"\([^"]*\)".*/\1/'
}

doctrine_version() {
  grep -o 'hyperflow:doctrine:start version=[0-9][0-9.]*' | head -1 | sed 's/.*version=//'
}

# A doctrine block is invalidated by its CONTENT, not its version label: auto-bridge
# deliberately leaves a block untouched when the body-sha matches, "even if the
# version label differs" (scripts/auto-bridge.py, S7 freshness check). Comparing
# version labels here would therefore report every doctrine embed as STALE on any
# version-only release. Compare the body-sha instead.
doctrine_body_sha() {
  grep -o 'hyperflow:doctrine:start[^>]*body-sha=[0-9a-f]*' | head -1 | sed 's/.*body-sha=//'
}

print_row() {
  local color=''
  case "$5" in
    FRESH) color="$GREEN" ;;
    STALE) color="$RED" ;;
    ERROR) color="$YELLOW" ;;
    INFO)  color="$CYAN" ;;
  esac
  printf '%-48s %-8s %-14s %-14s %b\n' "$1" "$2" "$3" "$4" "${color}$5${RESET}"
}

# ── Expected version = local manifest (single source of truth) ───────────────
EXPECTED=$(grep '"version"' "$ROOT/package.json" | head -1 \
  | sed 's/.*"version": *"\([^"]*\)".*/\1/' || true)
if [[ -z "$EXPECTED" ]]; then
  echo "Error: could not parse version from $ROOT/package.json" >&2
  exit 2
fi

# Ask auto-bridge for the template's body-sha rather than recomputing it here —
# a second implementation could disagree, and a freshness check that disagrees
# with the thing it checks is worse than no check.
EXPECTED_BODY_SHA=''
if command -v python3 >/dev/null 2>&1 && [[ -f "$ROOT/scripts/auto-bridge.py" ]]; then
  EXPECTED_BODY_SHA=$(python3 "$ROOT/scripts/auto-bridge.py" --body-sha "$ROOT" 2>/dev/null || true)
fi

# ── Pre-flight: no gh binary or no reachable API → skip cleanly ──────────────
if ! command -v gh >/dev/null 2>&1; then
  skip_out "gh CLI not found (install: brew install gh)"
fi
if ! with_timeout "$GH_TIMEOUT" gh api rate_limit >/dev/null 2>&1; then
  skip_out "GitHub API unreachable (no network, or gh not authenticated)"
fi

# ── Walk the registry ─────────────────────────────────────────────────────────
STALE_COUNT=0
ROWS_JSON=''
STALE_NOTES=()

if [[ "$JSON_MODE" != "true" ]]; then
  echo -e "${BOLD}Downstream dependents — expected hyperflow v${EXPECTED}${RESET}"
  echo -e "${CYAN}basis=version compares a vendored plugin copy; basis=content compares a doctrine block's body-sha${RESET}"
  printf '%-48s %-8s %-14s %-14s %s\n' 'DEPENDENT' 'BASIS' 'EXPECTED' 'ACTUAL' 'STATUS'
fi

for row in "${REGISTRY[@]}"; do
  IFS='|' read -r name method repo path note <<< "$row"
  expected="$EXPECTED"
  basis='version'
  actual=''
  status=''
  err=''
  content=''

  case "$method" in
    vendored-manifest)
      # A vendored copy of the plugin genuinely lags by version — compare versions.
      if content=$(gh_file "$repo" "$path"); then
        actual=$(printf '%s\n' "$content" | manifest_version || true)
      else
        err=$(head -c 200 "$ERRFILE" | tr '\n' ' ')
      fi
      ;;
    doctrine-remote)
      if content=$(gh_file "$repo" "$path"); then
        actual=$(printf '%s\n' "$content" | doctrine_body_sha || true)
        if [[ -n "$actual" && -n "$EXPECTED_BODY_SHA" ]]; then
          basis='content'
          expected="$EXPECTED_BODY_SHA"
        else
          # Legacy block predating body-sha, or no local template to hash — fall
          # back to the version label, exactly as auto-bridge does.
          actual=$(printf '%s\n' "$content" | doctrine_version || true)
        fi
      else
        err=$(head -c 200 "$ERRFILE" | tr '\n' ' ')
      fi
      ;;
    doctrine-local)
      if [[ -f "$ROOT/$path" ]]; then
        actual=$(doctrine_body_sha < "$ROOT/$path" || true)
        if [[ -n "$actual" && -n "$EXPECTED_BODY_SHA" ]]; then
          basis='content'
          expected="$EXPECTED_BODY_SHA"
        else
          actual=$(doctrine_version < "$ROOT/$path" || true)
        fi
      else
        err="local file $path not found"
      fi
      ;;
    info)
      status='INFO'
      basis='-'
      expected='-'
      actual='-'
      ;;
  esac

  if [[ -z "$status" ]]; then
    if [[ -n "$err" ]]; then
      status='ERROR'
      actual='?'
    elif [[ -z "$actual" ]]; then
      status='ERROR'
      err='could not parse a hyperflow version from the fetched file'
      actual='?'
    elif [[ "$actual" == "$expected" ]]; then
      status='FRESH'
    else
      status='STALE'
      STALE_COUNT=$((STALE_COUNT + 1))
    fi
  fi

  # Enrich the marketplace row: is the vendored copy still frozen upstream?
  if [[ "$method" == 'vendored-manifest' && "$status" == 'STALE' ]]; then
    if yaml=$(gh_file "$repo" 'sources.yaml'); then
      if printf '%s\n' "$yaml" | grep -A14 'name: hyperflow' | grep -q 'curated: true'; then
        note="Still frozen (curated: true). $note"
      else
        note="Unfrozen — their pipeline should pick up new releases on its next sync. $note"
      fi
    fi
  fi

  if [[ "$status" == 'STALE' ]]; then
    STALE_NOTES+=("$name → $note")
  fi

  if [[ "$JSON_MODE" == "true" ]]; then
    [[ -n "$ROWS_JSON" ]] && ROWS_JSON+=','
    ROWS_JSON+=$(printf '{"name":"%s","basis":"%s","expected":"%s","actual":"%s","status":"%s","error":"%s","action":"%s"}' \
      "$(json_escape "$name")" "$(json_escape "$basis")" "$(json_escape "$expected")" \
      "$(json_escape "$actual")" "$(json_escape "$status")" "$(json_escape "$err")" \
      "$(json_escape "$note")")
  else
    print_row "$name" "$basis" "$expected" "$actual" "$status"
    if [[ "$status" == 'ERROR' && -n "$err" ]]; then
      printf '   %b↳ %s%b\n' "$YELLOW" "$err" "$RESET"
    fi
  fi
done

# ── Report ────────────────────────────────────────────────────────────────────
if [[ "$JSON_MODE" == "true" ]]; then
  printf '{"skipped":false,"expected":"%s","checked_at":"%s","stale_count":%d,"rows":[%s]}\n' \
    "$(json_escape "$EXPECTED")" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$STALE_COUNT" "$ROWS_JSON"
else
  echo ""
  if [[ "$STALE_COUNT" -gt 0 ]]; then
    echo -e "${RED}${BOLD}${STALE_COUNT} downstream(s) STALE${RESET} — remediation (see RELEASING.md section 3):"
    for line in "${STALE_NOTES[@]}"; do
      printf '   %s\n' "$line"
    done
  else
    echo -e "${GREEN}All checkable downstreams are fresh (v${EXPECTED}).${RESET}"
  fi
fi

if [[ "$STALE_COUNT" -gt 0 ]]; then
  exit 1
fi
exit 0
