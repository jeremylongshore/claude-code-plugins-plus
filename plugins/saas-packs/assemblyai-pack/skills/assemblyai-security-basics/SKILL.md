---
name: assemblyai-security-basics
description: |
  Apply AssemblyAI security best practices for API keys, PII, and access control.
  Use when securing API keys, implementing PII redaction,
  or configuring temporary tokens for browser-side streaming.
  Trigger with phrases like "assemblyai security", "assemblyai secrets",
  "secure assemblyai", "assemblyai API key security", "assemblyai PII".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription, security]
compatible-with: claude-code
---

# AssemblyAI Security Basics

## Overview
Security best practices for AssemblyAI: API key management, temporary tokens for browser clients, PII redaction, and data retention policies.

## Prerequisites
- `assemblyai` package installed
- Understanding of environment variables
- AssemblyAI dashboard access

## Instructions

### Step 1: API Key Management

```bash
# .env (NEVER commit)
ASSEMBLYAI_API_KEY=your-api-key-here

# .gitignore
.env
.env.local
.env.*.local
```

```typescript
// Never hardcode API keys
// BAD:
const client = new AssemblyAI({ apiKey: 'sk_abc123...' });

// GOOD:
import { AssemblyAI } from 'assemblyai';
const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});
```

### Step 2: Temporary Tokens for Browser Streaming

Never expose your API key in frontend code. Use temporary tokens for browser-side streaming:

```typescript
// Server-side: /api/assemblyai-token.ts
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

export async function GET() {
  // Token expires after 5 minutes
  const token = await client.streaming.createTemporaryToken({
    expires_in_seconds: 300,
  });

  return Response.json({ token });
}

// Client-side: use the temporary token
// const { token } = await fetch('/api/assemblyai-token').then(r => r.json());
// const transcriber = new StreamingTranscriber({ token });
```

### Step 3: PII Redaction in Transcripts

```typescript
const transcript = await client.transcripts.transcribe({
  audio: audioUrl,
  redact_pii: true,
  redact_pii_policies: [
    'email_address',
    'phone_number',
    'person_name',
    'credit_card_number',
    'social_security_number',
    'date_of_birth',
    'medical_condition',
    'banking_information',
    'us_social_security_number',
  ],
  redact_pii_sub: 'entity_name', // or 'hash'
  // 'entity_name': "My name is [PERSON_NAME]"
  // 'hash':        "My name is ####"
});

// Also redact the audio itself
const transcriptWithRedactedAudio = await client.transcripts.transcribe({
  audio: audioUrl,
  redact_pii: true,
  redact_pii_policies: ['person_name', 'phone_number'],
  redact_pii_audio: true, // Generates audio with PII beeped out
});
```

### Step 4: Data Retention and Deletion

```typescript
// Delete transcript data for GDPR/privacy compliance
await client.transcripts.delete(transcriptId);
// This permanently removes the transcript text and metadata
// The audio file at your source URL is NOT deleted (you manage that)

// List and bulk-delete old transcripts
const page = await client.transcripts.list({ limit: 100 });
for (const t of page.transcripts) {
  const createdDate = new Date(t.created);
  const daysOld = (Date.now() - createdDate.getTime()) / (1000 * 60 * 60 * 24);

  if (daysOld > 30) {
    await client.transcripts.delete(t.id);
    console.log(`Deleted transcript ${t.id} (${daysOld.toFixed(0)} days old)`);
  }
}
```

### Step 5: Content Safety Detection

```typescript
// Detect sensitive content before it reaches your users
const transcript = await client.transcripts.transcribe({
  audio: audioUrl,
  content_safety: true,
});

const safetyResults = transcript.content_safety_labels?.results ?? [];
for (const result of safetyResults) {
  for (const label of result.labels) {
    if (label.confidence > 0.8) {
      console.warn(`Content safety flag: ${label.label} (${(label.confidence * 100).toFixed(0)}%)`);
      // Labels include: hate_speech, violence, profanity, etc.
    }
  }
}

// Get overall severity summary
const summary = transcript.content_safety_labels?.summary ?? {};
for (const [category, severity] of Object.entries(summary)) {
  console.log(`${category}: severity ${severity}`);
}
```

### Step 6: Security Checklist

- [ ] API key stored in environment variable, never in code
- [ ] `.env` files listed in `.gitignore`
- [ ] Separate API keys for dev/staging/prod environments
- [ ] Temporary tokens used for browser streaming (not raw API key)
- [ ] PII redaction enabled for sensitive audio
- [ ] Old transcripts deleted per retention policy
- [ ] Content safety enabled for user-generated audio
- [ ] Webhook endpoints validate payload authenticity
- [ ] CI/CD secrets stored in platform secrets manager (not env files)

## Output
- Secure API key storage pattern
- Temporary token endpoint for browser streaming
- PII redaction with configurable policies
- Data retention automation
- Content safety detection

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| API key in source code | Git scanning / secrets detection | Rotate key immediately at dashboard |
| API key in browser JS | Network tab inspection | Use temporary tokens |
| PII in transcripts | Manual review or automated scan | Enable `redact_pii` |
| Old transcripts retained | Audit transcript list | Automate deletion schedule |

## Resources
- [PII Redaction Guide](https://www.assemblyai.com/docs/audio-intelligence/pii-redaction)
- [Content Safety Detection](https://www.assemblyai.com/docs/audio-intelligence/content-moderation)
- [Streaming Temporary Tokens](https://www.assemblyai.com/docs/getting-started/transcribe-streaming-audio)
- [API Key Dashboard](https://www.assemblyai.com/app/account)

## Next Steps
For production deployment, see `assemblyai-prod-checklist`.
