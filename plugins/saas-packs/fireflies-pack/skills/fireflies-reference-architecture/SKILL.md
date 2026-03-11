---
name: fireflies-reference-architecture
description: |
  Implement Fireflies.ai reference architecture with best-practice project layout.
  Use when designing new Fireflies.ai integrations, reviewing project structure,
  or establishing architecture standards for Fireflies.ai applications.
  Trigger with phrases like "fireflies architecture", "fireflies best practices",
  "fireflies project structure", "how to organize fireflies", "fireflies layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Fireflies.ai Reference Architecture

## Overview
Production architecture for meeting intelligence with Fireflies.ai. Covers transcript processing pipelines, CRM integration, action item extraction, and meeting analytics dashboards using the GraphQL API.

## Prerequisites
- Fireflies.ai API key with GraphQL access
- GraphQL client (`graphql-request` or `urql`)
- CRM system for action item sync (optional)
- Database for transcript storage

## Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│              Meeting Sources                          │
│  Zoom │ Google Meet │ Teams │ Dialpad │ Phone        │
└──────────┬───────────────────────────────┬───────────┘
           │                               │
           ▼                               ▼
┌──────────────────────┐     ┌─────────────────────────┐
│  Fireflies.ai Bot    │     │  Upload API             │
│  (auto-join meetings)│     │  (manual recordings)    │
└──────────┬───────────┘     └──────────┬──────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────────────────────────────────────┐
│              Fireflies Processing                     │
│  Transcription │ Speaker ID │ AI Summary │ Actions   │
└──────────────────────────┬───────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌──────────────┐ ┌────────┐ ┌──────────────┐
     │ Transcript   │ │ Action │ │ Webhook      │
     │ Storage      │ │ Items  │ │ Events       │
     │ (DB/Search)  │ │ (CRM)  │ │ (Real-time)  │
     └──────────────┘ └────────┘ └──────────────┘
```

## Instructions

### Step 1: GraphQL Client Setup
```typescript
import { GraphQLClient } from 'graphql-request';

const fireflies = new GraphQLClient('https://api.fireflies.ai/graphql', {
  headers: { Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}` },
});

// Fetch recent transcripts
const GET_TRANSCRIPTS = `
  query GetTranscripts($limit: Int) {
    transcripts(limit: $limit) {
      id title date duration
      organizer_email participants
      summary { overview action_items keywords }
    }
  }
`;

async function getRecentMeetings(limit = 20) {
  const data = await fireflies.request(GET_TRANSCRIPTS, { limit });
  return data.transcripts;
}
```

### Step 2: Transcript Processing Pipeline
```typescript
const GET_FULL_TRANSCRIPT = `
  query GetTranscript($id: String!) {
    transcript(id: $id) {
      id title
      sentences {
        speaker_name text
        start_time end_time
      }
      summary { overview action_items keywords }
      meeting_attendees { displayName email }
    }
  }
`;

interface ProcessedMeeting {
  id: string;
  title: string;
  attendees: string[];
  actionItems: string[];
  keyTopics: string[];
  speakerBreakdown: Record<string, number>;
}

async function processMeeting(id: string): Promise<ProcessedMeeting> {
  const { transcript } = await fireflies.request(GET_FULL_TRANSCRIPT, { id });

  const speakerTime: Record<string, number> = {};
  for (const s of transcript.sentences) {
    const duration = s.end_time - s.start_time;
    speakerTime[s.speaker_name] = (speakerTime[s.speaker_name] || 0) + duration;
  }

  return {
    id: transcript.id,
    title: transcript.title,
    attendees: transcript.meeting_attendees.map((a: any) => a.email),
    actionItems: transcript.summary.action_items || [],
    keyTopics: transcript.summary.keywords || [],
    speakerBreakdown: speakerTime,
  };
}
```

### Step 3: Webhook Integration
```typescript
import express from 'express';
const app = express();

app.post('/webhooks/fireflies', express.json(), async (req, res) => {
  const { event_type, meeting_id, transcript_id } = req.body;

  if (event_type === 'Transcription completed') {
    const meeting = await processMeeting(transcript_id);

    // Sync action items to CRM
    for (const item of meeting.actionItems) {
      await createCRMTask(item, meeting.attendees);
    }
  }

  res.json({ received: true });
});
```

### Step 4: Meeting Analytics Aggregation
```typescript
async function weeklyMeetingReport() {
  const meetings = await getRecentMeetings(50);
  const oneWeekAgo = Date.now() - 7 * 86400000;  # 86400000 = configured value

  const recent = meetings.filter(
    (m: any) => new Date(m.date).getTime() > oneWeekAgo
  );

  return {
    totalMeetings: recent.length,
    totalHours: recent.reduce((s: number, m: any) => s + m.duration / 3600, 0).toFixed(1),  # 3600: timeout: 1 hour
    topAttendees: countAttendees(recent).slice(0, 5),
    actionItemCount: recent.reduce((s: number, m: any) =>
      s + (m.summary?.action_items?.length || 0), 0),
  };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Empty transcript | Meeting too short | Check minimum duration before processing |
| Missing speakers | Speaker diarization failed | Fall back to participant list |
| GraphQL rate limit | Too many queries | Batch requests, cache transcripts |
| Webhook not firing | URL not configured | Verify in Fireflies dashboard settings |

## Examples

### Quick Meeting Search
```typescript
async function searchMeetings(keyword: string) {
  const meetings = await getRecentMeetings(100);
  return meetings.filter((m: any) =>
    m.title?.toLowerCase().includes(keyword.toLowerCase()) ||
    m.summary?.keywords?.some((k: string) => k.toLowerCase().includes(keyword))
  );
}
```

## Resources
- [Fireflies GraphQL API](https://docs.fireflies.ai/graphql)
- [Fireflies Webhooks](https://docs.fireflies.ai/webhooks)
- [Fireflies Integrations](https://fireflies.ai/integrations)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale