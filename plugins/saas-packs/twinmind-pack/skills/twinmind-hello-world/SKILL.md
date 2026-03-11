---
name: twinmind-hello-world
description: |
  Create your first TwinMind meeting transcription and AI summary.
  Use when starting with TwinMind, testing your setup,
  or learning basic transcription and summary patterns.
  Trigger with phrases like "twinmind hello world", "first twinmind meeting",
  "twinmind quick start", "test twinmind transcription".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Hello World

## Overview
Create your first meeting transcription with AI-generated summary and action items.

## Prerequisites
- Completed `twinmind-install-auth` setup
- Chrome extension authenticated
- Microphone permissions granted
- Active internet connection

## Instructions

### Step 1: Start a Test Meeting

Option A - Browser Meeting:
1. Open Google Meet, Zoom, or Teams in browser
2. Start or join a test call
3. Click TwinMind extension icon
4. Click "Start Transcribing"

Option B - Voice Memo:
1. Click TwinMind extension icon
2. Select "Voice Memo" mode
3. Click the microphone button
4. Start speaking

### Step 2: Speak Test Content

For a meaningful test, speak for 30-60 seconds covering:
```
"Welcome to today's project status meeting.
We have three items on the agenda.

First, the mobile app launch is scheduled for next Friday.
Sarah will handle the App Store submission.

Second, we need to review the Q1 budget.
John, please send the spreadsheet by Wednesday.

Third, the customer feedback survey shows 85% satisfaction.
We should schedule a follow-up meeting next week to discuss improvements."
```

### Step 3: Stop and Generate Summary

1. Click "Stop Transcribing" button
2. Wait for processing (5-10 seconds)
3. TwinMind automatically generates:
   - Full transcript with timestamps
   - Meeting summary
   - Action items with owners
   - Key discussion points

### Step 4: Review Output

Expected transcript output:
```
[00:00] Welcome to today's project status meeting...
[00:05] We have three items on the agenda...
[00:12] First, the mobile app launch is scheduled for next Friday...
[00:18] Sarah will handle the App Store submission...
```

Expected AI summary:
```
## Meeting Summary
Project status meeting covering mobile app launch, Q1 budget review,
and customer feedback analysis.

## Action Items
- [ ] Sarah: Submit app to App Store (Due: Friday)
- [ ] John: Send Q1 budget spreadsheet (Due: Wednesday)
- [ ] Team: Schedule follow-up meeting for feedback discussion

## Key Points
- Mobile app launching next Friday
- Customer satisfaction at 85%
- Budget review pending
```

### Step 5: Access Memory Vault

After the meeting:
```javascript
// TwinMind stores transcripts in your Memory Vault
// Access via extension sidebar or ask AI:

"What did we discuss about the mobile app launch?"
"Who is responsible for the budget spreadsheet?"
"When is the next meeting scheduled?"
```

### Step 6: Test Cross-Platform Sync (Optional)

1. Open TwinMind mobile app
2. Sign in with same account
3. Verify transcript appears in app
4. Test AI queries on mobile

## Output
- Complete meeting transcript with timestamps
- AI-generated summary document
- Extracted action items with assignees
- Content indexed in Memory Vault
- Console output showing:
```
Transcription complete!
Duration: 1m 23s
Words: 156
Speakers: 1
Language: English
AI Summary: Generated
Action Items: 3 extracted
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No audio detected | Microphone not selected | Check audio input settings |
| Transcript empty | Audio too quiet | Increase microphone volume |
| Summary not generated | Processing timeout | Retry or check network |
| Speaker labels wrong | Single speaker test | Use multi-speaker content |
| Sync failed | Network interruption | Check connection, retry |

## Understanding the Output

### Transcript Quality Metrics
```javascript
// TwinMind uses Ear-3 model with:
// - 5.26% Word Error Rate (industry-leading)
// - 3.8% Diarization Error Rate
// - 140+ language support

// Quality indicators in UI:
// - Green: High confidence (>95%)
// - Yellow: Medium confidence (80-95%)
// - Red: Low confidence (<80%)
```

### AI Model Selection
TwinMind routes queries to optimal models:
- Summaries: GPT-4 or Claude
- Quick answers: Gemini Flash
- Memory search: Custom embeddings

## Examples

### Quick Voice Memo
```javascript
// Perfect for capturing ideas on the go
// 1. Click extension
// 2. Voice memo mode
// 3. Speak thought
// 4. Auto-transcribed and indexed

"Note to self: Follow up with the design team about
the new color palette before Thursday's review."

// Result: Indexed, searchable, reminded via calendar
```

### Meeting with Multiple Speakers
```javascript
// TwinMind automatically labels speakers
// Speaker diarization identifies who said what

// Output format:
// [Speaker 1 - 00:00]: "Let's start the standup..."
// [Speaker 2 - 00:15]: "I completed the API integration..."
// [Speaker 1 - 00:32]: "Great work. Any blockers?"
```

## Resources
- [TwinMind Chrome Extension Tutorial](https://twinmind.com/ce-tutorial)
- [TwinMind Documentation](https://twinmind.com)
- [Ear-3 Model Details](https://twinmind.com/ear-3)

## Next Steps
Proceed to `twinmind-local-dev-loop` for development workflow integration.