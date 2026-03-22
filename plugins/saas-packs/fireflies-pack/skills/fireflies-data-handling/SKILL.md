---
name: fireflies-data-handling
description: |
  Handle Fireflies.ai transcript data: export formats, PII redaction, retention policies, and compliance.
  Use when exporting transcripts, implementing data redaction,
  configuring retention, or ensuring GDPR/CCPA compliance.
  Trigger with phrases like "fireflies data", "fireflies PII",
  "fireflies GDPR", "fireflies data retention", "fireflies privacy", "fireflies export".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, compliance]

---
# Fireflies.ai Data Handling

## Overview
Manage meeting transcript data: export in multiple formats (JSON, text, SRT), redact PII from transcripts and summaries, implement retention policies with automated cleanup, and handle GDPR/CCPA data subject requests.

## Prerequisites
- `FIREFLIES_API_KEY` configured
- Understanding of transcript data structure (sentences, summary, analytics)
- Storage for processed transcripts

## Instructions

### Step 1: Fetch Transcript Data
```typescript
const FIREFLIES_API = "https://api.fireflies.ai/graphql";

async function getFullTranscript(id: string) {
  const res = await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({
      query: `
        query($id: String!) {
          transcript(id: $id) {
            id title date duration
            organizer_email
            speakers { id name }
            sentences { speaker_name text start_time end_time }
            summary { overview action_items keywords short_summary }
            meeting_attendees { displayName email }
          }
        }
      `,
      variables: { id },
    }),
  });
  const json = await res.json();
  if (json.errors) throw new Error(json.errors[0].message);
  return json.data.transcript;
}
```

### Step 2: Export in Multiple Formats
```typescript
type ExportFormat = "json" | "text" | "srt" | "csv";

function exportTranscript(transcript: any, format: ExportFormat): string {
  switch (format) {
    case "json":
      return JSON.stringify(transcript, null, 2);

    case "text":
      const lines = [
        `# ${transcript.title}`,
        `Date: ${transcript.date} | Duration: ${transcript.duration}min`,
        `Speakers: ${transcript.speakers.map((s: any) => s.name).join(", ")}`,
        "",
        "## Summary",
        transcript.summary?.overview || "(none)",
        "",
        "## Action Items",
        ...(transcript.summary?.action_items || []).map((a: string) => `- ${a}`),
        "",
        "## Transcript",
        ...transcript.sentences.map((s: any) =>
          `[${fmtTime(s.start_time)}] ${s.speaker_name}: ${s.text}`
        ),
      ];
      return lines.join("\n");

    case "srt":
      return transcript.sentences.map((s: any, i: number) =>
        [
          i + 1,
          `${fmtSrt(s.start_time)} --> ${fmtSrt(s.end_time)}`,
          `${s.speaker_name}: ${s.text}`,
          "",
        ].join("\n")
      ).join("\n");

    case "csv":
      const header = "start_time,end_time,speaker,text";
      const rows = transcript.sentences.map((s: any) =>
        `${s.start_time},${s.end_time},"${s.speaker_name}","${s.text.replace(/"/g, '""')}"`
      );
      return [header, ...rows].join("\n");
  }
}

