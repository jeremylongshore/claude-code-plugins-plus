---
name: fireflies-migration-deep-dive
description: |
  Migrate to Fireflies.ai from other meeting transcription platforms or legacy recording systems.
  Use when switching from Otter.ai, Rev, or custom transcription to Fireflies,
  or importing historical meeting data into the Fireflies ecosystem.
  Trigger with phrases like "migrate to fireflies", "switch from otter",
  "fireflies migration", "import meetings to fireflies", "fireflies replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, migration]

---
# Fireflies.ai Migration Deep Dive

## Current State
!`npm list graphql graphql-request 2>/dev/null || echo 'No graphql packages'`

## Overview
Migrate to Fireflies.ai from other transcription platforms or custom recording systems. Covers historical recording import via `uploadAudio`, adapter pattern for gradual cutover, and data validation post-migration.

## Migration Types

| Scenario | Approach | Timeline |
|----------|----------|----------|
| Fresh start (no history) | Configure Fireflies bot, done | 1 day |
| Import recordings | Batch `uploadAudio` | 1-2 weeks |
| Switch from competitor | Parallel run + gradual cutover | 2-4 weeks |
| Enterprise rollout | Phased department-by-department | 1-2 months |

## Instructions

### Step 1: Pre-Migration Assessment
```typescript
// Inventory your current meeting data
interface MigrationInventory {
  totalRecordings: number;
  totalHours: number;
  formats: string[];        // mp3, mp4, wav, m4a, ogg
  averageDuration: number;  // minutes
  dateRange: { oldest: string; newest: string };
  platforms: string[];      // Zoom, Teams, etc.
}

// Fireflies supports: mp3, mp4, wav, m4a, ogg
// Size limits: 200MB audio, 100MB video (free), 1.5GB video (paid)
// Minimum: 50KB (can bypass with bypass_size_check: true)
```

### Step 2: Batch Upload Historical Recordings
```typescript
const FIREFLIES_API = "https://api.fireflies.ai/graphql";

interface UploadJob {
  url: string;        // Must be publicly accessible HTTPS URL
  title: string;
  attendees?: { displayName: string; email: string }[];
  referenceId: string; // Your internal ID for tracking
}

async function batchUpload(jobs: UploadJob[]) {
  const results: { id: string; status: string; error?: string }[] = [];

  for (const job of jobs) {
    try {
      const res = await fetch(FIREFLIES_API, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
        },
        body: JSON.stringify({
          query: `
            mutation($input: AudioUploadInput) {
              uploadAudio(input: $input) {
                success title message
              }
            }
          `,
          variables: {
            input: {
              url: job.url,
              title: job.title,
              attendees: job.attendees,
              client_reference_id: job.referenceId,
              webhook: process.env.WEBHOOK_URL,
            },
          },
        }),
      });

      const json = await res.json();
      if (json.errors) {
        results.push({ id: job.referenceId, status: "error", error: json.errors[0].message });
      } else {
        results.push({ id: job.referenceId, status: "uploaded" });
      }
    } catch (err) {
      results.push({ id: job.referenceId, status: "error", error: (err as Error).message });
    }

    // Rate limit: wait between uploads
    await new Promise(r => setTimeout(r, 2000));
  }

  return results;
}
```

### Step 3: Upload with Authenticated URLs
If your recordings are behind auth (S3, GCS):
```typescript
// Bearer token auth (e.g., pre-signed URLs with auth headers)
const upload = {
  url: "https://storage.example.com/recordings/meeting-123.mp3",
  title: "Q1 Planning",
  download_auth: {
    type: "bearer_token",
    bearer: { token: "your-storage-access-token" },
  },
  client_reference_id: "meeting-123",
};

// Basic auth
const uploadBasicAuth = {
  url: "https://recordings.example.com/files/meeting-456.mp3",
  title: "Sprint Review",
  download_auth: {
    type: "basic_auth",
    basic: { username: "api-user", password: "api-pass" },
  },
  client_reference_id: "meeting-456",
};
```

### Step 4: Direct File Upload (No Public URL)
For files that can't be made publicly accessible:
```typescript
// Step 1: Get a pre-signed upload URL from Fireflies
const { createUploadUrl } = await firefliesQuery(`
  mutation($input: CreateUploadUrlInput!) {
    createUploadUrl(input: $input) {
      url
      meeting_id
    }
  }
