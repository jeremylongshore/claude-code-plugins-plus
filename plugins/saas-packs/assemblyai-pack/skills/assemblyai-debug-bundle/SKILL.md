---
name: assemblyai-debug-bundle
description: |
  Collect AssemblyAI debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for AssemblyAI problems.
  Trigger with phrases like "assemblyai debug", "assemblyai support bundle",
  "collect assemblyai logs", "assemblyai diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription]
compatible-with: claude-code
---

# AssemblyAI Debug Bundle

## Overview
Collect all diagnostic information needed to resolve AssemblyAI issues — SDK version, transcript status, API connectivity, and configuration — packaged for support tickets.

## Prerequisites
- `assemblyai` package installed
- Access to application logs
- Failed transcript ID (if applicable)

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# assemblyai-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="assemblyai-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== AssemblyAI Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Environment
echo "--- Runtime ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Node.js not found" >> "$BUNDLE_DIR/summary.txt"
echo "Platform: $(uname -s) $(uname -m)" >> "$BUNDLE_DIR/summary.txt"
echo "ASSEMBLYAI_API_KEY: ${ASSEMBLYAI_API_KEY:+[SET (${#ASSEMBLYAI_API_KEY} chars)]}" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# SDK version
echo "--- SDK Version ---" >> "$BUNDLE_DIR/summary.txt"
npm list assemblyai 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "assemblyai not in node_modules" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# API connectivity
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: ${ASSEMBLYAI_API_KEY:-none}" \
  https://api.assemblyai.com/v2/transcript 2>/dev/null || echo "FAILED")
echo "GET /v2/transcript: HTTP $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.assemblyai.com/v2 2>/dev/null || echo "FAILED")
echo "GET /v2: HTTP $STATUS_CODE" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# AssemblyAI service status
echo "--- Service Status ---" >> "$BUNDLE_DIR/summary.txt"
curl -s https://status.assemblyai.com/api/v2/status.json 2>/dev/null \
  | python3 -m json.tool 2>/dev/null >> "$BUNDLE_DIR/summary.txt" \
  || echo "Could not fetch status" >> "$BUNDLE_DIR/summary.txt"

# Package bundle
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Review for sensitive data before sharing with support."
```

### Step 2: Programmatic Transcript Diagnostics

```typescript
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

async function diagnoseTranscript(transcriptId: string) {
  const transcript = await client.transcripts.get(transcriptId);

  const report = {
    id: transcript.id,
    status: transcript.status,
    error: transcript.error ?? null,
    audio_url: transcript.audio_url,
    audio_duration: transcript.audio_duration,
    language_code: transcript.language_code,
    speech_model: transcript.speech_model,
    created: transcript.created,
    completed: transcript.completed,

    // Feature flags that were enabled
    features: {
      speaker_labels: !!transcript.utterances?.length,
      sentiment_analysis: !!transcript.sentiment_analysis_results?.length,
      entity_detection: !!transcript.entities?.length,
      auto_highlights: !!transcript.auto_highlights_result?.results?.length,
      content_safety: !!transcript.content_safety_labels?.results?.length,
      redact_pii: transcript.text?.includes('####') || transcript.text?.includes('['),
      summarization: !!transcript.summary,
    },

    // Word count / duration sanity check
    word_count: transcript.words?.length ?? 0,
    words_per_minute: transcript.audio_duration
      ? ((transcript.words?.length ?? 0) / (transcript.audio_duration / 60)).toFixed(1)
      : 'N/A',
  };

  console.log(JSON.stringify(report, null, 2));
  return report;
}

// Usage: diagnoseTranscript('your-transcript-id');
```

### Step 3: Check Recent Failed Transcripts

```typescript
async function findFailedTranscripts(limit = 50) {
  const page = await client.transcripts.list({ limit });
  const failed = page.transcripts.filter(t => t.status === 'error');

  console.log(`Found ${failed.length} failed transcripts out of ${page.transcripts.length}:`);
  for (const t of failed) {
    console.log(`  ${t.id} | ${t.created} | ${t.error}`);
  }

  return failed;
}
```

## What to Include in a Support Ticket

**Always include:**
- Transcript ID (e.g., `6wij2z3g66-...`)
- Error message (exact text)
- SDK version (`npm list assemblyai`)
- Node.js version
- Timestamp of the failure (UTC)

**Never include:**
- Your API key
- Raw audio containing PII
- Customer data

**Helpful extras:**
- Audio file format and duration
- Which features were enabled (speaker_labels, etc.)
- Whether the issue is intermittent or consistent

## Output
- `assemblyai-debug-YYYYMMDD-HHMMSS.tar.gz` archive with:
  - `summary.txt` — Runtime, SDK version, API connectivity, service status
- Programmatic transcript diagnosis report
- List of recently failed transcripts

## Error Handling
| Item | Purpose | Check |
|------|---------|-------|
| SDK version | Version-specific bugs | `npm list assemblyai` |
| API connectivity | Network/firewall | `curl api.assemblyai.com` |
| Service status | Outage check | status.assemblyai.com |
| Transcript status | Job-specific error | `client.transcripts.get(id)` |
| Audio URL | Accessibility | `curl -I <audio_url>` |

## Resources
- [AssemblyAI Support](https://support.assemblyai.com)
- [AssemblyAI Status Page](https://status.assemblyai.com)
- [AssemblyAI Community Discord](https://www.assemblyai.com/discord)

## Next Steps
For rate limit issues, see `assemblyai-rate-limits`.
