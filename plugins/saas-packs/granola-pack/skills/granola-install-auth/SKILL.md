---
name: granola-install-auth
description: |
  Install and configure Granola AI meeting notes with calendar and audio permissions.
  Use when setting up Granola for the first time, connecting Google/Outlook calendars,
  granting macOS Screen Recording permission, or configuring Windows audio capture.
  Trigger: "install granola", "setup granola", "granola calendar", "granola permissions".
allowed-tools: Read, Write, Edit, Bash(brew:*), Bash(open:*), Bash(pgrep:*), Bash(defaults:*), Bash(ls:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, granola-install]

---
# Granola Install & Auth

## Overview
Install Granola, the AI notepad that captures meeting audio directly from your device (no bot joins the call), transcribes with GPT-4o/Claude, and produces structured notes with action items. Supports Zoom, Google Meet, Teams, Slack Huddles, and WebEx.

## Prerequisites
- macOS 12+ or Windows 10+ (iOS/Android for mobile)
- Google Calendar or Microsoft Outlook account
- Active internet connection for initial auth

## Instructions

### Step 1 — Download and Install

```bash
# macOS via Homebrew
brew install --cask granola

# Or download directly
open "https://www.granola.ai/download"
```

Windows: download the installer from `granola.ai/download` and run the `.exe`.

### Step 2 — Create Account and Authenticate

1. Launch Granola
2. Click **Sign up** — authenticate with Google or Microsoft
3. Granola uses WorkOS for SSO; enterprise users may see their IdP login (Okta, Azure AD)

### Step 3 — Grant System Permissions

**macOS (critical — both required):**
```
System Settings > Privacy & Security > Microphone
  → Enable Granola

System Settings > Privacy & Security > Screen & System Audio Recording
  → Enable Granola
```
The Screen Recording permission is required because macOS bundles system audio capture under that category — Granola does **not** record your screen.

**Windows:**
Microphone permissions are granted automatically. Confirm at:
```
Settings > Privacy & Security > Microphone → Granola enabled
```

### Step 4 — Connect Calendar

1. Granola Settings (avatar bottom-left) > **Calendar**
2. Connect Google Calendar or Microsoft Outlook
3. Select which calendars to sync (personal, work, shared)
4. Granola detects meetings from synced calendars with video/conference links

### Step 5 — Verify Audio Capture

```bash
# macOS — confirm Granola is running
pgrep -l Granola

# Check installed version
defaults read /Applications/Granola.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo "Check Granola > About"
```

Join or start any meeting (Zoom, Meet, Teams). Granola shows a floating notepad when it detects a calendar event with a conferencing link. Verify the live transcription indicator appears.

### Step 6 — Configure Preferences

| Setting | Location | Recommended |
|---------|----------|-------------|
| Auto-start with calendar | Preferences > General | On |
| Default template | Preferences > Templates | Match your meeting type |
| AI model | Uses GPT-4o/Claude | No configuration needed |
| Auto-update | Preferences > General | On |

## Output
- Granola installed and running on login
- Calendar connected with meeting auto-detection
- System audio + microphone permissions granted
- Live transcription verified on a test call

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| No audio captured | Missing Screen & System Audio permission (macOS) | System Settings > Privacy & Security > Screen & System Audio Recording > enable Granola, then restart |
| Calendar not syncing | OAuth token expired or wrong account | Disconnect calendar in Settings, re-authenticate |
| App won't launch | macOS Gatekeeper block | Right-click Granola.app > Open, or `xattr -cr /Applications/Granola.app` |
| Meeting not detected | Event has no video link | Add a Zoom/Meet/Teams link to the calendar event |
| Bluetooth audio drops | BT device causes transcription stops | Switch to built-in mic or wired headset |

## Granola Architecture (How It Works)
```
Your Device Audio ──→ Granola Desktop App ──→ Granola Cloud (transcription)
                           │                        │
                     Local notepad            GPT-4o / Claude
                     (your typed notes)       (enhance + summarize)
                           │                        │
                           └────── Merged Output ───┘
                                   │
                          Structured meeting notes
                          with action items
```
- Audio is transcribed server-side; Granola does **not** store raw audio after processing
- Your typed notes are merged with the transcript for context-aware summaries
- No bot joins your meeting — capture happens via system audio

## Resources
- [Download Granola](https://www.granola.ai/download)
- [Setup Guide](https://docs.granola.ai/help-center/getting-started/setting-up-granola-for-the-first-time)
- [Transcription Troubleshooting](https://docs.granola.ai/help-center/troubleshooting/transcription-issues)
- [Security Standards](https://docs.granola.ai/help-center/consent-security-privacy/our-security-standards)

## Next Steps
After installation, proceed to `granola-hello-world` for your first meeting capture.