`, { input: { /* file metadata */ } });

// Step 2: Upload file directly to the pre-signed URL
await fetch(createUploadUrl.url, {
  method: "PUT",
  body: fileBuffer,
});

// Step 3: Confirm the upload
await firefliesQuery(`
  mutation($input: ConfirmUploadInput!) {
    confirmUpload(input: $input) {
      success
    }
  }
`, { input: { meeting_id: createUploadUrl.meeting_id } });
```

### Step 5: Track Migration Progress via Webhooks
```typescript
// Webhook handler tracks which uploads have completed
const migrationTracker = new Map<string, { status: string; meetingId?: string }>();

async function handleMigrationWebhook(event: any) {
  if (event.eventType === "Transcription completed" && event.clientReferenceId) {
    migrationTracker.set(event.clientReferenceId, {
      status: "completed",
      meetingId: event.meetingId,
    });

    // Check progress
    const completed = [...migrationTracker.values()].filter(v => v.status === "completed").length;
    const total = migrationTracker.size;
    console.log(`Migration progress: ${completed}/${total} (${Math.round(completed/total*100)}%)`);
  }
}
```

### Step 6: Validate Migration
```typescript
async function validateMigration(expectedIds: string[]) {
  const results = {
    found: 0,
    missing: [] as string[],
    hasSummary: 0,
    hasSentences: 0,
  };

  for (const refId of expectedIds) {
    const tracker = migrationTracker.get(refId);
    if (!tracker?.meetingId) {
      results.missing.push(refId);
      continue;
    }

    results.found++;

    // Verify transcript quality
    const { transcript } = await firefliesQuery(`
      query($id: String!) {
        transcript(id: $id) {
          id title
          sentences { text }
          summary { overview action_items }
        }
      }
    `, { id: tracker.meetingId });

    if (transcript.summary?.overview) results.hasSummary++;
    if (transcript.sentences?.length > 0) results.hasSentences++;

    await new Promise(r => setTimeout(r, 1100)); // Rate limit
  }

  console.log(`Validation: ${results.found}/${expectedIds.length} found`);
  console.log(`With summary: ${results.hasSummary}`);
  console.log(`With sentences: ${results.hasSentences}`);
  console.log(`Missing: ${results.missing.length}`);

  return results;
}
```

### Step 7: Adapter Pattern for Gradual Cutover
```typescript
interface TranscriptionService {
  getTranscript(id: string): Promise<any>;
  searchTranscripts(query: string): Promise<any[]>;
}

class FirefliesService implements TranscriptionService {
  async getTranscript(id: string) {
    return firefliesQuery(`
      query($id: String!) {
        transcript(id: $id) {
          id title date duration
          sentences { speaker_name text start_time end_time }
          summary { overview action_items }
        }
      }
    `, { id });
  }

  async searchTranscripts(query: string) {
    const data = await firefliesQuery(`
      query($keyword: String) {
        transcripts(keyword: $keyword, limit: 20) {
          id title date duration
        }
      }
    `, { keyword: query });
    return data.transcripts;
  }
}

// Gradual cutover with feature flag
function getTranscriptionService(): TranscriptionService {
  if (process.env.USE_FIREFLIES === "true") {
    return new FirefliesService();
  }
  return new LegacyTranscriptionService();
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `payload_too_small` | File < 50KB | Set `bypass_size_check: true` |
| Upload rejected | Free plan | Uploads require Pro+ plan |
| Auth download fails | Token expired | Refresh storage credentials |
| Missing transcription | Audio quality poor | Check file format and audio clarity |
| Duplicate uploads | Re-running batch | Use `client_reference_id` for dedup |

## Output
- Pre-migration inventory assessed
- Historical recordings uploaded via `uploadAudio` mutation
- Migration progress tracked via webhooks and `clientReferenceId`
- Post-migration validation confirming transcript quality
- Adapter layer enabling gradual platform cutover

## Resources
- [Upload Audio Mutation](https://docs.fireflies.ai/graphql-api/mutation/upload-audio)
- [Fireflies API Docs](https://docs.fireflies.ai/)

## Next Steps
For monitoring the migrated system, see `fireflies-observability`.