function fmtTime(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function fmtSrt(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  const ms = Math.floor((sec % 1) * 1000);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(ms).padStart(3, "0")}`;
}
```

### Step 3: PII Redaction
```typescript
const PII_PATTERNS = [
  { regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, tag: "[EMAIL]" },
  { regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, tag: "[PHONE]" },
  { regex: /\b\d{3}-\d{2}-\d{4}\b/g, tag: "[SSN]" },
  { regex: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, tag: "[CARD]" },
  { regex: /\b\d{1,5}\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln)\b/gi, tag: "[ADDRESS]" },
];

function redactText(text: string): string {
  let result = text;
  for (const { regex, tag } of PII_PATTERNS) {
    result = result.replace(regex, tag);
  }
  return result;
}

function redactTranscript(transcript: any): any {
  return {
    ...transcript,
    // Redact organizer email
    organizer_email: redactText(transcript.organizer_email || ""),
    // Redact sentences
    sentences: transcript.sentences?.map((s: any) => ({
      ...s,
      text: redactText(s.text),
      speaker_name: s.speaker_name, // Keep speaker names for context
    })),
    // Redact summary fields too
    summary: transcript.summary ? {
      ...transcript.summary,
      overview: redactText(transcript.summary.overview || ""),
      action_items: transcript.summary.action_items?.map(redactText),
      short_summary: redactText(transcript.summary.short_summary || ""),
    } : null,
    // Redact attendee info
    meeting_attendees: transcript.meeting_attendees?.map((a: any) => ({
      displayName: a.displayName,
      email: redactText(a.email || ""),
    })),
  };
}
```

### Step 4: Retention Policy with Automated Cleanup
```typescript
interface RetentionPolicy {
  fullTranscriptDays: number;   // Keep full sentences
  summaryDays: number;          // Keep summary after transcript deleted
  deleteAfterDays: number;      // Delete everything
}

const DEFAULT_POLICY: RetentionPolicy = {
  fullTranscriptDays: 90,
  summaryDays: 365,
  deleteAfterDays: 730,
};

async function applyRetentionPolicy(policy = DEFAULT_POLICY) {
  const data = await getTranscriptList(200);
  const now = Date.now();
  const results = { kept: 0, archived: 0, deleted: 0 };

  for (const t of data.transcripts) {
    const ageDays = (now - new Date(t.date).getTime()) / 86400000;

    if (ageDays > policy.deleteAfterDays) {
      // Delete from Fireflies
      await deleteTranscript(t.id);
      results.deleted++;
    } else if (ageDays > policy.fullTranscriptDays) {
      // Archive: keep summary only in your DB
      await archiveToSummaryOnly(t.id);
      results.archived++;
    } else {
      results.kept++;
    }
  }

  console.log(`Retention applied: ${results.kept} kept, ${results.archived} archived, ${results.deleted} deleted`);
  return results;
}

async function deleteTranscript(id: string) {
  // Rate limit: 10 deletes per minute
  await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({
      query: `mutation($id: String!) { deleteTranscript(transcript_id: $id) }`,
      variables: { id },
    }),
  });
  // Respect rate limit
  await new Promise(r => setTimeout(r, 6500));
}
```

### Step 5: GDPR Data Subject Request
```typescript
// Handle "right to be forgotten" requests
async function handleDataSubjectDeletion(email: string) {
  // Find all transcripts where this person participated
  const data = await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({
      query: `query($participants: [String]) {
        transcripts(participants: $participants, limit: 100) {
          id title date participants
        }
      }`,
      variables: { participants: [email] },
    }),
  }).then(r => r.json());

  const affected = data.data.transcripts;
  console.log(`Found ${affected.length} transcripts with ${email}`);

  // Option 1: Delete transcripts entirely
  // Option 2: Redact the person's contributions
  // Choose based on your legal requirements

  return {
    email,
    affectedTranscripts: affected.length,
    transcriptIds: affected.map((t: any) => t.id),
  };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing sentences | Transcript still processing | Check before export |
| PII in action items | Redaction only on sentences | Redact summary fields too (Step 3 does this) |
| Delete rate limit | 10 deletes/min | Add 6.5s delay between deletes |
| Large transcript OOM | 2+ hour meeting | Stream or paginate sentences |

## Output
- Multi-format transcript export (JSON, text, SRT, CSV)
- PII redaction covering sentences, summaries, and attendee info
- Automated retention policy with configurable thresholds
- GDPR/CCPA data subject request handler

## Resources
- [Fireflies Privacy Policy](https://fireflies.ai/privacy)
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [Transcript Query](https://docs.fireflies.ai/graphql-api/query/transcript)

## Next Steps
For enterprise access control, see `fireflies-enterprise-rbac`.
