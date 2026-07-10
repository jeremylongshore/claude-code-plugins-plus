#!/usr/bin/env bash

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Resolve script and project root ───────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || pwd)"

# ── Defaults ──────────────────────────────────────────────────────────────────
TOOLS="all"
FORCE=false
DRY_RUN=false

# ── Valid tool names ───────────────────────────────────────────────────────────
VALID_TOOLS="claude-code opencode codex agents antigravity cursor grok all"

# ── Usage ─────────────────────────────────────────────────────────────────────
usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] [TARGET_DIR]

Generate hyperflow auto-detection shim files at the project root so AI coding
tools can discover and load hyperflow conventions automatically.

OPTIONS:
  --tools <list>   Comma-separated tools to set up (default: all)
                   Valid values: claude-code, opencode, codex, agents, antigravity, cursor, grok, all
                     claude-code  — writes CLAUDE.md (append mode)
                     opencode     — writes AGENTS.md
                     codex        — writes AGENTS.md
                     agents       — writes AGENTS.md (alias for opencode)
                     antigravity  — writes AGENTS.md + .agent/workflows/hyperflow* slash commands
                     cursor       — writes AGENTS.md (Cursor reads it natively)
                     grok         — writes AGENTS.md + .grok/rules/hyperflow.md
                     all          — claude-code + opencode + codex + agents + antigravity + cursor + grok
  --force          Overwrite existing files (default: skip with warning)
  --dry-run        Print what would be created without writing files
  --help           Show this help message

EXAMPLES:
  $(basename "$0")
  $(basename "$0") --tools opencode
  $(basename "$0") --tools codex
  $(basename "$0") --tools all --force
  $(basename "$0") --dry-run
EOF
}

# ── Argument parsing ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tools)
      [[ $# -lt 2 ]] && { echo -e "${RED}✗ --tools requires a value${RESET}"; exit 1; }
      TOOLS="$2"; shift 2 ;;
    --force)
      FORCE=true; shift ;;
    --dry-run)
      DRY_RUN=true; shift ;;
    --help|-h)
      usage; exit 0 ;;
    -*)
      echo -e "${RED}✗ Unknown option: $1${RESET}"; usage; exit 1 ;;
    *)
      # Positional: treat as target directory override
      ROOT="$1"; shift ;;
  esac
done

# ── Validate tool list ────────────────────────────────────────────────────────
validate_tools() {
  local raw="$1"
  IFS=',' read -ra requested <<< "$raw"
  for t in "${requested[@]}"; do
    t="${t// /}"  # strip spaces
    local found=false
    for v in $VALID_TOOLS; do
      [[ "$t" == "$v" ]] && found=true && break
    done
    if [[ "$found" == false ]]; then
      echo -e "${RED}✗ Invalid tool: '$t'. Valid values: ${VALID_TOOLS// /, }${RESET}"
      exit 1
    fi
  done
}

validate_tools "$TOOLS"

# ── Tool inclusion check ──────────────────────────────────────────────────────
wants_tool() {
  local tool="$1"
  [[ "$TOOLS" == "all" ]] && return 0
  IFS=',' read -ra list <<< "$TOOLS"
  for t in "${list[@]}"; do
    t="${t// /}"
    [[ "$t" == "$tool" ]] && return 0
  done
  return 1
}

# ── Derived flags per file ────────────────────────────────────────────────────
need_agents_md=false
need_claude_md=false
need_antigravity=false
need_grok_rules=false

wants_tool "opencode"    && need_agents_md=true
wants_tool "codex"       && need_agents_md=true
wants_tool "agents"      && need_agents_md=true
wants_tool "claude-code" && need_claude_md=true
wants_tool "antigravity" && need_antigravity=true
wants_tool "antigravity" && need_agents_md=true   # Antigravity also reads AGENTS.md
wants_tool "cursor"      && need_agents_md=true   # Cursor reads AGENTS.md natively
wants_tool "grok"        && need_agents_md=true   # Grok loads AGENTS.md
wants_tool "grok"        && need_grok_rules=true

# ── Template directory ────────────────────────────────────────────────────────
TEMPLATE_DIR="$SCRIPT_DIR/../templates"

