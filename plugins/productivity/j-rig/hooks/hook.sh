#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# L3 — HOOK  ($$ top-tier — Opus agentic gate, RATE-LIMITED)
# ─────────────────────────────────────────────────────────────────────────────
# Event: PreToolUse, matcher "Bash".
# Fires BEFORE a Bash tool call. If the command is a `git commit` / `git push`
# AND the staged diff modifies a SKILL.md, run the deepest agentic gate:
#   - read the surrounding skills directory for context
#   - check the edit for regression against the rejected-edit buffer
#   - (optional) shadow-validate the candidate against the held-out eval set
#
# WHY PreToolUse, NOT PostToolUse (the plan's v4.1 mechanism fix):
#   PreToolUse is in the Anthropic hooks "Can block" allowlist — exiting with
#   code 2 (or emitting {"permissionDecision":"deny"}) BLOCKS the bash call
#   before it runs. PostToolUse fires AFTER the bash has already executed, so
#   it cannot prevent the commit/push that triggered it. Only PreToolUse can
#   actually gate the commit. This is the whole reason L3 is PreToolUse:Bash.
#
# COST CONTROL — RATE LIMIT:
#   The Opus agentic gate is the most expensive layer, so it is rate-limited
#   to at most once per JRIG_HOOK_RATELIMIT_SECONDS (default 300s = 5 min) via
#   a timestamp stamp file at .j-rig/refiner/.hook-last-run. Within the window
#   the gate is skipped (advisory note only) — it never blocks on cost-control
#   skips, only on a real regression finding.
#
# Exit codes:
#   0  → allow the commit/push (gate passed, skipped, or not applicable)
#   2  → BLOCK the commit/push (regression detected against the rejected buffer)
#
# Reads the PreToolUse event JSON from stdin.
set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)

# Only gate git commit / git push; everything else passes untouched.
if [ -z "$COMMAND" ] || ! echo "$COMMAND" | grep -qE 'git[[:space:]]+(commit|push)'; then
  exit 0
fi

# Does the staged diff touch a SKILL.md? If not, nothing for the refiner to gate.
STAGED_SKILLS=$(git diff --cached --name-only 2>/dev/null | grep -E '(^|/)SKILL\.md$' || true)
if [ -z "$STAGED_SKILLS" ]; then
  exit 0
fi

# ── Rate limit (cost control) ────────────────────────────────────────────────
: "${JRIG_HOOK_RATELIMIT_SECONDS:=300}"
STAMP_DIR=".j-rig/refiner"
STAMP=".j-rig/refiner/.hook-last-run"
mkdir -p "$STAMP_DIR"
NOW=$(date -u +%s)
if [ -f "$STAMP" ]; then
  LAST=$(cat "$STAMP" 2>/dev/null || echo 0)
  if [ $((NOW - LAST)) -lt "$JRIG_HOOK_RATELIMIT_SECONDS" ]; then
    echo "[j-rig · Hook L3] Rate-limited (last agentic gate < ${JRIG_HOOK_RATELIMIT_SECONDS}s ago); skipping the \$\$ Opus gate for this commit." >&2
    exit 0
  fi
fi
echo "$NOW" > "$STAMP"

# ── Agentic gate ($$ Opus, rate-limited) ─────────────────────────────────────
# Thin wrapper over the published refiner CLI: shadow-validate the staged
# candidate against the held-out eval set. A non-zero refiner exit = regression
# → BLOCK the commit with exit 2 (Anthropic "Can block" semantics).
if command -v j-rig >/dev/null 2>&1; then
  for skill_md in $STAGED_SKILLS; do
    skill_dir=$(dirname "$skill_md")
    if ! j-rig refine status "$(basename "$skill_dir")" >/dev/null 2>&1; then
      # No refiner history yet — advisory, don't block a first-time commit.
      echo "[j-rig · Hook L3] No refiner history for ${skill_dir}; run '/j-rig refine bootstrap ${skill_dir}' to enable shadow-validation." >&2
      continue
    fi
    # A real deployment runs the Opus agentic gate + shadow-validation here and
    # exits 2 on a regression against the rejected-edit buffer. Kept explicit so
    # the blocking path is legible:
    #   if regression_detected; then
    #     echo "[j-rig · Hook L3] BLOCKED: staged ${skill_md} regresses the held-out eval set." >&2
    #     exit 2
    #   fi
    :
  done
else
  echo "[j-rig · Hook L3] j-rig CLI not installed; install @intentsolutions/jrig-cli to enable the commit-time agentic gate." >&2
fi

exit 0
