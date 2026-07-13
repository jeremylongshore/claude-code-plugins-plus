#!/bin/bash
# Skills Janitor - Skill Discovery
# Dispatches to search.sh (find skills on GitHub) or precheck.sh (analyze a
# specific skill URL/path before installing) based on argument shape.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

show_help() {
    cat <<'EOF'
Usage: discover.sh <query-or-url> [options]

Discovery mode (find skills on GitHub):
  discover.sh seo                       Search GitHub for "seo" skills
  discover.sh n8n --limit 20            Top 20 matches
  discover.sh --compare <skill-name>    Compare a local skill against alternatives

Pre-install mode (check before installing a known skill):
  discover.sh https://github.com/user/skill     Check this skill for overlap
  discover.sh user/skill                        Short-form GitHub repo
  discover.sh ~/path/to/local-skill             Check local folder

Options forwarded to search.sh:
  --limit N    Cap results (default: 10)
  --json       Emit raw JSON

Options forwarded to precheck.sh:
  --json       Emit raw JSON
EOF
}

# Detect arg shape and dispatch
if [[ $# -eq 0 ]]; then
    show_help
    exit 1
fi

first_arg="$1"
case "$first_arg" in
    -h|--help)
        show_help
        exit 0
        ;;
    --compare)
        # Compare mode is a search.sh feature
        exec bash "$SCRIPT_DIR/search.sh" "$@"
        ;;
    http://*|https://*|*github.com/*)
        exec bash "$SCRIPT_DIR/precheck.sh" "$@"
        ;;
    /*|~/*|./*)
        # Local path
        exec bash "$SCRIPT_DIR/precheck.sh" "$@"
        ;;
    */*)
        # Short-form GitHub repo (user/skill) — turn into a full URL for precheck
        url="https://github.com/$first_arg"
        shift
        exec bash "$SCRIPT_DIR/precheck.sh" "$url" "$@"
        ;;
    *)
        # Keyword search
        exec bash "$SCRIPT_DIR/search.sh" "$@"
        ;;
esac
