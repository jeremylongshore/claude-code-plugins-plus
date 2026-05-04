#!/usr/bin/env bash
# install.sh — post-install hook for the contributing-clanker plugin.
#
# Runs after `/plugin install contributing-clanker`. Idempotent — re-running
# is safe and overwrites runtime scripts with the freshly-installed versions
# (which is desired: the plugin upgrade path is "uninstall + install").
#
# What it does:
#   1. Creates ~/.contribute-system/{candidates,research,gates,gates/lib,bin,
#      check-runs,test-logs} if missing
#   2. Copies the plugin's runtime scripts (gates + orchestrators + reporters
#      + lib) into the runtime dirs with chmod +x
#   3. If ~/.contribute-system/profile.md is missing, writes a starter
#      template the user can fill in
#   4. Prints next-steps
#
# What it does NOT touch (your data is yours):
#   - ~/.contribute-system/candidates/*.md
#   - ~/.contribute-system/research/*.md
#   - ~/.contribute-system/log.jsonl
#   - ~/.contribute-system/profile.md (only created if missing)

set -euo pipefail

# Resolve PLUGIN_DIR — Claude Code sets CLAUDE_PLUGIN_ROOT at hook execution.
# Fallback resolves relative to this script for manual invocation.
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
RUNTIME_DIR="${CONTRIBUTE_SYSTEM_DIR:-$HOME/.contribute-system}"

printf '\n  Installing contributing-clanker runtime to %s\n\n' "$RUNTIME_DIR"

# 1. Create runtime directory tree
for sub in candidates research gates gates/lib bin check-runs test-logs; do
  /usr/bin/mkdir -p "$RUNTIME_DIR/$sub"
done

# 2. Copy plugin's runtime scripts into the runtime dirs
SKILL_SCRIPTS="$PLUGIN_DIR/skills/contribute/scripts"

if [[ ! -d "$SKILL_SCRIPTS" ]]; then
  printf '  ! plugin skill scripts missing at %s\n' "$SKILL_SCRIPTS" >&2
  printf '    (expected the release script to have synced them — manifest mismatch)\n' >&2
  exit 1
fi

# Top-level orchestrators + reporters → ~/.contribute-system/bin/
for f in "$SKILL_SCRIPTS"/*.sh; do
  [[ -f "$f" ]] || continue
  /usr/bin/cp -f "$f" "$RUNTIME_DIR/bin/"
  /usr/bin/chmod +x "$RUNTIME_DIR/bin/$(basename "$f")"
done

# Gates → ~/.contribute-system/gates/
for f in "$SKILL_SCRIPTS"/gates/*.sh; do
  [[ -f "$f" ]] || continue
  /usr/bin/cp -f "$f" "$RUNTIME_DIR/gates/"
  /usr/bin/chmod +x "$RUNTIME_DIR/gates/$(basename "$f")"
done

# Gate library → ~/.contribute-system/gates/lib/
if [[ -f "$SKILL_SCRIPTS/gates/lib/preamble.sh" ]]; then
  /usr/bin/cp -f "$SKILL_SCRIPTS/gates/lib/preamble.sh" "$RUNTIME_DIR/gates/lib/preamble.sh"
fi

GATE_COUNT=$(/usr/bin/find "$RUNTIME_DIR/gates" -maxdepth 1 -name '*.sh' -type f 2>/dev/null | /usr/bin/wc -l)
SCRIPT_COUNT=$(/usr/bin/find "$RUNTIME_DIR/bin" -maxdepth 1 -name '*.sh' -type f 2>/dev/null | /usr/bin/wc -l)

printf '  ✓ %d gate scripts installed at %s\n' "$GATE_COUNT" "$RUNTIME_DIR/gates/"
printf '  ✓ %d orchestrator + reporter scripts at %s\n' "$SCRIPT_COUNT" "$RUNTIME_DIR/bin/"

# 3. Starter profile.md if missing
PROFILE="$RUNTIME_DIR/profile.md"
if [[ ! -f "$PROFILE" ]]; then
  /usr/bin/cat > "$PROFILE" <<'PROFILE_TEMPLATE'
---
title: Contribution profile
created: 2026-01-01
---

# Contribution profile

Edit this file with your preferred languages, target repo tiers, and any
constraints. The `@scout` subagent reads this when sweeping for new work.

## Languages

- (e.g.) typescript
- python
- bash

## Target repo tiers

- mainstream  # >5k stars, active maintainers, predictable etiquette
- emerging    # 500-5k stars, smaller community, faster turnaround
- niche       # <500 stars, often single-maintainer

## Constraints

- (e.g.) no CLA-required repos for trivial work
- (e.g.) no Java repos (out of stack strength)
- (e.g.) avoid GPL-incompatible licensing if your work has commercial reuse needs
PROFILE_TEMPLATE
  printf '  ✓ wrote starter profile at %s\n' "$PROFILE"
else
  printf '  ✓ profile.md already exists — left untouched\n'
fi

# 4. Next steps
printf '\n  Done.\n\n'
printf '  Next steps:\n'
printf '    1. Edit %s with your languages + target tiers\n' "$PROFILE"
printf '    2. Verify gh + jq:  gh auth status && command -v jq\n'
printf '    3. In Claude Code:  /contribute\n\n'
printf '  Your candidate state, dossiers, and event log will live at %s\n' "$RUNTIME_DIR"
printf '  (preserved across plugin upgrade and uninstall)\n\n'
