---
name: granola-common-errors
description: |
  Troubleshoot common Granola errors — audio capture failures, transcription issues,
  calendar sync problems, and integration errors. Platform-specific fixes for macOS and Windows.
  Trigger: "granola error", "granola not working", "granola not recording",
  "fix granola", "granola troubleshoot".
allowed-tools: Read, Write, Edit, Bash(pgrep:*), Bash(ps:*), Bash(system_profiler:*), Bash(defaults:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, troubleshooting]

---
# Granola Common Errors

## Overview
Diagnose and fix the most common Granola issues. Each error includes platform-specific symptoms, root causes, and step-by-step remediation. Granola captures audio from your device's system audio output (not via meeting platform APIs), so most issues trace back to audio permissions or device configuration.

## Prerequisites
- Granola installed (even if malfunctioning)
- Terminal access for diagnostic commands (macOS) or PowerShell (Windows)
- Admin/sudo access for permission changes

## Instructions

### Step 1 — Quick Diagnostic Check
```bash
# Is Granola running?
pgrep -l Granola

# What version?
defaults read /Applications/Granola.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null

# Audio devices available
system_profiler SPAudioDataType 2>/dev/null | grep -A2 "Default Input"
```

### Step 2 — Match Your Symptom

---

## Audio / Transcription Issues

### "No Audio Captured" — Transcript is Empty

**Root cause:** Granola cannot hear system audio. On macOS, this is almost always a permissions issue.

**macOS fix:**
1. System Settings > Privacy & Security > **Screen & System Audio Recording**
2. Enable Granola (this grants system audio access despite the misleading name)
3. System Settings > Privacy & Security > **Microphone** > Enable Granola
4. **Restart Granola** after changing permissions (right-click menu bar icon > Restart)

```bash
# Nuclear option — reset Core Audio if devices are confused
sudo killall coreaudiod
# coreaudiod restarts automatically
```

**Windows fix:**
1. Settings > Privacy & Security > Microphone > Ensure Granola is enabled
2. Check that the correct audio device is set as default output
3. Right-click sound icon > Sound settings > ensure no audio enhancements are enabled

### "Transcription Starts Then Stops" (4-5 Minutes In)

**Root cause:** Granola stops transcription when it detects no new audio for ~15 minutes, or when the computer sleeps.

**Fix:**
- Keep your machine awake during meetings (disable sleep/screen lock)
- Ensure meeting audio is playing through your default output device
- Bluetooth devices can cause dropouts — try built-in speakers or wired headset
- Right-click Granola icon > **Restart Granola**, then reopen the note

### "Poor Transcription Quality"

| Cause | Fix |
|-------|-----|
| Background noise | Use noise-cancelling headset or quiet room |
| Echo/reverb | Smaller room, soft furnishings |
| Crosstalk (multiple speakers) | One person speaks at a time |
| Low mic volume | Position mic within 12 inches, check input levels |
| Non-English accents | Granola accuracy varies — speak clearly, slower |

---

## Calendar / Meeting Detection Issues

### "Meeting Not Detected"

**Symptoms:** Granola doesn't show the floating notepad when you join a call.

**Checklist:**
1. **Calendar connected?** Settings > Calendar — reconnect if expired
2. **Event has video link?** Granola only detects events with Zoom/Meet/Teams/WebEx links
3. **Right calendar synced?** Check that the meeting's calendar is in the sync list
4. **Force refresh:** Click the sync icon in Granola, wait 30 seconds
5. **Manual start:** Click Granola menu bar icon > **Start Recording** to bypass detection

### "Calendar Authentication Failed"

**Fix:**
1. Settings > Calendar > Disconnect
2. Clear browser cookies for accounts.google.com or login.microsoftonline.com
3. Reconnect calendar in a private/incognito browser window
4. If using Google Workspace with admin restrictions, IT may need to approve Granola's OAuth app

---

## Integration Errors

### Slack — "Channel Not Found" or Post Fails

1. Verify the channel exists and hasn't been renamed
2. Invite the Granola bot to the channel: `/invite @Granola`
3. Reconnect Slack at Settings > Integrations > Slack

### Notion — "Database Missing" or Share Fails

1. Granola creates its own database on first connect — don't delete it
2. Reconnect Notion: Settings > Integrations > Notion > Disconnect > Reconnect
3. Granola can only write to its own database (you cannot pick a custom database)

### HubSpot — "Contact Not Matched"

1. The attendee's email must match a HubSpot Contact record
2. Granola does **not** create new contacts automatically
3. Create the contact in HubSpot first, then re-share the note
4. For auto-creation, use Zapier with a "Find or Create Contact" action

### Zapier — "Trigger Not Firing"

1. Verify Granola connection in Zapier (reconnect if needed)
2. Check that the folder name in the trigger matches exactly
3. For "Note Added to Folder" trigger, ensure the note is actually in that folder
4. Add a 2-minute delay step — notes may still be processing when the trigger fires

---

## App Issues

### App Crashes or Freezes

```bash
# Force quit and restart
pkill -9 Granola
open -a Granola

# Clear caches if crashes persist
rm -rf ~/Library/Caches/Granola
```

### App Won't Start After Update

```bash
# Clear preferences (you'll need to re-authenticate)
defaults delete ai.granola.app 2>/dev/null
rm -rf ~/Library/Caches/Granola

# Reinstall
brew reinstall --cask granola
```

### "Processing Stuck" — Notes Never Finish

- Normal processing takes 1-2 minutes per meeting
- Wait up to 15 minutes for long meetings (2+ hours)
- Check internet connectivity
- Check [status.granola.ai](https://status.granola.ai) for service outages
- Restart Granola and reopen the note

## Output
- Root cause identified for the specific Granola issue
- Platform-specific fix applied and verified
- Meeting capture confirmed working after remediation

## Error Quick Reference

| Symptom | Most Likely Cause | First Fix |
|---------|------------------|-----------|
| No transcript | Missing Screen & System Audio permission | Grant permission, restart Granola |
| Transcript stops mid-meeting | Computer sleep or Bluetooth dropout | Keep awake, try wired audio |
| Meeting not detected | No video link in calendar event | Add conferencing link or manually start |
| Slack post missing | Bot not in channel | `/invite @Granola` |
| HubSpot sync fails | Contact doesn't exist | Create contact in HubSpot first |
| App crashes | Corrupted cache | Delete ~/Library/Caches/Granola |

## Resources
- [Transcription Troubleshooting](https://docs.granola.ai/help-center/troubleshooting/transcription-issues)
- [How Transcription Works](https://docs.granola.ai/help-center/taking-notes/how-transcription-works)
- [Granola Status Page](https://status.granola.ai)
- [Granola Updates (Known Issues)](https://www.granola.ai/updates)

## Next Steps
Proceed to `granola-debug-bundle` for creating comprehensive diagnostic reports.
