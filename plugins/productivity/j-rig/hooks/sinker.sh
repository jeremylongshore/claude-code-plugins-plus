#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# L1 — SINKER  ($0, no model call — the cheapest layer)
# ─────────────────────────────────────────────────────────────────────────────
# Event: PostToolUse, matcher "Edit|Write".
# Fires after every Edit/Write. If the touched file is a SKILL.md, run the
# deterministic validate-skillmd Tier-2 frontmatter check (agentskills.io +
# Claude Code extension-layer compliance per Skill Refiner plan AC-11) and
# append any warning to the session context. NO model is invoked — this is a
# pure static gate, so it can fire on every edit at zero token cost.
#
# Advisory only: the sinker never blocks. It writes findings to stderr so
# Claude sees them in the next turn's context. Blocking is the L3 Hook's job.
#
# Reads the hook event JSON from stdin (Claude Code hooks contract).
set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.file // empty' 2>/dev/null || true)

# Only act on SKILL.md edits; silently pass on everything else.
if [ -z "$FILE_PATH" ] || ! echo "$FILE_PATH" | grep -qE '(^|/)SKILL\.md$'; then
  exit 0
fi

# Deterministic Tier-2 check. Prefer the in-repo marketplace validator when
# present (this repo ships scripts/validate-skills-schema.py); fall back to the
# /validate-skillmd skill guidance if it is not reachable. Either way, $0 —
# no model call.
VALIDATOR="scripts/validate-skills-schema.py"
if [ -f "$VALIDATOR" ]; then
  if ! python3 "$VALIDATOR" "$FILE_PATH" --marketplace >/dev/null 2>&1; then
    {
      echo "[j-rig · Sinker L1] SKILL.md frontmatter check FAILED for: $FILE_PATH"
      echo "  Run: python3 $VALIDATOR \"$FILE_PATH\" --marketplace  (deterministic, no model call)"
      echo "  Fix the 8-field marketplace frontmatter before this skill ships."
    } >&2
  fi
else
  {
    echo "[j-rig · Sinker L1] Edited a SKILL.md ($FILE_PATH)."
    echo "  Run /validate-skillmd on it (Tier 2 deterministic frontmatter check) before shipping."
  } >&2
fi

exit 0
