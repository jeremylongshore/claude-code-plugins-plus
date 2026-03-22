---
name: granola-debug-bundle
description: |
  Create diagnostic bundles for Granola support requests.
  Use when preparing support tickets, collecting system/audio/network info,
  or diagnosing complex issues that require Granola support team assistance.
  Trigger: "granola debug", "granola diagnostics", "granola support bundle",
  "granola logs", "granola system info".
allowed-tools: Read, Write, Edit, Bash(system_profiler:*), Bash(sw_vers:*), Bash(defaults:*), Bash(curl:*), Bash(pgrep:*), Bash(ls:*), Bash(zip:*), Bash(mkdir:*), Bash(uname:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, debugging, support]

---
# Granola Debug Bundle

## Current State
!`sw_vers 2>/dev/null || uname -a`
!`defaults read /Applications/Granola.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo 'Granola version: check Menu > About'`

## Overview
Collect diagnostic information for Granola support. Produces a zip bundle with system info, audio configuration, network connectivity, and app state — without exposing meeting content, transcripts, or API keys.

## Prerequisites
- Terminal access (macOS Terminal or Windows PowerShell)
- Granola installed (even if malfunctioning)
- Internet access for network diagnostics

## Instructions

### Step 1 — Create Debug Directory
```bash
set -euo pipefail
DEBUG_DIR="$HOME/Desktop/granola-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DEBUG_DIR"
echo "Debug directory: $DEBUG_DIR"
```

### Step 2 — Collect System Information

**macOS:**
```bash
set -euo pipefail
cd "$DEBUG_DIR"

# OS and hardware
sw_vers > system-info.txt
uname -a >> system-info.txt
sysctl -n hw.memsize | awk '{printf "RAM: %.0f GB\n", $1/1073741824}' >> system-info.txt

# Granola version
defaults read /Applications/Granola.app/Contents/Info.plist CFBundleShortVersionString >> system-info.txt 2>/dev/null || echo "Version: not found" >> system-info.txt

# Granola process status
pgrep -l Granola >> system-info.txt 2>/dev/null || echo "Granola: NOT RUNNING" >> system-info.txt

# Audio configuration (critical for transcription issues)
system_profiler SPAudioDataType > audio-config.txt 2>/dev/null
```

**Windows (PowerShell):**
```powershell
$dir = "$env:USERPROFILE\Desktop\granola-debug-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $dir

# System info
Get-CimInstance Win32_OperatingSystem | Select Caption, Version > "$dir\system-info.txt"
Get-Process Granola -ErrorAction SilentlyContinue >> "$dir\system-info.txt"

# Audio devices
Get-CimInstance Win32_SoundDevice | Select Name, Status > "$dir\audio-config.txt"
```

### Step 3 — Check Permissions (macOS)

```bash
set -euo pipefail
cd "$DEBUG_DIR"
echo "=== Permission Check ===" > permissions.txt

# Check if Granola has microphone access
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT service, allowed FROM access WHERE client='ai.granola.app';" >> permissions.txt 2>/dev/null \
  || echo "Cannot read TCC database (expected on macOS 14+). Check manually:" >> permissions.txt

echo "" >> permissions.txt
echo "Manual verification required:" >> permissions.txt
echo "  System Settings > Privacy & Security > Microphone > Granola" >> permissions.txt
echo "  System Settings > Privacy & Security > Screen & System Audio Recording > Granola" >> permissions.txt
```

### Step 4 — Network Diagnostics

```bash
set -euo pipefail
cd "$DEBUG_DIR"

# Test Granola API connectivity
echo "=== Network Tests ===" > network-test.txt
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> network-test.txt

# API endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://api.granola.ai/ 2>/dev/null || echo "FAIL")
echo "api.granola.ai: HTTP $HTTP_CODE" >> network-test.txt

# DNS resolution
nslookup api.granola.ai >> network-test.txt 2>&1

# WorkOS auth endpoint (Granola uses WorkOS for authentication)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://api.workos.com/ 2>/dev/null || echo "FAIL")
echo "api.workos.com (auth): HTTP $HTTP_CODE" >> network-test.txt
```

### Step 5 — Collect Cache Metadata (Not Content)

```bash
set -euo pipefail
cd "$DEBUG_DIR"

CACHE_FILE="$HOME/Library/Application Support/Granola/cache-v3.json"
echo "=== Cache Metadata ===" > cache-info.txt

if [ -f "$CACHE_FILE" ]; then
    ls -lh "$CACHE_FILE" >> cache-info.txt
    # Count documents without exposing content
    python3 -c "
import json
from pathlib import Path
try:
    raw = json.loads(Path('$CACHE_FILE').read_text())
    state = json.loads(raw) if isinstance(raw, str) else raw
    data = state.get('state', state)
    print(f'Documents: {len(data.get(\"documents\", {}))}')
    print(f'Transcripts: {len(data.get(\"transcripts\", {}))}')
    print(f'Meetings metadata: {len(data.get(\"meetingsMetadata\", {}))}')
except Exception as e:
    print(f'Parse error: {e}')
" >> cache-info.txt 2>/dev/null
else
    echo "Cache file not found" >> cache-info.txt
fi
```

### Step 6 — Package and Submit

```bash
set -euo pipefail
cd "$(dirname "$DEBUG_DIR")"
zip -r "$(basename "$DEBUG_DIR").zip" "$(basename "$DEBUG_DIR")/"
echo "Bundle ready: $(basename "$DEBUG_DIR").zip"
echo "Submit to: help@granola.ai or via in-app support"
```

## Self-Diagnosis Checklist
Run through this before contacting support:

- [ ] Granola is updated to the latest version (Check for updates in menu)
- [ ] Internet connection is stable (can load granola.ai in browser)
- [ ] Microphone permission is granted
- [ ] Screen & System Audio Recording permission is granted (macOS)
- [ ] Correct audio input device is selected in System Settings
- [ ] No conflicting virtual audio software (Loopback, BlackHole, etc.)
- [ ] Calendar is connected and syncing (check Settings > Calendar)
- [ ] Sufficient disk space (> 500 MB free)
- [ ] [status.granola.ai](https://status.granola.ai) shows no active incidents

## Privacy: What the Bundle Does NOT Include
- Meeting transcripts or notes content
- Personal calendar event details
- API keys or authentication tokens
- Audio recordings
- Contact/attendee information

## Output
- Zip file on Desktop containing system, audio, network, and app diagnostics
- Ready for submission to Granola support at help@granola.ai
- Self-diagnosis checklist completed before escalation

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Permission denied on TCC database | macOS 14+ security | Use manual permission verification instead |
| Network test fails | Firewall or proxy | Check outbound HTTPS to `api.granola.ai` and `api.workos.com` |
| Zip creation fails | Disk full | Free space, or tar instead: `tar czf bundle.tar.gz debug-dir/` |
| Cache parse error | Different Granola version | Report the error — it helps support identify the version issue |

## Resources
- [Granola Support](https://help.granola.ai)
- [Status Page](https://status.granola.ai)
- [Transcription Troubleshooting](https://docs.granola.ai/help-center/troubleshooting/transcription-issues)

## Next Steps
Proceed to `granola-rate-limits` to understand usage limits and plan differences.
