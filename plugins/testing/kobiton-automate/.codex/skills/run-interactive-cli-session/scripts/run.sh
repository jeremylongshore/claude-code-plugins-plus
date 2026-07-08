#!/bin/bash
# Wrapper that resolves binary, portal URL, and credentials automatically.
# Usage: kobiton [kobiton-cli args...]
# Install: ln -sf <plugin-path>/skills/run-interactive-cli-session/scripts/run.sh ~/.kobiton/bin/kobiton

set -euo pipefail

# --- Helper: trim leading and trailing whitespace (pure bash) ---
trim() { local v="$1"; v="${v#"${v%%[![:space:]]*}"}"; v="${v%"${v##*[![:space:]]}"}"; printf '%s' "$v"; }

# Resolve symlinks so SCRIPT_DIR points to the real location, not the symlink
SOURCE="$0"
while [ -L "$SOURCE" ]; do
  DIR="$(cd "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd "$(dirname "$SOURCE")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/.."
PROJECT_ROOT="$SKILL_DIR/../.."

# --- 1. Resolve bundled binary ---
BINARY="$SKILL_DIR/bin/kobiton"
if [ ! -f "$BINARY" ]; then
  echo "Error: bundled kobiton CLI binary missing at $BINARY." >&2
  echo "Re-install the plugin to restore it." >&2
  exit 1
fi
chmod +x "$BINARY" 2>/dev/null

# --- 2. Load credentials from ~/.kobiton/.credentials (INI profile format) ---
CRED_FILE="$HOME/.kobiton/.credentials"
if [ -z "${KOBITON_USER:-}" ] && [ -f "$CRED_FILE" ]; then
  PROFILE="${KOBITON_PROFILE:-default}"
  IN_PROFILE=false
  FOUND_PROFILE=false
  while IFS= read -r line || [ -n "$line" ]; do
    # Strip trailing whitespace from the raw line
    line="$(trim "$line")"
    # Skip blank lines and comments
    [[ -z "$line" || "$line" == \#* ]] && continue
    # Section header
    if [[ "$line" == \[*\] ]]; then
      section="${line#[}"
      section="${section%]}"
      section="$(trim "$section")"
      if [ "$section" = "$PROFILE" ]; then
        IN_PROFILE=true
        FOUND_PROFILE=true
      else
        # If we were in our profile, we've passed it — stop
        $IN_PROFILE && break
        IN_PROFILE=false
      fi
      continue
    fi
    # Key=Value inside our profile
    if $IN_PROFILE; then
      key="$(trim "${line%%=*}")"
      value="$(trim "${line#*=}")"
      case "$key" in
        KOBITON_USER)   KOBITON_USER="$value" ;;
        KOBITON_API_KEY) KOBITON_API_KEY="$value" ;;
        KOBITON_PORTAL)  KOBITON_PORTAL="$value" ;;
      esac
    fi
  done < "$CRED_FILE"

  if ! $FOUND_PROFILE; then
    echo "Error: Profile [$PROFILE] not found in $CRED_FILE" >&2
    exit 1
  fi

  export KOBITON_USER KOBITON_API_KEY
  [ -n "${KOBITON_PORTAL:-}" ] && export KOBITON_PORTAL
fi

# --- 3. Auto-derive portal URL from .mcp.json (fallback if not in credentials) ---
if [ -z "${KOBITON_PORTAL:-}" ]; then
  MCP_FILE="$PROJECT_ROOT/.mcp.json"
  if [ -f "$MCP_FILE" ]; then
    MCP_URL=$(MCP_FILE="$MCP_FILE" node -e "
      const m=JSON.parse(require('fs').readFileSync(process.env.MCP_FILE,'utf8'));
      const s=m.mcpServers?.kobiton;
      console.log(s?.url || '');
    " 2>/dev/null || true)
    if [ -n "$MCP_URL" ]; then
      export KOBITON_PORTAL="${MCP_URL%/mcp}"
    fi
  fi
fi

# --- 4. Validate minimum requirements ---
MISSING=()
[ -z "${KOBITON_PORTAL:-}" ]  && MISSING+=("KOBITON_PORTAL")
[ -z "${KOBITON_USER:-}" ]    && MISSING+=("KOBITON_USER")
[ -z "${KOBITON_API_KEY:-}" ] && MISSING+=("KOBITON_API_KEY")
if [ ${#MISSING[@]} -gt 0 ]; then
  echo "Error: Missing ${MISSING[*]}." >&2
  echo "Run /automate:doctor to diagnose, or /automate:setup to fetch fresh credentials." >&2
  exit 1
fi

# --- 5. KOB-52724: declare the AI workspace identity so kobiton-cli's
#       resolve_ai_tool_name() includes it in the POST /v2/sessions body.
#
#       This wrapper lives at the stable path ~/.kobiton/bin/kobiton and
#       can therefore be invoked by ANY AI workspace (Claude Code, Copilot
#       CLI, Gemini CLI, Codex CLI, …), not just Claude Code. We MUST NOT
#       hard-default to "Claude" or we mis-attribute every non-Claude
#       caller's session.
#
#       Priority (mirrors kobiton-cli's resolve_ai_tool_name() in the k
#       repo — keep these in lock-step):
#         1. KOBITON_AI_TOOL_NAME already exported by the caller — pass
#            through unchanged.
#         2. CLAUDECODE=1     → "Claude"  (Anthropic Claude Code; set on
#            every spawned subprocess).
#         3. COPILOT_CLI=1    → "Copilot" (GitHub Copilot CLI; verified
#            by inspecting the bundled binary's subprocess env-builder;
#            analog of CLAUDECODE=1).
#         4. GEMINI_CLI=1     → "Gemini"  (speculative — Google's
#            `@google/gemini-cli` v0.x does NOT set this on spawned
#            subprocesses today. Kept as a forward-compat path + manual
#            opt-in. The install-path fallback below is the actual
#            mechanism that catches Gemini today.)
#         5. CODEX_THREAD_ID  → "Codex"   (OpenAI Codex CLI; verified
#            in the @openai/codex native binary — set per-invocation
#            during an active Codex thread.) Also accepts CODEX_CLI=1
#            for convention parity.
#         6. Install-path fallback — when no env-var marker fires, infer
#            the host from THIS script's resolved install location:
#                ~/.claude/plugins/...        → Claude Code
#                ~/.copilot/installed-plugins → Copilot CLI
#                ~/.gemini/extensions/...     → Gemini CLI
#                ~/.codex/...                 → Codex CLI (path TBD)
#            Each AI host installs the plugin under its own directory
#            and re-points the `~/.kobiton/bin/kobiton` symlink, so
#            $SCRIPT_DIR (symlink-resolved earlier in this script)
#            reflects which install the caller went through. Rescues
#            Gemini CLI today and is robust to future AI hosts that
#            don't expose a clean subprocess env marker.
#         7. Still nothing — leave unset and let kobiton-cli's own
#            resolve_ai_tool_name() fall through to None (session row's
#            aiToolName ends up null). Better than guessing.
if [ -z "${KOBITON_AI_TOOL_NAME:-}" ]; then
  if [ "${CLAUDECODE:-}" = "1" ]; then
    export KOBITON_AI_TOOL_NAME=Claude
  elif [ "${COPILOT_CLI:-}" = "1" ]; then
    export KOBITON_AI_TOOL_NAME=Copilot
  elif [ "${GEMINI_CLI:-}" = "1" ]; then
    export KOBITON_AI_TOOL_NAME=Gemini
  elif [ "${CODEX_CLI:-}" = "1" ] || [ -n "${CODEX_THREAD_ID:-}" ]; then
    export KOBITON_AI_TOOL_NAME=Codex
  else
    case "$SCRIPT_DIR" in
      */.gemini/extensions/*)         export KOBITON_AI_TOOL_NAME=Gemini ;;
      */.copilot/installed-plugins/*) export KOBITON_AI_TOOL_NAME=Copilot ;;
      */.claude/plugins/*)            export KOBITON_AI_TOOL_NAME=Claude ;;
      */.codex/*)                     export KOBITON_AI_TOOL_NAME=Codex ;;
    esac
  fi
fi

# --- 6. Run the CLI (JWT at ~/.kobiton/.session is loaded by CLI itself) ---
exec "$BINARY" "$@"
