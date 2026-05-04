#!/usr/bin/env bash
# uninstall.sh — pre-uninstall hook for the contributing-clanker plugin.
#
# Runs before `/plugin uninstall contributing-clanker`. Removes the
# plugin-shipped runtime scripts and preserves the user's data.
#
# What it does:
#   - Removes ~/.contribute-system/bin/*.sh
#   - Removes ~/.contribute-system/gates/*.sh
#   - Removes ~/.contribute-system/gates/lib/*.sh
#
# What it does NOT touch (your data is yours):
#   - ~/.contribute-system/candidates/   (your candidate queue)
#   - ~/.contribute-system/research/     (your dossiers)
#   - ~/.contribute-system/log.jsonl     (your event history)
#   - ~/.contribute-system/profile.md    (your preferences)
#   - ~/.contribute-system/check-runs/   (your check-run logs)
#   - ~/.contribute-system/test-logs/    (your test output logs)
#
# To purge entirely: rm -rf ~/.contribute-system/

set -euo pipefail

RUNTIME_DIR="${CONTRIBUTE_SYSTEM_DIR:-$HOME/.contribute-system}"

if [[ ! -d "$RUNTIME_DIR" ]]; then
  printf '  ! runtime directory %s not found — nothing to uninstall\n' "$RUNTIME_DIR"
  exit 0
fi

printf '\n  Removing contributing-clanker runtime scripts from %s\n\n' "$RUNTIME_DIR"

REMOVED_BIN=0
REMOVED_GATES=0

if [[ -d "$RUNTIME_DIR/bin" ]]; then
  for f in "$RUNTIME_DIR"/bin/*.sh; do
    [[ -f "$f" ]] || continue
    /usr/bin/rm -f "$f"
    REMOVED_BIN=$((REMOVED_BIN + 1))
  done
fi

if [[ -d "$RUNTIME_DIR/gates" ]]; then
  for f in "$RUNTIME_DIR"/gates/*.sh; do
    [[ -f "$f" ]] || continue
    /usr/bin/rm -f "$f"
    REMOVED_GATES=$((REMOVED_GATES + 1))
  done
  /usr/bin/rm -f "$RUNTIME_DIR/gates/lib/preamble.sh" 2>/dev/null || true
fi

printf '  ✓ removed %d orchestrator/reporter script(s) from %s/bin/\n' "$REMOVED_BIN" "$RUNTIME_DIR"
printf '  ✓ removed %d gate script(s) from %s/gates/\n' "$REMOVED_GATES" "$RUNTIME_DIR"

# Preserved data summary
CAND_COUNT=$(/usr/bin/find "$RUNTIME_DIR/candidates" -maxdepth 1 -name '*.md' -type f 2>/dev/null | /usr/bin/wc -l)
DOSSIER_COUNT=$(/usr/bin/find "$RUNTIME_DIR/research" -maxdepth 1 -name '*.md' -type f 2>/dev/null | /usr/bin/wc -l)
if [[ -f "$RUNTIME_DIR/log.jsonl" ]]; then
  LOG_LINES=$(/usr/bin/wc -l < "$RUNTIME_DIR/log.jsonl")
else
  LOG_LINES=0
fi

printf '\n  Preserved (your data — left untouched):\n'
printf '    %d candidate(s) at %s/candidates/\n' "$CAND_COUNT" "$RUNTIME_DIR"
printf '    %d dossier(s) at %s/research/\n' "$DOSSIER_COUNT" "$RUNTIME_DIR"
printf '    %s event(s) in %s/log.jsonl\n' "$LOG_LINES" "$RUNTIME_DIR"
printf '    profile.md at %s\n' "$RUNTIME_DIR/profile.md"
printf '\n  To purge entirely:  rm -rf %s\n\n' "$RUNTIME_DIR"
