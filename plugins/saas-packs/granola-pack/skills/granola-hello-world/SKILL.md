---
name: granola-hello-world
description: |
  Capture your first meeting with Granola and review AI-enhanced notes.
  Use when testing Granola setup, learning the notepad + transcript flow,
  or understanding how Enhance Notes and Granola Chat work.
  Trigger: "granola hello world", "first granola meeting", "try granola", "granola test".
allowed-tools: Read, Write, Edit, Bash(pgrep:*), Bash(open:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, getting-started]

---
# Granola Hello World

## Overview
Capture your first meeting with Granola and learn the three-phase workflow: live notepad, Enhance Notes, and Granola Chat. Granola captures audio from your device (no bot joins), transcribes it, and merges your typed notes with the full transcript to produce structured output.

## Prerequisites
- Completed `granola-install-auth` setup
- Calendar connected with an upcoming meeting (or create a test one)
- Microphone + Screen & System Audio permissions granted

## Instructions

### Step 1 — Start a Meeting
1. Join any video call — Zoom, Google Meet, Teams, Slack Huddle, or WebEx
2. Granola auto-detects the meeting from your synced calendar
3. A floating notepad appears showing the meeting title and attendees
4. If auto-detection fails, click the Granola icon in your menu bar and select **Start Recording**

### Step 2 — Take Live Notes in the Notepad
During the meeting, type rough notes directly in the Granola notepad:
```markdown
- discussed Q1 priorities
- sarah owns onboarding revamp
- need design review by thursday
- budget question - follow up with finance
```
These notes give Granola context. The AI uses your notes **plus** the full transcript to produce better output — you do not need to capture everything.

### Step 3 — End Meeting and Enhance
1. End your video call
2. Granola processes the transcript (typically 1-2 minutes)
3. Click **Enhance Notes** — Granola merges your notes with the transcript
4. Select a template (or use the default) to structure the output

### Step 4 — Review Enhanced Output
Granola produces structured notes based on your template:

```markdown
# Team Standup — March 22, 2026

## Summary
Discussed Q1 priorities. Agreed to focus on customer onboarding
improvements. Sarah will lead the initiative with a design review
by Thursday.

## Key Decisions
- Onboarding revamp is the top priority for Q1
- Budget approval needed from Finance before expanding scope

## Action Items
- [ ] @sarah: Schedule design review meeting by Thursday
- [ ] @mike: Create onboarding improvement tickets in Linear
- [ ] @alex: Follow up with Finance on budget allocation

## Participants
Sarah Chen, Mike Johnson, Alex Kim
```

### Step 5 — Use Granola Chat
After enhancement, use the chat panel to ask questions about the meeting:
- "List my action items"
- "Draft a follow-up email to the attendees"
- "What were the open questions?"
- "Summarize the budget discussion"

Granola Chat has full context of the transcript and your notes.

### Step 6 — Use Recipes for Repeatable Prompts
Type `/` in Granola Chat to invoke Recipes — saved prompts for common tasks:
- `/standup` — extract blockers and progress updates
- `/follow-up` — draft a follow-up email
- `/action-items` — list all action items with owners
- Create custom recipes for your team's workflows

## Output
- Complete meeting notes with AI-generated summary
- Key decisions and action items extracted with owners
- Full searchable transcript (expandable in the note)
- Granola Chat available for post-meeting queries

## Tips for Better Notes
1. **Type key points during the meeting** — even rough notes dramatically improve output
2. **State names when assigning actions** — "Action item: Sarah will schedule the review"
3. **Use explicit action language** — "We decided...", "Next step is..."
4. **Summarize decisions verbally** — the AI picks up on decision language
5. **One speaker at a time** — reduces transcription errors

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| No transcript generated | Wrong audio device selected | Check System Settings > Sound > Input matches your meeting audio |
| Meeting not detected | Calendar event missing video link | Add Zoom/Meet/Teams link to event, or manually start recording |
| Processing stuck > 5 min | Connectivity issue | Check internet, restart Granola (right-click icon > Restart) |
| Empty enhanced notes | Meeting < 2 minutes | Granola needs sufficient audio for meaningful enhancement |
| Poor transcription | Background noise or crosstalk | Use headset, mute when not speaking |

## People & Companies (Automatic)
After your first meeting, check the **People** and **Companies** views in the sidebar. Granola automatically:
- Creates contact entries from calendar attendees
- Enriches with job titles, profile photos, and company info
- Links all past meeting notes to each person
- Lets you review full conversation history before follow-ups

## Resources
- [How Transcription Works](https://docs.granola.ai/help-center/taking-notes/how-transcription-works)
- [Customize Notes with Templates](https://docs.granola.ai/help-center/taking-notes/customise-notes-with-templates)
- [Granola Chat & Recipes](https://www.granola.ai/blog/say-hello-to-recipes)
- [People and Companies](https://docs.granola.ai/help-center/people-and-companies)

## Next Steps
Proceed to `granola-core-workflow-a` for meeting template setup and preparation workflows.
