---
name: windsurf-debug-bundle
description: |
  Collect Windsurf diagnostic information for troubleshooting and support tickets.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic data for Windsurf problems.
  Trigger with phrases like "windsurf debug", "windsurf support",
  "windsurf diagnostic", "windsurf logs", "windsurf not working".
allowed-tools: Read, Bash(grep:*), Bash(ls:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, debugging, support]

---
# Windsurf Debug Bundle

## Current State
!`windsurf --version 2>/dev/null || echo 'Windsurf CLI not in PATH'`
!`node --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect all diagnostic information needed to troubleshoot Windsurf issues or submit effective support tickets.

## Prerequisites
- Windsurf installed (even if malfunctioning)
- Terminal access
- Permission to read Windsurf config directories

## Instructions

### Step 1: Collect Windsurf Configuration State

```bash
#!/bin/bash
set -euo pipefail

BUNDLE="windsurf-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"/{config,logs,workspace}

echo "=== Windsurf Debug Bundle ===" > "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"

# 1. Windsurf version and environment
echo "--- Environment ---" >> "$BUNDLE/summary.txt"
windsurf --version >> "$BUNDLE/summary.txt" 2>&1 || echo "windsurf CLI not found" >> "$BUNDLE/summary.txt"
node --version >> "$BUNDLE/summary.txt" 2>&1
echo "OS: $(uname -srm)" >> "$BUNDLE/summary.txt"

# 2. Codeium config (redacted)
echo "--- Codeium Config ---" >> "$BUNDLE/summary.txt"
ls -la ~/.codeium/ >> "$BUNDLE/config/codeium-dir.txt" 2>&1 || echo "No ~/.codeium/" >> "$BUNDLE/config/codeium-dir.txt"

# 3. MCP server config (redacted)
if [ -f ~/.codeium/windsurf/mcp_config.json ]; then
  sed 's/"[A-Za-z0-9_-]\{20,\}"/"***REDACTED***"/g' ~/.codeium/windsurf/mcp_config.json > "$BUNDLE/config/mcp-config-redacted.json"
fi

# 4. Workspace config
cp .windsurfrules "$BUNDLE/workspace/" 2>/dev/null || true
cp .codeiumignore "$BUNDLE/workspace/" 2>/dev/null || true
ls -la .windsurf/ >> "$BUNDLE/workspace/windsurf-dir.txt" 2>/dev/null || true
ls -la .windsurf/rules/ >> "$BUNDLE/workspace/rules-dir.txt" 2>/dev/null || true

# 5. Extension list
windsurf --list-extensions > "$BUNDLE/config/extensions.txt" 2>/dev/null || echo "Cannot list extensions" > "$BUNDLE/config/extensions.txt"
```

### Step 2: Collect Logs

```bash
# Windsurf logs location varies by OS:
# macOS: ~/Library/Application Support/Windsurf/logs/
# Linux: ~/.config/Windsurf/logs/
# Windows: %APPDATA%/Windsurf/logs/

LOG_DIR="${HOME}/.config/Windsurf/logs"
[ -d "$LOG_DIR" ] || LOG_DIR="${HOME}/Library/Application Support/Windsurf/logs"

if [ -d "$LOG_DIR" ]; then
  # Copy last 1000 lines of each log (redacted)
  for log in "$LOG_DIR"/*.log; do
    tail -1000 "$log" 2>/dev/null | sed 's/Bearer [^ ]*/Bearer ***REDACTED***/g' > "$BUNDLE/logs/$(basename "$log")"
  done
fi

# Codeium-specific logs
if [ -d ~/.codeium/windsurf/logs ]; then
  cp ~/.codeium/windsurf/logs/*.log "$BUNDLE/logs/" 2>/dev/null || true
fi
```

### Step 3: Check Workspace Health

```bash
# Workspace analysis
echo "--- Workspace Health ---" >> "$BUNDLE/summary.txt"
echo "File count: $(find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' | wc -l)" >> "$BUNDLE/summary.txt"
echo "Has .windsurfrules: $([ -f .windsurfrules ] && echo 'YES' || echo 'NO')" >> "$BUNDLE/summary.txt"
echo "Has .codeiumignore: $([ -f .codeiumignore ] && echo 'YES' || echo 'NO')" >> "$BUNDLE/summary.txt"
echo "Has .windsurf/rules/: $([ -d .windsurf/rules ] && echo 'YES' || echo 'NO')" >> "$BUNDLE/summary.txt"

# Check for common issues
if [ ! -f .codeiumignore ] && [ -d node_modules ]; then
  echo "WARNING: No .codeiumignore but node_modules exists -- indexing will be slow" >> "$BUNDLE/summary.txt"
fi
```

### Step 4: Package and Submit

```bash
tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo "Debug bundle created: $BUNDLE.tar.gz"
echo "Review for sensitive data before submitting to support."
```

## Support Ticket Template

```markdown
## Windsurf Support Request

**Windsurf Version:** [from debug bundle]
**OS:** [macOS/Linux/Windows + version]
**Plan:** [Free/Pro/Teams/Enterprise]

### Issue
[One paragraph description]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]

### Expected vs Actual
- Expected: [behavior]
- Actual: [behavior]

### Attachments
- [ ] Debug bundle (windsurf-debug-*.tar.gz)
- [ ] Screenshot of error (if visual)
- [ ] Relevant .windsurfrules (if context-related)

### Already Tried
- [ ] Restart Cascade
- [ ] Reload Window
- [ ] Reset Indexing
- [ ] Disable conflicting extensions
```

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| Windsurf version | Compatibility check | Yes |
| Extension list | Conflict detection | Yes |
| Workspace config | Context issues | Yes |
| Log files (redacted) | Error analysis | Yes |
| MCP config (redacted) | Integration issues | Yes |

## Examples

### ALWAYS REDACT
- API keys and tokens
- Passwords and secrets
- Personal file paths (replace with ~/)
- Customer data

### Quick Single-Command Health Check
```bash
echo "Windsurf: $(windsurf --version 2>/dev/null || echo 'N/A')" && \
echo "Rules: $([ -f .windsurfrules ] && wc -c < .windsurfrules || echo 'none')" && \
echo "Ignore: $([ -f .codeiumignore ] && wc -l < .codeiumignore || echo 'none')"
```

## Resources
- [Windsurf GitHub Issues](https://github.com/Exafunction/codeium/issues)
- [Windsurf Status](https://status.windsurf.com)

## Next Steps
For rate limit issues, see `windsurf-rate-limits`.