# ── Bug 1 fix: render_template substitutes ${HYPERFLOW_VERSION}, ${PROJECT_NAME}, ${DATE} ──
render_template() {
  local tpl="$1"
  HYPERFLOW_VERSION="${HYPERFLOW_VERSION:-$(cat "$SCRIPT_DIR/../skills/hyperflow/VERSION" 2>/dev/null || echo "unknown")}"
  PROJECT_NAME="${PROJECT_NAME:-$(basename "$ROOT")}"
  DATE="$(date +%Y-%m-%d)"

  if command -v envsubst >/dev/null 2>&1; then
    HYPERFLOW_VERSION="$HYPERFLOW_VERSION" PROJECT_NAME="$PROJECT_NAME" DATE="$DATE" \
      envsubst '${HYPERFLOW_VERSION} ${PROJECT_NAME} ${DATE}' < "$tpl"
  else
    sed -e "s|\${HYPERFLOW_VERSION}|$HYPERFLOW_VERSION|g" \
        -e "s|\${PROJECT_NAME}|$PROJECT_NAME|g" \
        -e "s|\${DATE}|$DATE|g" \
        "$tpl"
  fi
}

# ── Shim body (fallback when template file is absent) ────────────────────────
_fallback_shim_body() {
  local version
  version="${HYPERFLOW_VERSION:-$(cat "$SCRIPT_DIR/../skills/hyperflow/VERSION" 2>/dev/null || echo "unknown")}"
  cat <<EOF
## Hyperflow

This project uses hyperflow for autonomous multi-agent orchestration.

On session start, invoke the \`hyperflow\` skill (or follow \`~/.hyperflow/config.json\` if present).

### Context files

- \`.hyperflow/profile.md\` — project profile
- \`.hyperflow/architecture.md\` — folder structure
- \`.hyperflow/conventions.md\` — coding conventions
- \`.hyperflow/memory/index.md\` — persistent learnings index
- \`.hyperflow/tasks/\` — in-progress task state
EOF
}

# ── Template loader (falls back to embedded heredoc) ─────────────────────────
load_template() {
  local tpl_file="$TEMPLATE_DIR/$1"
  if [[ -f "$tpl_file" ]]; then
    render_template "$tpl_file"
  else
    _fallback_shim_body
  fi
}

# ── File write helper ─────────────────────────────────────────────────────────
CREATED_FILES=()

write_file() {
  local path="$1"
  local content="$2"

  if [[ "$DRY_RUN" == true ]]; then
    echo -e "${BLUE}==> [dry-run] Would write: ${path}${RESET}"
    CREATED_FILES+=("$path")
    return
  fi

  if [[ -f "$path" ]] && [[ "$FORCE" == false ]]; then
    echo -e "${YELLOW}⚠  Already exists (skipping): ${path}${RESET}"
    return
  fi

  local dir
  dir="$(dirname "$path")"
  [[ -d "$dir" ]] || mkdir -p "$dir"

  printf '%s\n' "$content" > "$path"
  echo -e "${GREEN}✓  Written: ${path}${RESET}"
  CREATED_FILES+=("$path")
}

# ── Claude Code: append-or-create logic ───────────────────────────────────────
write_claude_md() {
  local path="$ROOT/CLAUDE.md"
  # Bug 1+marker fix: embed version in start marker; shell is single source
  local version
  version="${HYPERFLOW_VERSION:-$(cat "$SCRIPT_DIR/../skills/hyperflow/VERSION" 2>/dev/null || echo "unknown")}"
  local start_marker="<!-- hyperflow-shim-start v${version} -->"
  local end_marker="<!-- hyperflow-shim-end -->"
  # Bug 2 fix: template has no markers; shell adds them exactly once
  local section
  section="$(load_template "CLAUDE.md.template")"

  local block
  block="${start_marker}
${section}
${end_marker}"

  if [[ "$DRY_RUN" == true ]]; then
    if [[ -f "$path" ]]; then
      echo -e "${BLUE}==> [dry-run] Would append hyperflow section to: ${path}${RESET}"
    else
      echo -e "${BLUE}==> [dry-run] Would create: ${path}${RESET}"
    fi
    CREATED_FILES+=("$path")
    return
  fi

  if [[ -f "$path" ]]; then
    # Check if shim already present (prefix match handles version-embedded marker)
    if grep -q "hyperflow-shim-start" "$path"; then
      if [[ "$FORCE" == false ]]; then
        echo -e "${YELLOW}⚠  Hyperflow section already present in ${path} (skipping — use --force to update)${RESET}"
        return
      fi
      # Bug 3 fix: correct awk strips lines between markers (inclusive) without leaving stale end-marker
      local tmpfile
      tmpfile="$(mktemp)"
      awk -v s="hyperflow-shim-start" -v e="hyperflow-shim-end" '
        index($0,s){skip=1; next}
        skip && index($0,e){skip=0; next}
        !skip{print}
      ' "$path" > "$tmpfile"
      mv "$tmpfile" "$path"
      echo -e "${BLUE}==> Replacing existing hyperflow section in ${path}${RESET}"
    fi
    printf '\n%s\n' "$block" >> "$path"
    echo -e "${GREEN}✓  Appended hyperflow section to: ${path}${RESET}"
  else
    printf '%s\n' "$block" > "$path"
    echo -e "${GREEN}✓  Created: ${path}${RESET}"
  fi
  CREATED_FILES+=("$path")
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  echo -e "${BOLD}==> Hyperflow detection shim setup${RESET}"
  echo -e "    Project root: ${ROOT}"
  echo -e "    Tools:        ${TOOLS}"
  [[ "$FORCE"   == true ]] && echo -e "    Mode:         force (overwrite)"
  [[ "$DRY_RUN" == true ]] && echo -e "    Mode:         dry-run"
  echo ""

  # AGENTS.md — OpenCode / Codex / Cursor / Grok / Antigravity
  if [[ "$need_agents_md" == true ]]; then
    echo -e "${BLUE}==> AGENTS.md (OpenCode / Codex / Cursor / Grok)${RESET}"
    write_file "$ROOT/AGENTS.md" "$(load_template "AGENTS.md.template")"
  fi

  # CLAUDE.md — Claude Code (append mode)
  if [[ "$need_claude_md" == true ]]; then
    echo -e "${BLUE}==> CLAUDE.md (Claude Code)${RESET}"
    write_claude_md
  fi

  # .agent/workflows — Antigravity slash commands (/hyperflow*)
  if [[ "$need_antigravity" == true ]]; then
    echo -e "${BLUE}==> .agent/workflows (Antigravity)${RESET}"
    local wf_src="$TEMPLATE_DIR/antigravity/workflows"
    if [[ -d "$wf_src" ]]; then
      mkdir -p "$ROOT/.agent/workflows"
      local wf
      for wf in "$wf_src"/*.md; do
        [[ -f "$wf" ]] || continue
        write_file "$ROOT/.agent/workflows/$(basename "$wf")" "$(cat "$wf")"
      done
    else
      echo -e "${YELLOW}  antigravity workflow templates not found at $wf_src${RESET}"
    fi
  fi

  # .grok/rules — Grok project rules
  if [[ "$need_grok_rules" == true ]]; then
    echo -e "${BLUE}==> .grok/rules (Grok)${RESET}"
    local grok_tpl="$TEMPLATE_DIR/grok-rules/hyperflow.md"
    if [[ -f "$grok_tpl" ]]; then
      mkdir -p "$ROOT/.grok/rules"
      write_file "$ROOT/.grok/rules/hyperflow.md" "$(render_template "$grok_tpl")"
    else
      echo -e "${YELLOW}  grok rules template not found at $grok_tpl${RESET}"
    fi
  fi

  echo ""
  if [[ "${#CREATED_FILES[@]}" -gt 0 ]]; then
    local file_list
    file_list="$(IFS=', '; echo "${CREATED_FILES[*]}" | sed "s|${ROOT}/||g")"
    if [[ "$DRY_RUN" == true ]]; then
      echo -e "${BOLD}Hyperflow detection shims would be created:${RESET} ${file_list}"
    else
      echo -e "${BOLD}${GREEN}Hyperflow detection shims created:${RESET} ${file_list}"
    fi
  else
    echo -e "${YELLOW}No files written (all already existed — use --force to overwrite)${RESET}"
  fi
}

main
