---
name: granola-common-errors
description: |
  Troubleshoot common Granola errors and issues.
  Use when experiencing recording problems, sync issues,
  transcription errors, or integration failures.
  Trigger with phrases like "granola error", "granola not working",
  "granola problem", "fix granola", "granola troubleshoot".
allowed-tools: Read, Write, Edit, Bash(pgrep:*), Bash(ps:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Common Errors

## Overview
Diagnose and resolve common Granola issues for uninterrupted meeting capture.

## Quick Diagnostics

### Check Granola Status
```bash
# macOS - Check if Granola is running
pgrep -l Granola

# Check audio devices
system_profiler SPAudioDataType | grep "Default Input"

# Check microphone permissions
tccutil list | grep Granola
```

## Common Errors & Solutions

### Audio Issues

#### Error: "No Audio Captured"
**Symptoms:** Meeting recorded but transcript is empty
**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Wrong audio input | System Preferences > Sound > Input > Select correct device |
| Microphone muted | Check physical mute button on device |
| Permission denied | Grant microphone access in System Preferences |
| Virtual audio conflict | Disable conflicting audio software |

```bash
set -euo pipefail
# Reset audio on macOS
sudo killall coreaudiod
```

#### Error: "Poor Transcription Quality"
**Symptoms:** Many errors in transcript
**Solutions:**
1. Use quality microphone or headset
2. Reduce background noise
3. Speak clearly and at moderate pace
4. Position microphone closer

### Calendar Sync Issues

#### Error: "Meeting Not Detected"
**Symptoms:** Granola doesn't auto-start for scheduled meeting
**Solutions:**

1. **Check calendar connection:**
   - Settings > Integrations > Calendar
   - Disconnect and reconnect

2. **Verify event visibility:**
   - Event must be on synced calendar
   - You must be an attendee
   - Event needs video link

3. **Force sync:**
   - Click sync button in Granola
   - Wait 30 seconds
   - Check if meeting appears

#### Error: "Calendar Authentication Failed"
**Symptoms:** Can't connect Google/Outlook calendar
**Solutions:**
```
1. Clear browser cache
2. Log out of Google/Microsoft account
3. Log back in
4. Try connecting Granola again
5. Use private/incognito browser window
```

### Processing Issues

#### Error: "Notes Not Appearing"
**Symptoms:** Meeting ended but no notes generated
**Solutions:**

| Timeframe | Action |
|-----------|--------|
| < 2 min | Wait - processing takes time |
| 2-5 min | Check internet connection |
| 5-10 min | Restart Granola app |
| > 10 min | Contact support |

#### Error: "Processing Failed"
**Symptoms:** Error message after meeting
**Causes:**
- Audio file corrupted
- Meeting too short (< 2 min)
- Server issues
- Storage full

**Solutions:**
1. Check Granola status page
2. Verify sufficient disk space
3. Try re-uploading if option available
4. Contact support with meeting ID

### Integration Issues

#### Error: "Zapier Connection Lost"
**Symptoms:** Automations not triggering
**Solutions:**
1. Open Zapier dashboard
2. Find Granola connection
3. Click "Reconnect"
4. Re-authorize access
5. Test Zap manually

#### Error: "Slack/Notion Sync Failed"
**Symptoms:** Notes not appearing in connected apps
**Solutions:**
1. Check integration status in Settings
2. Verify target workspace permissions
3. Re-authenticate if expired
4. Check target channel/database exists

### App Issues

#### Error: "App Won't Start"
**Solutions (macOS):**
```bash
set -euo pipefail
# Force quit Granola
killall Granola

# Clear preferences (caution: resets settings)
rm -rf ~/Library/Preferences/com.granola.*
rm -rf ~/Library/Application\ Support/Granola

# Reinstall
brew reinstall granola
```

**Solutions (Windows):**
```
1. Task Manager > End Granola process
2. Settings > Apps > Granola > Repair
3. If fails, uninstall and reinstall
```

#### Error: "Update Failed"
**Solutions:**
1. Close Granola completely
2. Download latest from granola.ai/download
3. Install over existing version
4. Restart computer if needed

## Error Code Reference

| Code | Meaning | Action |
|------|---------|--------|
| E001 | Authentication failed | Re-login to Granola |
| E002 | Audio capture error | Check microphone |
| E003 | Network error | Check internet |
| E004 | Processing timeout | Retry or contact support |
| E005 | Storage full | Free up disk space |
| E006 | Calendar sync error | Reconnect calendar |

## When to Contact Support
- Errors persist after troubleshooting
- Data loss or corruption
- Billing issues
- Feature requests

**Support:** help@granola.ai

## Resources
- [Granola Status](https://status.granola.ai)
- [Granola Help Center](https://granola.ai/help)
- [Known Issues](https://granola.ai/updates)

## Next Steps
Proceed to `granola-debug-bundle` for creating diagnostic reports.

## Prerequisites

- Access to the Granola Common Errors environment or API
- Required CLI tools installed and authenticated
- Familiarity with Granola Common Errors concepts and terminology

## Instructions

1. Assess the current state of the Granola Common Errors configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Granola Common Errors |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply granola common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola common errors for production environments with multiple constraints and team-specific requirements.