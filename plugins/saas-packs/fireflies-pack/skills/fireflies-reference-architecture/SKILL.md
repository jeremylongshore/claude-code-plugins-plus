---
name: fireflies-reference-architecture
description: |
  Design meeting intelligence architecture with Fireflies.ai GraphQL API, webhooks, and CRM sync.
  Use when designing new integrations, planning transcript pipelines,
  or establishing architecture for meeting analytics platforms.
  Trigger with phrases like "fireflies architecture", "fireflies design",
  "fireflies project structure", "meeting intelligence pipeline".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, architecture]

---
# Fireflies.ai Reference Architecture

## Overview
Production architecture for meeting intelligence using Fireflies.ai. Event-driven pipeline: meetings are recorded by the Fireflies bot, transcripts arrive via webhook, then are processed for action items, analytics, and CRM sync.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│              Meeting Sources                          │
│  Zoom  │  Google Meet  │  MS Teams  │  Upload API    │
└──────────┬───────────────────────────────┬───────────┘
           │ Bot auto-joins                │ uploadAudio
           ▼                               ▼
┌──────────────────────────────────────────────────────┐
│              Fireflies.ai Platform                    │
│  Transcription → Speaker ID → AI Summary → Actions   │
└───────────────────────┬──────────────────────────────┘
                        │ Webhook: "Transcription completed"
                        │ Payload: { meetingId, eventType }
                        ▼
┌──────────────────────────────────────────────────────┐
│              Your Webhook Receiver                    │
│  1. Verify x-hub-signature (HMAC-SHA256)             │
│  2. ACK 200 immediately                              │
│  3. Queue for async processing                       │
└───────────────────────┬──────────────────────────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
   ┌──────────────┐ ┌────────┐ ┌──────────────┐
   │ Transcript   │ │ Action │ │ Analytics    │
   │ Storage      │ │ Items  │ │ Engine       │
   │ (DB/Search)  │ │ (CRM)  │ │ (Dashboards) │
   └──────────────┘ └────────┘ └──────────────┘
```

## Core Components

### 1. GraphQL Client Layer
```typescript
// lib/fireflies.ts
const FIREFLIES_API = "https://api.fireflies.ai/graphql";

export async function firefliesQuery(query: string, variables?: any) {
  const res = await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({ query, variables }),
  });
  const json = await res.json();
  if (json.errors) throw new Error(json.errors[0].message);
  return json.data;
}
```

### 2. Webhook Processor
```typescript
// services/webhook-processor.ts
import crypto from "crypto";

interface TranscriptEvent {
  meetingId: string;
  eventType: string;
  clientReferenceId?: string;
}

export async function processWebhookEvent(event: TranscriptEvent) {
  // Fetch full transcript
  const { transcript } = await firefliesQuery(`
    query($id: String!) {
      transcript(id: $id) {
        id title date duration
        organizer_email
        speakers { id name }
        sentences {
          speaker_name text start_time end_time
          ai_filters { task question sentiment }
        }
        summary { overview action_items keywords topics_discussed }
        meeting_attendees { displayName email }
        analytics {
          sentiments { positive_pct negative_pct neutral_pct }
          speakers { name duration word_count questions words_per_minute }
        }
      }
    }
  `, { id: event.meetingId });

  // Process in parallel
  await Promise.all([
    storeTranscript(transcript),
    syncActionItems(transcript),
    updateAnalytics(transcript),
  ]);

  return transcript;
}
```

### 3. Transcript Storage
```typescript
// services/transcript-store.ts
interface StoredMeeting {
  firefliesId: string;
  title: string;
  date: string;
  duration: number;
  speakers: string[];
  overview: string;
  actionItems: string[];
  keywords: string[];
  sentiment: { positive: number; negative: number; neutral: number };
}

