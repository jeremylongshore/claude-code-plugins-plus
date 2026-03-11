---
name: fireflies-data-handling
description: |
  Implement Fireflies.ai PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Fireflies.ai integrations.
  Trigger with phrases like "fireflies data", "fireflies PII",
  "fireflies GDPR", "fireflies data retention", "fireflies privacy", "fireflies CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Fireflies.ai Data Handling

## Overview
Manage meeting transcript data from Fireflies.ai. Covers transcript export formats, PII redaction in transcripts, meeting data retention policies, and selective data sync to CRM and project management tools.

## Prerequisites
- Fireflies.ai API key
- GraphQL client configured
- Understanding of transcript data structure
- Storage for processed transcripts

## Instructions

### Step 1: Transcript Export and Format Conversion
```typescript
import { GraphQLClient } from 'graphql-request';

const fireflies = new GraphQLClient('https://api.fireflies.ai/graphql', {
  headers: { Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}` },
});

const FULL_TRANSCRIPT = `
  query GetTranscript($id: String!) {
    transcript(id: $id) {
      id title date duration
      sentences { speaker_name text start_time end_time }
      summary { overview action_items keywords }
    }
  }
`;

async function exportTranscript(id: string, format: 'json' | 'text' | 'srt') {
  const { transcript } = await fireflies.request(FULL_TRANSCRIPT, { id });

  switch (format) {
    case 'json':
      return JSON.stringify(transcript, null, 2);
    case 'text':
      return transcript.sentences
        .map((s: any) => `${s.speaker_name}: ${s.text}`)
        .join('\n');
    case 'srt':
      return transcript.sentences
        .map((s: any, i: number) => [
          i + 1,
          `${formatTime(s.start_time)} --> ${formatTime(s.end_time)}`,
          `${s.speaker_name}: ${s.text}`,
          '',
        ].join('\n'))
        .join('\n');
  }
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')},${String(ms).padStart(3,'0')}`;
}
```

### Step 2: PII Redaction in Transcripts
```typescript
const PII_PATTERNS = [
  { regex: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, tag: '[EMAIL]' },
  { regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, tag: '[PHONE]' },
  { regex: /\b\d{3}-\d{2}-\d{4}\b/g, tag: '[SSN]' },
  { regex: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, tag: '[CARD]' },
];

function redactTranscript(sentences: any[]) {
  return sentences.map(s => ({
    ...s,
    text: redactText(s.text),
  }));
}

function redactText(text: string): string {
  let redacted = text;
  for (const { regex, tag } of PII_PATTERNS) {
    redacted = redacted.replace(regex, tag);
  }
  return redacted;
}
```

### Step 3: Meeting Data Retention Policy
```typescript
interface RetentionPolicy {
  transcriptRetentionDays: number;
  summaryRetentionDays: number;
  actionItemRetentionDays: number;
}

const DEFAULT_POLICY: RetentionPolicy = {
  transcriptRetentionDays: 90,
  summaryRetentionDays: 365,
  actionItemRetentionDays: 180,
};

async function applyRetention(
  transcripts: any[],
  policy = DEFAULT_POLICY
) {
  const now = Date.now();
  const results = { kept: 0, archived: 0, deleted: 0 };

  for (const t of transcripts) {
    const ageDays = (now - new Date(t.date).getTime()) / 86400000;

    if (ageDays > policy.transcriptRetentionDays) {
      // Archive: keep summary, delete full transcript
      await archiveTranscript(t.id, {
        keepSummary: ageDays <= policy.summaryRetentionDays,
        keepActions: ageDays <= policy.actionItemRetentionDays,
      });
      results.archived++;
    } else {
      results.kept++;
    }
  }

  return results;
}
```

### Step 4: Selective CRM Sync
```typescript
async function syncActionItemsToCRM(transcriptId: string) {
  const { transcript } = await fireflies.request(FULL_TRANSCRIPT, { id: transcriptId });

  const actionItems = transcript.summary?.action_items || [];
  if (actionItems.length === 0) return { synced: 0 };

  const tasks = actionItems.map((item: string) => ({
    title: item.slice(0, 200),
    source: 'fireflies',
    meetingTitle: transcript.title,
    meetingDate: transcript.date,
    participants: transcript.sentences
      .map((s: any) => s.speaker_name)
      .filter((v: string, i: number, a: string[]) => a.indexOf(v) === i),
  }));

  return { synced: tasks.length, tasks };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing sentences | Transcription still processing | Check transcript status before export |
| PII in action items | Redaction only applied to sentences | Also redact summary fields |
| Large transcript | Long meeting (2+ hours) | Process in chunks, stream export |
| Retention policy gap | No automated cleanup | Schedule weekly retention job |

## Examples

### Batch Export for Compliance
```typescript
async function exportAllForAudit(ids: string[]) {
  return Promise.all(ids.map(async id => ({
    id,
    text: await exportTranscript(id, 'text'),
    exportedAt: new Date().toISOString(),
  })));
}
```

## Resources
- [Fireflies GraphQL API](https://docs.fireflies.ai/graphql)
- [Fireflies Data Retention](https://fireflies.ai/privacy)
