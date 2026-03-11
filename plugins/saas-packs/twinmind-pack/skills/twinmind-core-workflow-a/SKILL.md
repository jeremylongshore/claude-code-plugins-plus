---
name: twinmind-core-workflow-a
description: |
  Execute TwinMind primary workflow: Meeting transcription and summary generation.
  Use when implementing meeting capture, building transcription features,
  or automating meeting documentation.
  Trigger with phrases like "twinmind transcription workflow",
  "meeting transcription", "capture meeting with twinmind".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Core Workflow A: Meeting Transcription & Summary

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Primary workflow for capturing meetings, generating transcripts with speaker diarization, and creating AI summaries with action items.

## Prerequisites
- Completed `twinmind-install-auth` setup
- TwinMind Pro/Enterprise for API access
- Valid API credentials configured
- Audio source available (live or file)

## Instructions

### Step 1: Initialize Meeting Capture
Build a `MeetingCapture` class with `startLiveCapture()` for real-time recording and `transcribeRecording()` for file-based transcription. Use Ear-3 model with auto language detection and speaker diarization.

### Step 2: Generate AI Summary
Create a `SummaryGenerator` with `generateSummary()` (brief/detailed/bullet-points formats), `generateFollowUpEmail()`, and `generateMeetingNotes()` methods.

### Step 3: Handle Speaker Identification
Build a `SpeakerManager` that extracts speakers from transcript segments, calculates speaking time per speaker, and optionally matches speakers to calendar attendees.

### Step 4: Orchestrate Complete Workflow
Wire everything together in `processMeeting()`: transcribe audio, then generate summary and identify speakers in parallel, optionally produce follow-up email and meeting notes.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete MeetingCapture, SummaryGenerator, SpeakerManager, and orchestration code.

## Output
- Complete meeting transcript with timestamps
- Speaker-labeled segments
- AI-generated summary
- Extracted action items with assignees
- Optional follow-up email draft
- Optional formatted meeting notes

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Transcription timeout | Large audio file | Increase maxWaitMs or use async callback |
| Speaker match failed | No calendar data | Provide attendees list manually |
| Summary generation failed | Transcript too short | Ensure minimum 30s of audio |
| Audio format unsupported | Wrong codec | Convert to MP3/WAV/M4A |
| Rate limit exceeded | Too many requests | Implement queue-based processing |

## Examples


**Basic usage**: Apply twinmind core workflow a to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind core workflow a for production environments with multiple constraints and team-specific requirements.

## Audio Format Support

| Format | Supported | Notes |
|--------|-----------|-------|
| MP3 | Yes | Recommended |
| WAV | Yes | Best quality |
| M4A | Yes | iOS recordings |
| WebM | Yes | Browser recordings |

## Resources
- [TwinMind Transcription API](https://twinmind.com/docs/transcription)
- [Ear-3 Model Details](https://twinmind.com/ear-3)
- [Audio Format Guide](https://twinmind.com/docs/audio-formats)

## Next Steps
For action item extraction and follow-up automation, see `twinmind-core-workflow-b`.