async function storeTranscript(transcript: any): Promise<StoredMeeting> {
  const meeting: StoredMeeting = {
    firefliesId: transcript.id,
    title: transcript.title,
    date: transcript.date,
    duration: transcript.duration,
    speakers: transcript.speakers.map((s: any) => s.name),
    overview: transcript.summary?.overview || "",
    actionItems: transcript.summary?.action_items || [],
    keywords: transcript.summary?.keywords || [],
    sentiment: {
      positive: transcript.analytics?.sentiments?.positive_pct || 0,
      negative: transcript.analytics?.sentiments?.negative_pct || 0,
      neutral: transcript.analytics?.sentiments?.neutral_pct || 0,
    },
  };

  // Store in your database
  await db.meetings.upsert({ where: { firefliesId: meeting.firefliesId }, data: meeting });
  return meeting;
}
```

### 4. Action Item Sync
```typescript
// services/action-items.ts
async function syncActionItems(transcript: any) {
  const items = transcript.summary?.action_items || [];
  if (items.length === 0) return;

  const attendees = transcript.meeting_attendees?.map((a: any) => a.email) || [];

  for (const item of items) {
    await taskManager.create({
      title: item.slice(0, 200),
      source: `Fireflies: ${transcript.title}`,
      meetingId: transcript.id,
      meetingDate: transcript.date,
      participants: attendees,
    });
  }

  console.log(`Synced ${items.length} action items from "${transcript.title}"`);
}
```

### 5. Meeting Analytics
```typescript
// services/analytics.ts
async function buildWeeklyReport() {
  const since = new Date(Date.now() - 7 * 86400000).toISOString();

  const data = await firefliesQuery(`
    query($fromDate: DateTime) {
      transcripts(fromDate: $fromDate, limit: 100) {
        id title date duration
        participants
        summary { action_items keywords }
        analytics {
          speakers { name duration word_count }
          sentiments { positive_pct }
        }
      }
    }
  `, { fromDate: since });

  const meetings = data.transcripts;
  return {
    totalMeetings: meetings.length,
    totalHours: (meetings.reduce((s: number, m: any) => s + m.duration, 0) / 60).toFixed(1),
    actionItems: meetings.reduce((s: number, m: any) => s + (m.summary?.action_items?.length || 0), 0),
    topKeywords: aggregateKeywords(meetings).slice(0, 10),
    avgSentiment: avgSentiment(meetings),
  };
}

function aggregateKeywords(meetings: any[]): [string, number][] {
  const counts: Record<string, number> = {};
  for (const m of meetings) {
    for (const kw of m.summary?.keywords || []) {
      counts[kw] = (counts[kw] || 0) + 1;
    }
  }
  return Object.entries(counts).sort((a, b) => b[1] - a[1]);
}
```

### 6. Audio Upload Pipeline
```typescript
// services/upload.ts
async function uploadRecording(fileUrl: string, title: string, attendees?: any[]) {
  return firefliesQuery(`
    mutation($input: AudioUploadInput) {
      uploadAudio(input: $input) {
        success
        title
        message
      }
    }
  `, {
    input: {
      url: fileUrl,
      title,
      attendees: attendees?.map(a => ({ displayName: a.name, email: a.email })),
      webhook: process.env.WEBHOOK_URL,
      client_reference_id: `upload-${Date.now()}`,
    },
  });
}
```

## Project Layout
```
meeting-intelligence/
  src/
    lib/fireflies.ts          # GraphQL client
    services/
      webhook-processor.ts    # Event handler
      transcript-store.ts     # DB persistence
      action-items.ts         # CRM/task sync
      analytics.ts            # Aggregation
      upload.ts               # Audio upload
    api/
      webhooks/fireflies.ts   # Webhook endpoint
      health.ts               # Health check
    types/fireflies.ts        # TypeScript interfaces
  tests/
    fixtures/                 # Recorded API responses
    services/                 # Service unit tests
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing transcript | `meetingId` invalid | Log and skip, alert on repeated failures |
| Empty summary | Meeting too short | Check duration > 1 min before processing |
| Duplicate webhook | Network retry | Use `meetingId` as idempotency key |
| Rate limit on batch | Many transcripts at once | Queue with PQueue (1 req/sec) |

## Output
- Event-driven architecture with webhook-triggered processing
- Transcript storage with search-ready schema
- Action item extraction and CRM sync pipeline
- Meeting analytics aggregation engine

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [Fireflies Webhooks](https://docs.fireflies.ai/graphql-api/webhooks)
- [Transcript Query](https://docs.fireflies.ai/graphql-api/query/transcript)

## Next Steps
For multi-environment deployment, see `fireflies-multi-env-setup`.
