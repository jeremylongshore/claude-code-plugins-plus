---
name: fireflies-core-workflow-a
description: |
  Retrieve and process Fireflies.ai meeting transcripts with speaker diarization and summaries.
  Use when fetching transcripts, extracting action items,
  or building meeting intelligence pipelines.
  Trigger with phrases like "fireflies transcript", "get meeting notes",
  "fireflies meeting data", "fetch fireflies recording".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, workflow, transcripts]

---
# Fireflies.ai Core Workflow A -- Transcript Retrieval & Processing

## Overview
Primary workflow for Fireflies.ai: fetch meeting transcripts via GraphQL, process speaker-diarized sentences, extract action items and summaries, and route meeting intelligence downstream.

## Prerequisites
- Completed `fireflies-install-auth` setup
- `FIREFLIES_API_KEY` set with Business+ plan for full access
- At least one completed meeting in Fireflies

## Instructions

### Step 1: Build the GraphQL Client
```typescript
// lib/fireflies.ts
const FIREFLIES_API = "https://api.fireflies.ai/graphql";

export async function firefliesQuery<T = any>(
  query: string,
  variables?: Record<string, any>
): Promise<T> {
  const res = await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({ query, variables }),
  });

  const json = await res.json();
  if (json.errors) {
    const err = json.errors[0];
    throw new Error(`Fireflies API error: ${err.message} (${err.code || "unknown"})`);
  }
  return json.data;
}
```

### Step 2: List Transcripts with Filters
```typescript
const LIST_TRANSCRIPTS = `
  query ListTranscripts(
    $limit: Int,
    $mine: Boolean,
    $fromDate: DateTime,
    $toDate: DateTime,
    $organizers: [String],
    $participants: [String]
  ) {
    transcripts(
      limit: $limit
      mine: $mine
      fromDate: $fromDate
      toDate: $toDate
      organizers: $organizers
      participants: $participants
    ) {
      id title date duration
      organizer_email participants
      summary { overview action_items keywords }
    }
  }
`;

// Fetch this week's meetings for a specific organizer
const data = await firefliesQuery(LIST_TRANSCRIPTS, {
  limit: 20,
  fromDate: "2026-03-15T00:00:00Z",
  organizers: ["alice@company.com"],
});
```

### Step 3: Fetch Full Transcript with Sentences
```typescript
const GET_TRANSCRIPT = `
  query GetTranscript($id: String!) {
    transcript(id: $id) {
      id title date duration
      organizer_email
      speakers { id name }
      sentences {
        index
        speaker_name
        speaker_id
        text
        raw_text
        start_time
        end_time
        ai_filters {
          task
          question
          sentiment
          pricing
          metric
          date_and_time
        }
      }
      summary {
        overview
        short_summary
        bullet_gist
        action_items
        keywords
        outline
        topics_discussed
      }
      meeting_attendees { displayName email }
      meeting_attendance { name join_time leave_time }
      analytics {
        sentiments { positive_pct negative_pct neutral_pct }
        speakers {
          name duration word_count
          words_per_minute questions
          longest_monologue filler_words
        }
      }
    }
  }
`;

const { transcript } = await firefliesQuery(GET_TRANSCRIPT, { id: "abc123" });
```

### Step 4: Process Meeting Intelligence
```typescript
interface MeetingIntelligence {
  id: string;
  title: string;
  attendees: string[];
  actionItems: string[];
  keyTopics: string[];
  speakerBreakdown: { name: string; minutes: number; wordCount: number }[];
  sentiment: { positive: number; negative: number; neutral: number };
  questions: string[];
}

function processMeeting(transcript: any): MeetingIntelligence {
  // Extract questions from AI filters
  const questions = transcript.sentences
    .filter((s: any) => s.ai_filters?.question)
    .map((s: any) => `${s.speaker_name}: ${s.text}`);

  return {
    id: transcript.id,
    title: transcript.title,
    attendees: transcript.meeting_attendees?.map((a: any) => a.email) || [],
    actionItems: transcript.summary?.action_items || [],
    keyTopics: transcript.summary?.keywords || [],
    speakerBreakdown: (transcript.analytics?.speakers || []).map((s: any) => ({
      name: s.name,
      minutes: Math.round(s.duration / 60),
      wordCount: s.word_count,
    })),
    sentiment: {
      positive: transcript.analytics?.sentiments?.positive_pct || 0,
      negative: transcript.analytics?.sentiments?.negative_pct || 0,
      neutral: transcript.analytics?.sentiments?.neutral_pct || 0,
    },
    questions,
  };
}
```

### Step 5: Export Transcript as Text
```typescript
function transcriptToText(transcript: any): string {
  const lines: string[] = [
    `# ${transcript.title}`,
    `Date: ${transcript.date} | Duration: ${transcript.duration}min`,
    `Speakers: ${transcript.speakers.map((s: any) => s.name).join(", ")}`,
    "",
    "## Summary",
    transcript.summary?.overview || "(no summary)",
    "",
    "## Action Items",
    ...(transcript.summary?.action_items || []).map((a: string) => `- ${a}`),
    "",
    "## Transcript",
  ];

  for (const s of transcript.sentences) {
    const timestamp = formatTimestamp(s.start_time);
    lines.push(`[${timestamp}] ${s.speaker_name}: ${s.text}`);
  }
  return lines.join("\n");
}

function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `auth_failed` | Invalid API key | Regenerate in Fireflies dashboard |
| Empty `sentences` array | Transcript still processing | Check `meeting_info.summary_status` |
| `null` summary | Short meeting (<1 min) | Summary requires minimum content |
| Rate limit 429 | Over 60 req/min (Business) | Implement backoff per `fireflies-rate-limits` |
| Missing `analytics` | Free/Pro plan | Analytics requires Business+ plan |

## Output
- Full transcript with speaker-diarized sentences and timestamps
- AI-generated summary, action items, and keywords
- Speaker analytics with talk time, word count, and sentiment
- Meeting intelligence object ready for downstream processing

## Resources
- [Transcript Query](https://docs.fireflies.ai/graphql-api/query/transcript)
- [Fireflies API Concepts](https://docs.fireflies.ai/fundamentals/concepts)

## Next Steps
For search, analytics, and AskFred, see `fireflies-core-workflow-b`.
