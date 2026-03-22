---
name: windsurf-advanced-troubleshooting
description: |
  Advanced Windsurf debugging for hard-to-diagnose IDE, Cascade, and indexing issues.
  Use when standard troubleshooting fails, Cascade produces consistently wrong output,
  or investigating deep configuration problems.
  Trigger with phrases like "windsurf deep debug", "windsurf mystery error",
  "windsurf impossible to fix", "cascade keeps failing", "windsurf advanced debug".
allowed-tools: Read, Grep, Bash(ls:*), Bash(curl:*), Bash(find:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, debugging, advanced, troubleshooting]

---
# Windsurf Advanced Troubleshooting

## Overview
Deep debugging techniques for Windsurf issues that resist standard troubleshooting. Covers Cascade context corruption, indexing engine problems, extension conflicts, MCP failures, and workspace configuration debugging.

## Prerequisites
- Standard troubleshooting attempted (see `windsurf-common-errors`)
- Terminal access
- Understanding of Windsurf's architecture (VS Code base + Codeium AI layer)

## Instructions

### Step 1: Isolate Windsurf Layer vs VS Code Layer

```
Windsurf = VS Code + Codeium AI Layer

If the issue is:
- Editor crashes, rendering, file system → VS Code layer
- AI suggestions wrong, Cascade fails, indexing stuck → Codeium layer
- Extension not working → Extension compatibility layer

Test VS Code layer:
  windsurf --disable-extensions  # Run without extensions
  # If issue persists → VS Code layer problem

Test Codeium layer:
  # Disable Codeium: Extensions > search "codeium" > Disable
  # If issue resolves → Codeium layer problem
```

### Step 2: Debug Cascade Context Issues

When Cascade consistently gives wrong or irrelevant suggestions:

```bash
set -euo pipefail
echo "=== Cascade Context Debug ==="

# 1. Check rules file
echo "--- .windsurfrules ---"
if [ -f .windsurfrules ]; then
  CHARS=$(wc -c < .windsurfrules)
  echo "Size: $CHARS chars (limit: 6000)"
  [ "$CHARS" -gt 6000 ] && echo "WARNING: Over limit — content truncated!"
else
  echo "MISSING — Cascade has no project context"
fi

# 2. Check workspace rules
echo "--- Workspace Rules ---"
TOTAL_RULE_CHARS=0
if [ -d .windsurf/rules ]; then
  for rule in .windsurf/rules/*.md; do
    [ -f "$rule" ] || continue
    CHARS=$(wc -c < "$rule")
    TOTAL_RULE_CHARS=$((TOTAL_RULE_CHARS + CHARS))
    HAS_TRIGGER=$(grep -c "^trigger:" "$rule" || true)
    echo "  $(basename "$rule"): $CHARS chars, trigger: $([[ $HAS_TRIGGER -gt 0 ]] && echo 'YES' || echo 'MISSING')"
  done
  echo "Total: $TOTAL_RULE_CHARS chars"
else
  echo "No .windsurf/rules/ directory"
fi

# 3. Check total rules budget
RULES_CHARS=$(wc -c < .windsurfrules 2>/dev/null || echo 0)
GLOBAL_CHARS=$(wc -c < ~/.windsurf/global_rules.md 2>/dev/null || echo 0)
TOTAL=$((RULES_CHARS + GLOBAL_CHARS))
echo "--- Total Rules Budget ---"
echo "Project rules: $RULES_CHARS + Global rules: $GLOBAL_CHARS = $TOTAL chars (limit: 12000)"
[ "$TOTAL" -gt 12000 ] && echo "WARNING: Over 12000 total — rules will be truncated!"

# 4. Check memories
echo "--- Memories ---"
MEMORY_DIR="$HOME/.codeium/windsurf/memories"
if [ -d "$MEMORY_DIR" ]; then
  MEMORY_COUNT=$(find "$MEMORY_DIR" -type f | wc -l)
  echo "Memory files: $MEMORY_COUNT"
  [ "$MEMORY_COUNT" -gt 50 ] && echo "WARNING: Many memories — may cause conflicting context"
else
  echo "No memories directory"
fi
```

### Step 3: Debug Indexing Problems

