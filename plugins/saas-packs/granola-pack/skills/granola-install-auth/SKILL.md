---
name: granola-install-auth
description: |
  Install and configure Granola AI meeting notes app with calendar integration.
  Use when setting up Granola for the first time, connecting calendar accounts,
  or configuring audio capture permissions.
  Trigger with phrases like "install granola", "setup granola",
  "granola calendar", "configure granola", "granola permissions".
allowed-tools: Read, Write, Edit, Bash(brew:*), Bash(open:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Install & Auth

## Overview
Set up Granola AI meeting notes app and configure calendar integration for automatic meeting capture.

## Prerequisites
- macOS 12+ or Windows 10+ (or iPhone for mobile)
- Google Calendar or Microsoft Outlook account
- Microphone permissions enabled
- Stable internet connection

## Instructions

### Step 1: Download Granola
```bash
# macOS via Homebrew (if available)
brew install --cask granola

# Or download directly from https://granola.ai/download
open https://granola.ai/download
```

### Step 2: Create Account
1. Open Granola application
2. Click "Sign up" or "Log in"
3. Authenticate with Google or Microsoft account
4. Grant calendar access permissions

### Step 3: Configure Audio Permissions
```
macOS:
System Preferences > Security & Privacy > Privacy > Microphone
- Enable Granola

Windows:
Settings > Privacy > Microphone
- Allow Granola to access microphone
```

### Step 4: Connect Calendar
1. In Granola settings, go to "Integrations"
2. Connect Google Calendar or Outlook
3. Select which calendars to sync
4. Enable automatic meeting detection

### Step 5: Verify Setup
1. Schedule a test meeting
2. Start the meeting
3. Confirm Granola shows "Recording" indicator
4. End meeting and verify notes generated

## Output
- Granola app installed and configured
- Calendar connected with meeting sync enabled
- Audio permissions granted
- Test meeting successfully captured

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Audio Not Captured | Microphone permission denied | Grant microphone access in system settings |
| Calendar Not Syncing | OAuth token expired | Disconnect and reconnect calendar |
| App Won't Start | Outdated OS version | Update to macOS 12+ or Windows 10+ |
| No Meeting Detected | Calendar not connected | Verify calendar integration in settings |

## Examples

### macOS Quick Setup
```bash
# Download and open Granola
open https://granola.ai/download

# After installation, grant permissions
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
```

### Verify Installation
```bash
# Check if Granola is running (macOS)
pgrep -l Granola

# Check app location
ls -la /Applications/Granola.app
```

## Resources
- [Granola Download](https://granola.ai/download)
- [Granola Getting Started](https://granola.ai/help)
- [Granola Updates](https://granola.ai/updates)

## Next Steps
After successful installation, proceed to `granola-hello-world` for your first meeting capture.