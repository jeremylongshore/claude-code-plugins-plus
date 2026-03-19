---
name: granola-debug-bundle
description: |
  Create diagnostic bundles for Granola troubleshooting.
  Use when preparing support requests, collecting system information,
  or diagnosing complex issues with Granola.
  Trigger with phrases like "granola debug", "granola diagnostics",
  "granola support bundle", "granola logs", "granola system info".
allowed-tools: Read, Write, Edit, Bash(system_profiler:*), Bash(log:*), Bash(sw_vers:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect comprehensive diagnostic information for Granola troubleshooting and support requests.

## Prerequisites
- Administrator access on your computer
- Granola installed (even if malfunctioning)
- Terminal/Command Prompt access

## Instructions

### Step 1: System Information

#### macOS
```bash
# Create debug directory
mkdir -p ~/Desktop/granola-debug
cd ~/Desktop/granola-debug

# System info
sw_vers > system-info.txt
system_profiler SPHardwareDataType >> system-info.txt
system_profiler SPSoftwareDataType >> system-info.txt

# Audio configuration
system_profiler SPAudioDataType > audio-config.txt

# Display info
system_profiler SPDisplaysDataType > display-info.txt
```

#### Windows
```powershell
# Create debug directory
mkdir $env:USERPROFILE\Desktop\granola-debug
cd $env:USERPROFILE\Desktop\granola-debug

# System info
systeminfo > system-info.txt

# Audio devices
Get-WmiObject Win32_SoundDevice | Out-File audio-devices.txt
```

### Step 2: Granola Logs

#### macOS
```bash
# Granola application logs
cp -r ~/Library/Logs/Granola ./granola-logs 2>/dev/null

# Application support data (no sensitive data)
ls -la ~/Library/Application\ Support/Granola/ > app-support-listing.txt

# System logs related to Granola
log show --predicate 'process == "Granola"' --last 1h > system-logs.txt 2>/dev/null
```

#### Windows
```powershell
# Granola logs
Copy-Item "$env:LOCALAPPDATA\Granola\logs" -Destination ".\granola-logs" -Recurse

# Application event logs
Get-EventLog -LogName Application -Source "Granola" -Newest 100 | Out-File app-events.txt
```

### Step 3: Network Diagnostics
```bash
set -euo pipefail
# Test Granola connectivity
curl -s -o /dev/null -w "%{http_code}" https://api.granola.ai/health > network-test.txt
curl -s -o /dev/null -w "%{http_code}" https://granola.ai >> network-test.txt

# DNS resolution
nslookup api.granola.ai >> network-test.txt 2>&1

# Trace route (optional, may take time)
traceroute -m 10 api.granola.ai >> network-test.txt 2>&1
```

### Step 4: Calendar Integration Status
```bash
# Create calendar status report
cat > calendar-status.txt << 'EOF'
Calendar Integration Checklist:

1. Calendar Provider: [Google/Outlook/Other]
2. Last Successful Sync: [Date/Time]
3. Connected Calendars: [List]
4. OAuth Token Status: [Valid/Expired/Unknown]
5. Permissions Granted: [Yes/No/Partial]

Recent Calendar Errors:
[Copy any errors from Granola settings]
EOF
```

### Step 5: Audio Configuration Check
```bash
# macOS audio test
cat > audio-check.txt << 'EOF'
Audio Configuration Report
==========================

Default Input Device: $(system_profiler SPAudioDataType | grep "Default Input" | head -1)

Input Devices Available:
$(system_profiler SPAudioDataType | grep -A5 "Input Source")

Audio Permissions:
- Granola has microphone access: [Yes/No]
- Other apps using microphone: [List]

Virtual Audio Software:
- Loopback: [Installed/Not Installed]
- BlackHole: [Installed/Not Installed]
- Other: [Specify]
EOF
```

### Step 6: Create Debug Bundle
```bash
# Package all diagnostics
cd ~/Desktop
zip -r granola-debug-$(date +%Y%m%d-%H%M%S).zip granola-debug/

echo "Debug bundle created: granola-debug-$(date +%Y%m%d-%H%M%S).zip"
echo "Send this file to help@granola.ai"
```

## Debug Bundle Contents

| File | Purpose |
|------|---------|
| system-info.txt | OS and hardware details |
| audio-config.txt | Audio device configuration |
| granola-logs/ | Application log files |
| network-test.txt | Connectivity diagnostics |
| calendar-status.txt | Calendar integration state |
| audio-check.txt | Microphone configuration |

## Output
- Comprehensive debug bundle zip file
- Ready for submission to Granola support
- Excludes sensitive data (transcripts, notes)

## Privacy Considerations
The debug bundle does NOT include:
- Meeting transcripts or notes
- Personal calendar event details
- API keys or tokens
- Audio recordings

## Submitting to Support
1. Email debug bundle to: help@granola.ai
2. Include:
   - Description of issue
   - Steps to reproduce
   - When issue started
   - Your Granola version
3. Reference any error codes displayed

## Self-Diagnosis Tips
Before contacting support, check:

```markdown
## Quick Checks
- [ ] Granola is updated to latest version
- [ ] Internet connection is stable
- [ ] Microphone permissions granted
- [ ] Calendar is connected
- [ ] Sufficient disk space (> 1GB)
- [ ] Antivirus not blocking Granola
```

## Resources
- [Granola Support](https://granola.ai/help)
- [Status Page](https://status.granola.ai)

## Next Steps
Proceed to `granola-rate-limits` to understand usage limits.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with debugging |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply granola debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola debug bundle for production environments with multiple constraints and team-specific requirements.