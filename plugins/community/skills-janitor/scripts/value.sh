#!/bin/bash
# Skills Janitor - Skill Value Report
# "Is each skill earning its context budget?"
# Runs usage tracking to refresh the usage data, then renders the token-cost
# table (which already cross-references with usage data). Replaces the v1.2
# split between janitor-usage and janitor-tokens.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Parse args ---
WEEKS=4
BUDGET=200000
JSON_OUTPUT=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --weeks) WEEKS="$2"; shift 2 ;;
        --budget) BUDGET="$2"; shift 2 ;;
        --json) JSON_OUTPUT=true; shift ;;
        -h|--help)
            echo "Usage: value.sh [--weeks N] [--budget N] [--json]"
            echo ""
            echo "Combined usage + token-cost view. For each installed skill, shows"
            echo "how many tokens it costs your context and whether you've used it"
            echo "in the lookback window."
            echo ""
            echo "  --weeks N   Usage lookback window (default: 4)"
            echo "  --budget N  Context window size for % calculations (default: 200000)"
            echo "  --json      Emit raw JSON instead of formatted output"
            exit 0
            ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# Refresh usage data silently — tokencost.sh reads data/usage-history.json
# that usage.sh writes. Without this, tokencost reports stale "never used"
# verdicts for skills the user has invoked since the last run.
bash "$SCRIPT_DIR/usage.sh" --weeks "$WEEKS" --json >/dev/null 2>&1 || true

# Render the token-cost table (with fresh usage data joined in)
if [[ "$JSON_OUTPUT" == "true" ]]; then
    bash "$SCRIPT_DIR/tokencost.sh" --weeks "$WEEKS" --budget "$BUDGET" --json
else
    bash "$SCRIPT_DIR/tokencost.sh" --weeks "$WEEKS" --budget "$BUDGET"
fi
