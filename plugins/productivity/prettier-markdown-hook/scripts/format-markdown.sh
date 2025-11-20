#!/usr/bin/env bash
# Prettier Markdown Formatting Stop Hook v2.0.0
# Formats all .md files in workspace when Claude stops responding
# Auto-commits with optional AI-generated messages (opt-in)
# Uses fire-and-forget pattern for async execution (< 10ms exit)
#
# Configuration: ~/.prettierrc-hook.json (JSON with jq parser)
# Environment Variables:
#   PRETTIER_CONFIG         - Config file location (default: ~/.prettierrc-hook.json)
#   PRETTIER_ENABLE_AI_COMMITS - Enable AI commit messages (default: unset/disabled)
#   PRETTIER_LOG_DIR        - Log directory override
#   PRETTIER_DEBUG          - Enable debug logging (default: unset/disabled)

set -euo pipefail

# ============================================================================
# Configuration & Environment
# ============================================================================

# Get workspace directory from Claude Code environment
workspace_dir="${CLAUDE_WORKSPACE_DIR:-$(pwd)}"

# Config file location
CONFIG_FILE="${PRETTIER_CONFIG:-$HOME/.prettierrc-hook.json}"

# Default log directory (XDG-compliant)
DEFAULT_LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/prettier-hook"

# ============================================================================
# Logging Functions
# ============================================================================

log_error() {
    local message="$1"
    local log_dir="${PRETTIER_LOG_DIR:-$DEFAULT_LOG_DIR}"
    mkdir -p "$log_dir"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $message" >> "$log_dir/errors.log"
}

log_info() {
    local message="$1"
    if [[ -n "${PRETTIER_DEBUG:-}" ]]; then
        local log_dir="${PRETTIER_LOG_DIR:-$DEFAULT_LOG_DIR}"
        mkdir -p "$log_dir"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $message" >> "$log_dir/prettier-hook.log"
    fi
}

log_warn() {
    local message="$1"
    local log_dir="${PRETTIER_LOG_DIR:-$DEFAULT_LOG_DIR}"
    mkdir -p "$log_dir"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $message" >> "$log_dir/prettier-hook.log"
}

# ============================================================================
# Phase 1: Dependency Validation
# ============================================================================

check_dependencies() {
    local missing_deps=()

    # Check required dependencies
    for cmd in prettier jq git; do
        if ! command -v "$cmd" &>/dev/null; then
            missing_deps+=("$cmd")
            log_error "Missing required dependency: $cmd"
        fi
    done

    # Exit if any critical dependencies missing
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Cannot proceed: missing dependencies: ${missing_deps[*]}"
        exit 1
    fi

    log_info "All dependencies validated: prettier, jq, git"
}

# ============================================================================
# Phase 2: Configuration Loading System
# ============================================================================

load_config() {
    # Initialize defaults
    EXCLUDE_ORGS=()
    EXCLUDE_PATHS=()
    LOG_DIR="$DEFAULT_LOG_DIR"
    ENABLE_AI_COMMITS=false

    # Built-in default exclusions (always applied)
    DEFAULT_EXCLUDES=(
        "node_modules"
        ".git"
        ".github"
        ".claude/skills"
        "skills"
        "plugins"
        "file-history"
    )

    log_info "Loading config from: $CONFIG_FILE"

    # Load from config file if exists and is valid JSON
    if [[ -f "$CONFIG_FILE" ]]; then
        if jq empty "$CONFIG_FILE" &>/dev/null; then
            # Parse excludeOrgs array
            while IFS= read -r org; do
                EXCLUDE_ORGS+=("$org")
            done < <(jq -r '.excludeOrgs[]? // empty' "$CONFIG_FILE" 2>/dev/null)

            # Parse excludePaths array
            while IFS= read -r path; do
                EXCLUDE_PATHS+=("$path")
            done < <(jq -r '.excludePaths[]? // empty' "$CONFIG_FILE" 2>/dev/null)

            # Parse logDir (if set)
            local config_log_dir
            config_log_dir=$(jq -r '.logDir // empty' "$CONFIG_FILE" 2>/dev/null)
            if [[ -n "$config_log_dir" ]]; then
                # Expand tilde if present
                LOG_DIR="${config_log_dir/#\~/$HOME}"
            fi

            log_info "Config loaded: ${#EXCLUDE_ORGS[@]} org exclusions, ${#EXCLUDE_PATHS[@]} path exclusions"
        else
            log_warn "Config file invalid JSON, using defaults: $CONFIG_FILE"
        fi
    else
        log_info "No config file found, using defaults"
    fi

    # Environment variable overrides (highest priority)
    if [[ -n "${PRETTIER_ENABLE_AI_COMMITS:-}" ]]; then
        ENABLE_AI_COMMITS=true
        log_info "AI commits enabled via PRETTIER_ENABLE_AI_COMMITS"
    fi

    if [[ -n "${PRETTIER_LOG_DIR:-}" ]]; then
        LOG_DIR="$PRETTIER_LOG_DIR"
        log_info "Log directory overridden via PRETTIER_LOG_DIR: $LOG_DIR"
    fi

    # Combine default + custom exclusions (additive pattern)
    ALL_EXCLUDES=("${DEFAULT_EXCLUDES[@]}" "${EXCLUDE_PATHS[@]}")
}

