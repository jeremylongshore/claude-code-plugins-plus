---
name: granola-hello-world
description: |
  Capture your first meeting with Granola and review AI-generated notes.
  Use when testing Granola setup, learning the interface,
  or understanding how meeting capture works.
  Trigger with phrases like "granola hello world", "first granola meeting",
  "granola test", "granola quick start", "try granola".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Hello World

## Overview
Capture your first meeting with Granola and understand how AI-generated notes work.

## Prerequisites
- Completed `granola-install-auth` setup
- Calendar connected and syncing
- Microphone permissions granted
- Scheduled meeting (or create a test one)

## Instructions

### Step 1: Start a Meeting
1. Join any video call (Zoom, Google Meet, Teams, etc.)
2. Granola automatically detects the meeting from your calendar
3. Click "Start Recording" if auto-start is disabled

### Step 2: Take Live Notes (Optional)
During the meeting:
1. Open Granola notepad panel
2. Type key points or action items
3. Granola enhances notes with transcript context

### Step 3: End Meeting
1. End your video call
2. Granola processes the audio (typically 1-2 minutes)
3. Review the generated notes

### Step 4: Review AI Notes
1. Open Granola app
2. Find your meeting in the recent list
3. Review:
   - Meeting summary
   - Key discussion points
   - Action items extracted
   - Full transcript (expandable)

## Output
- Complete meeting notes with AI summary
- Key points and action items extracted
- Full searchable transcript
- Your manual notes enhanced with context

## Example Output
```markdown
# Team Standup - January 6, 2025

## Summary
Discussed Q1 priorities and sprint planning. Agreed to focus on
customer onboarding improvements.

## Key Points
- Sprint 23 completed with 15/18 story points
- Customer feedback indicates onboarding friction
- New design mockups ready for review Thursday

## Action Items
- [ ] @sarah: Schedule design review meeting
- [ ] @mike: Create onboarding improvement tickets
- [ ] @team: Review Q1 OKRs by Friday

## Participants
Sarah Chen, Mike Johnson, Alex Kim
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| No Audio Captured | Wrong audio source | Check system audio settings |
| Meeting Not Detected | Calendar event missing | Manually start recording |
| Processing Failed | Audio quality issues | Ensure stable internet during meeting |
| Notes Empty | Meeting too short | Minimum ~2 minutes required |

## Tips for Better Notes
1. **Speak clearly** - AI transcription improves with clear audio
2. **Use participant names** - Helps with speaker identification
3. **State action items explicitly** - "Action item: Sarah will..."
4. **Summarize at end** - Recap key decisions verbally

## Resources
- [Granola Note Templates](https://granola.ai/templates)
- [Granola Tips](https://granola.ai/tips)
- [Meeting Best Practices](https://granola.ai/blog)

## Next Steps
Proceed to `granola-local-dev-loop` for development workflow integration.

## Examples

**Basic usage**: Apply granola hello world to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola hello world for production environments with multiple constraints and team-specific requirements.