---
name: twinmind-install-auth
description: |
  Install and configure TwinMind Chrome extension, mobile app, and API access.
  Use when setting up TwinMind for meeting transcription, configuring calendar
  integration, or initializing TwinMind in your workflow.
  Trigger with phrases like "install twinmind", "setup twinmind",
  "twinmind auth", "configure twinmind", "twinmind chrome extension".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Install & Auth

## Overview
Set up TwinMind meeting AI across Chrome extension, mobile apps, and API integration.

## Prerequisites
- Chrome browser (latest version) for extension
- iOS 15+ or Android 10+ for mobile apps
- Google account for calendar integration
- TwinMind account (Free, Pro, or Enterprise)

## Instructions

### Step 1: Install Chrome Extension

1. Visit Chrome Web Store:
```
https://chromewebstore.google.com/detail/twinmind-chat-with-tabs-m/agpbjhhcmoanaljagpoheldgjhclepdj
```

2. Click "Add to Chrome" and confirm permissions

3. Pin the extension to your toolbar for quick access

### Step 2: Create Account & Authenticate

1. Click the TwinMind extension icon
2. Sign up with Google or email
3. Complete onboarding questionnaire for personalization

### Step 3: Configure Calendar Integration

```javascript
// TwinMind automatically syncs with authorized calendars
// After OAuth, meetings appear in the extension sidebar

// Calendar integration provides:
// - Meeting participant names
// - Meeting agenda/description
// - Automatic transcription start/stop
```

Authorize calendars in Settings > Integrations:
- Google Calendar (recommended)
- Microsoft Outlook
- Apple Calendar

### Step 4: Configure Audio Permissions

Grant microphone access when prompted:
- Chrome: Settings > Privacy > Microphone
- macOS: System Preferences > Security > Microphone
- Windows: Settings > Privacy > Microphone

### Step 5: Install Mobile App (Optional)

**iOS:**
```
https://apps.apple.com/us/app/twinmind-ai-notes-memory/id6504585781
```

**Android:**
```
https://play.google.com/store/apps/details?id=ai.twinmind.android
```

### Step 6: Configure API Access (Pro/Enterprise)

```bash
set -euo pipefail
# Set environment variable for API access
export TWINMIND_API_KEY="your-api-key"

# Or create .env file
echo 'TWINMIND_API_KEY=your-api-key' >> .env

# Verify API access
curl -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health
```

### Step 7: Verify Installation

```javascript
// Test transcription with a short recording
// 1. Start a test meeting or voice memo
// 2. Click TwinMind extension
// 3. Click "Start Transcribing"
// 4. Speak for 10-15 seconds
// 5. Click "Stop" and verify transcript appears
```

## Output
- Chrome extension installed and authenticated
- Calendar integration configured
- Mobile apps installed (optional)
- API key configured (Pro/Enterprise)
- Test transcription successful

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Microphone access denied | Permissions not granted | Enable in browser/OS settings |
| Calendar sync failed | OAuth token expired | Re-authorize in Settings |
| Extension not loading | Browser compatibility | Update Chrome to latest version |
| API key invalid | Incorrect or expired key | Regenerate key in TwinMind dashboard |
| Transcription not starting | Audio source not detected | Check microphone selection |

## Platform-Specific Notes

### macOS
```bash
# Check microphone permissions
tccutil list com.google.Chrome
```

### Windows
- Ensure "Allow apps to access microphone" is enabled
- Add Chrome to allowed apps list

### Linux
```bash
# Check PulseAudio is running
pulseaudio --check
pactl list sources | grep -i "name:"
```

## Account Tiers

| Feature | Free | Pro ($10/mo) | Enterprise |
|---------|------|--------------|------------|
| Transcription | Unlimited | Unlimited | Unlimited |
| Languages | 140+ | 140+ (premium quality) | 140+ (premium) |
| AI Models | Basic | GPT-4, Claude, Gemini | Custom models |
| Context Tokens | 500K | 2M | Unlimited |
| Support | Community | 24-hour | Dedicated |
| On-premise | No | No | Yes |

## Resources
- [TwinMind Website](https://twinmind.com)
- [Chrome Extension Tutorial](https://twinmind.com/ce-tutorial)
- [iOS App Store](https://apps.apple.com/us/app/twinmind-ai-notes-memory/id6504585781)
- [Android Play Store](https://play.google.com/store/apps/details?id=ai.twinmind.android)

## Next Steps
After successful setup, proceed to `twinmind-hello-world` for your first meeting transcription.

## Examples

**Basic usage**: Apply twinmind install auth to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind install auth for production environments with multiple constraints and team-specific requirements.