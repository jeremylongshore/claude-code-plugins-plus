---
name: fathom-upgrade-migration
description: |
  Handle Fathom API changes and version migrations.
  Trigger with phrases like "upgrade fathom", "fathom api changes", "fathom migration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Upgrade & Migration

## Overview

Fathom is an AI meeting assistant that records, transcribes, and summarizes meetings. The API operates under `/external/v1` and exposes endpoints for meetings, transcripts, and action items. Tracking API changes is important because Fathom iterates rapidly on transcript schema fields (speaker attribution, sentiment data, highlight clips) and breaking changes to response shapes can silently corrupt downstream integrations that consume meeting data for CRM sync or analytics pipelines.

## Version Detection

```typescript
const FATHOM_BASE = "https://api.fathom.video/external/v1";

interface FathomVersionCheck {
  apiVersion: string;
  knownFields: string[];
  detectedFields: string[];
  newFields: string[];
  removedFields: string[];
}

async function detectFathomApiChanges(apiKey: string): Promise<FathomVersionCheck> {
  const res = await fetch(`${FATHOM_BASE}/meetings?limit=1`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  const data = await res.json();
  const knownFields = ["id", "title", "created_at", "duration", "attendees", "transcript_url"];
  const detectedFields = data.meetings?.[0] ? Object.keys(data.meetings[0]) : [];
  return {
    apiVersion: res.headers.get("x-api-version") ?? "v1",
    knownFields,
    detectedFields,
    newFields: detectedFields.filter((f) => !knownFields.includes(f)),
    removedFields: knownFields.filter((f) => !detectedFields.includes(f)),
  };
}
```

## Migration Checklist

- [ ] Review Fathom product updates for API changes and deprecations
- [ ] Audit all endpoints referencing `/external/v1` in codebase
- [ ] Verify meeting list response schema matches current field expectations
- [ ] Check transcript endpoint for new speaker attribution fields
- [ ] Validate action item extraction format (structured vs. plain text)
- [ ] Update OAuth token refresh flow if auth endpoints changed
- [ ] Test webhook payloads for meeting completion events
- [ ] Verify pagination parameters (`cursor` vs. `offset`) are current
- [ ] Update CRM sync mappings if meeting metadata fields renamed
- [ ] Run integration tests against Fathom sandbox environment

## Schema Migration

```typescript
// Fathom transcript response evolved: flat text → speaker-attributed segments
interface OldTranscript {
  meeting_id: string;
  text: string;
  created_at: string;
}

interface NewTranscript {
  meeting_id: string;
  segments: Array<{
    speaker: string;
    text: string;
    start_time: number;
    end_time: number;
    confidence: number;
  }>;
  summary: string;
  action_items: Array<{ text: string; assignee?: string }>;
  created_at: string;
}

function migrateTranscript(old: OldTranscript): NewTranscript {
  return {
    meeting_id: old.meeting_id,
    segments: [{ speaker: "Unknown", text: old.text, start_time: 0, end_time: 0, confidence: 1.0 }],
    summary: "",
    action_items: [],
    created_at: old.created_at,
  };
}
```

## Rollback Strategy

```typescript
class FathomClient {
  private baseUrl: string;
  private fallbackUrl: string;

  constructor(private apiKey: string) {
    this.baseUrl = "https://api.fathom.video/external/v1";
    this.fallbackUrl = "https://api.fathom.video/external/v1"; // same base, version in path
  }

  async getMeetings(limit = 20): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/meetings?limit=${limit}`, {
        headers: { Authorization: `Bearer ${this.apiKey}` },
      });
      if (!res.ok) throw new Error(`Fathom API ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("Primary endpoint failed, attempting fallback:", err);
      const res = await fetch(`${this.fallbackUrl}/meetings?limit=${limit}`, {
        headers: { Authorization: `Bearer ${this.apiKey}`, Accept: "application/json; version=legacy" },
      });
      return await res.json();
    }
  }
}
```

## Error Handling

| Migration Issue | Symptom | Fix |
|----------------|---------|-----|
| Transcript schema changed | Missing `segments` array, only flat `text` returned | Update parser to handle both old flat and new segmented formats |
| Webhook payload mismatch | `meeting.completed` event missing expected fields | Re-register webhook with updated event schema version |
| OAuth scope expansion | `403 Forbidden` on transcript endpoint | Re-authorize with updated scopes (`meetings.read`, `transcripts.read`) |
| Pagination cursor invalid | `400 Bad Request` with cursor token | Switch from offset-based to cursor-based pagination if API changed |
| Rate limit headers changed | `429` without `Retry-After` header | Implement exponential backoff instead of relying on header |

## Resources

- [Fathom Product Updates](https://help.fathom.video/en/articles/6220097)
- [Fathom API Documentation](https://fathom.video/api)

## Next Steps

For CI pipeline integration, see `fathom-ci-integration`.