```bash
set -euo pipefail
echo "=== Indexing Debug ==="

# Count files that would be indexed
TOTAL_FILES=$(find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' | wc -l)
echo "Total files (excluding node_modules, .git): $TOTAL_FILES"

# Check for large files that slow indexing
echo "--- Large files (>1MB, not in node_modules) ---"
find . -type f -size +1M -not -path '*/node_modules/*' -not -path '*/.git/*' | head -10

# Check .codeiumignore effectiveness
if [ -f .codeiumignore ]; then
  echo "--- .codeiumignore patterns ---"
  wc -l < .codeiumignore
  echo "patterns defined"
else
  echo "WARNING: No .codeiumignore — indexing everything"
fi

# Recommendations
if [ "$TOTAL_FILES" -gt 10000 ]; then
  echo ""
  echo "RECOMMENDATION: >10K files. Open a subdirectory instead of root."
  echo "RECOMMENDATION: Add more patterns to .codeiumignore"
fi
```

### Step 4: Debug Extension Conflicts

```bash
set -euo pipefail
echo "=== Extension Conflict Check ==="

# List all installed extensions
windsurf --list-extensions 2>/dev/null | while read ext; do
  # Check for known conflicts
  case "$ext" in
    *copilot*|*tabnine*|*cody*|*intellicode*|*aws-toolkit*codewhisperer*)
      echo "CONFLICT: $ext — competes with Supercomplete/Cascade"
      ;;
    *remote*|*liveshare*|*container*)
      echo "OK: $ext — compatible but may affect performance"
      ;;
    *)
      echo "OK: $ext"
      ;;
  esac
done

echo ""
echo "Resolution: Disable conflicting extensions or run:"
echo "  windsurf --disable-extensions  # Test in clean mode"
```

### Step 5: Debug MCP Server Issues

```bash
set -euo pipefail
echo "=== MCP Debug ==="

MCP_CONFIG="$HOME/.codeium/windsurf/mcp_config.json"
if [ -f "$MCP_CONFIG" ]; then
  echo "MCP config exists"
  # Validate JSON
  python3 -c "import json; json.load(open('$MCP_CONFIG'))" 2>&1 && echo "JSON: valid" || echo "JSON: INVALID"

  # Check each server command
  python3 -c "
import json
config = json.load(open('$MCP_CONFIG'))
for name, server in config.get('mcpServers', {}).items():
    cmd = server.get('command', 'N/A')
    print(f'  {name}: command={cmd}')
  "
else
  echo "No MCP config at $MCP_CONFIG"
fi
```

### Step 6: Nuclear Reset Options

When nothing else works:

```markdown
## Progressive Reset (least to most destructive)

1. Restart Cascade
   Command Palette > "Cascade: Restart"

2. Reset Indexing
   Command Palette > "Codeium: Reset Indexing"

3. Reload Window
   Cmd/Ctrl+Shift+P > "Developer: Reload Window"

4. Clear Memories
   Delete contents of ~/.codeium/windsurf/memories/

5. Reset All Codeium State
   Close Windsurf
   rm -rf ~/.codeium/windsurf/cache/
   Reopen Windsurf (re-indexes, re-authenticates)

6. Clean Install
   Uninstall Windsurf
   rm -rf ~/.codeium/
   rm -rf ~/.config/Windsurf/  # Linux
   # or: rm -rf ~/Library/Application Support/Windsurf/  # macOS
   Reinstall from windsurf.com/download
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade gives contradictory advice | Conflicting memories | Clear old memories |
| Rules ignored | Over 12K combined chars | Trim rules, check total budget |
| Wrong file suggestions | Stale index | Reset indexing |
| Slow after update | Extension incompatibility | Test with `--disable-extensions` |
| MCP tools missing | Config JSON invalid | Validate with python3 json parser |
| Everything broken | Corrupted state | Progressive reset (Step 6) |

## Examples

### Quick Diagnostic One-Liner
```bash
echo "WS files: $(find . -not -path '*/node_modules/*' -not -path '*/.git/*' -type f | wc -l) | Rules: $(wc -c < .windsurfrules 2>/dev/null || echo 0)c | Ignore: $(wc -l < .codeiumignore 2>/dev/null || echo 0) patterns | Exts: $(windsurf --list-extensions 2>/dev/null | wc -l)"
```

### Submit Support Ticket
```markdown
Attach:
1. Output from all diagnostic scripts above
2. Debug bundle from windsurf-debug-bundle
3. Exact prompts that produce wrong results
4. Expected vs actual Cascade behavior
```

## Resources
- [Windsurf GitHub Issues](https://github.com/Exafunction/codeium/issues)
- [Windsurf Status Page](https://status.windsurf.com)

## Next Steps
For load and scale patterns, see `windsurf-load-scale`.