# ============================================================================
# Phase 3: Workspace Exclusion Detection (Refactored)
# ADR: docs/decisions/0001-prettier-workspace-exclusion.md
# ============================================================================

is_excluded_workspace() {
    local workspace="$1"

    # Check if git repository
    if ! git -C "$workspace" rev-parse --git-dir > /dev/null 2>&1; then
        # Not git repo - not excluded, run prettier
        return 1
    fi

    # Get git remote origin URL
    local remote_url
    remote_url=$(git -C "$workspace" config --get remote.origin.url 2>/dev/null)

    if [[ -z "$remote_url" ]]; then
        # No remote - local repo, not excluded, run prettier
        return 1
    fi

    # Check against configured organization exclusions
    for org in "${EXCLUDE_ORGS[@]}"; do
        if [[ "$remote_url" =~ github\.com[:/]$org/ ]]; then
            log_info "Workspace excluded: $org matches $remote_url"
            return 0  # EXCLUDED
        fi
    done

    return 1  # Not excluded - run prettier
}

# ============================================================================
# Initialization: Check dependencies and load config
# ============================================================================

check_dependencies
load_config

# ============================================================================
# Workspace Exclusion Check
# ============================================================================

if is_excluded_workspace "$workspace_dir"; then
    # Log skip decision for observability
    {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Skipping prettier - workspace excluded"
        echo "  Workspace: $workspace_dir"
        git -C "$workspace_dir" config --get remote.origin.url 2>/dev/null | \
            sed 's/^/  Remote: /'
    } >> "$LOG_DIR/prettier-skip.log" 2>&1

    exit 0  # Skip silently
fi

# ============================================================================
# Phase 4-6: Async Formatting + Commit (Fire-and-forget pattern)
# ============================================================================

{
    # Build find exclusion arguments
    find_excludes=""
    for pattern in "${ALL_EXCLUDES[@]}"; do
        find_excludes="$find_excludes -not -path '*/$pattern/*'"
    done

    # Step 1: Run prettier formatting on workspace files
    # Phase 4: Removed /tmp formatting - workspace only
    # Phase 6: Using configurable exclusions (defaults + config)
    eval "find \"$workspace_dir\" -type f -name '*.md' $find_excludes -exec prettier --write --prose-wrap preserve {} \\; 2>/dev/null"

    # Step 2: Check if prettier made any changes
    cd "$workspace_dir" 2>/dev/null || exit 0

    # Only proceed if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        exit 0
    fi

    # Check for modified markdown files (all subdirectories)
    if git diff --quiet -- '*.md' '**/*.md' 2>/dev/null; then
        # No changes - exit silently
        exit 0
    fi

    # Step 3: Stage formatting changes (all subdirectories)
    git add -- '*.md' '**/*.md' 2>/dev/null || exit 0

    # Count and list changed files
    changed_files=$(git diff --cached --name-only -- '*.md' '**/*.md' 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$changed_files" -eq 0 ]]; then
        exit 0
    fi

    # Get concise diff summary (first 50 lines to avoid token limits)
    diff_summary=$(git diff --cached --stat -- '*.md' '**/*.md' 2>/dev/null | head -50)
    file_list=$(git diff --cached --name-only -- '*.md' '**/*.md' 2>/dev/null)

    # ========================================================================
    # Phase 5: AI Commit Generation (Opt-In)
    # ========================================================================

    if [[ "$ENABLE_AI_COMMITS" == "true" ]] && command -v claude &>/dev/null && command -v timeout &>/dev/null; then
        # Generate AI commit message using Claude Code headless mode (Haiku model)
        commit_prompt="DISABLE_INTERLEAVED_THINKING

Generate a git commit message for these prettier formatting changes.

Files changed: $changed_files
$file_list

Diff summary:
$diff_summary

CRITICAL: Output ONLY the raw commit message text. Do NOT include:
- No introductory text like 'Here is the commit message:'
- No code blocks or backticks
- No explanations or commentary
- Just the commit message itself

Format:
Line 1: <type>: <summary> (50 chars max)
Line 2: (blank)
Line 3+: optional body (72 chars per line)

Use type: chore, docs, or style

Example output (copy this format exactly):
style: format markdown files with prettier

Standardized formatting for $changed_files file(s)."

        # Invoke Claude Code in headless mode using Haiku (cheapest model)
        commit_message=$(timeout 30 claude -p "$commit_prompt" \
            --model claude-haiku-4-5-20251001 \
            --output-format text \
            --allowedTools "Read" 2>/dev/null | \
            # Clean up output: remove common preambles and code blocks
            grep -v -E '^(Here|Based on|The commit|```|$)' | \
            head -10 || echo "")

        # Validate AI-generated message
        if [[ -z "$commit_message" ]] || [[ ${#commit_message} -lt 10 ]]; then
            commit_message=""  # Fall through to generic message
        fi
    fi

    # Use generic message if AI disabled or failed
    if [[ -z "${commit_message:-}" ]]; then
        commit_message="style: format markdown files with prettier

Automated formatting of $changed_files markdown file(s) by prettier hook."
    fi

    # Step 5: Commit with AI-generated or generic message
    git commit -m "$commit_message" 2>/dev/null || true

} > /dev/null 2>&1 &

# Exit immediately - don't wait for background process
exit 0
