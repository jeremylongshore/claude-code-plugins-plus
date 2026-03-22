---
name: assemblyai-prod-checklist
description: |
  Execute AssemblyAI production deployment checklist and rollback procedures.
  Use when deploying AssemblyAI integrations to production, preparing for launch,
  or implementing go-live procedures for transcription services.
  Trigger with phrases like "assemblyai production", "deploy assemblyai",
  "assemblyai go-live", "assemblyai launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription, production]
compatible-with: claude-code
---

# AssemblyAI Production Checklist

## Overview
Complete checklist for deploying AssemblyAI-powered transcription services to production with health checks, monitoring, and rollback procedures.

## Prerequisites
- Staging environment tested and verified
- Production API key from https://www.assemblyai.com/app/account
- Deployment pipeline configured
- Monitoring stack ready

## Instructions

### Pre-Deployment Checklist

#### API Key & Auth
- [ ] Production API key stored in secrets manager (not env files)
- [ ] Key is separate from dev/staging keys
- [ ] Temporary token endpoint configured for browser streaming
- [ ] API key rotation procedure documented

#### Code Quality
- [ ] All `transcript.status === 'error'` cases handled
- [ ] Rate limit retry with exponential backoff implemented
- [ ] No hardcoded API keys or audio URLs
- [ ] PII redaction enabled for sensitive audio content
- [ ] Webhook URL uses HTTPS
- [ ] Audio file upload size validated before submission

#### Error Handling
- [ ] 429 (rate limit) triggers retry with backoff
- [ ] 5xx (server error) triggers retry with backoff
- [ ] 401 (auth error) triggers alert, no retry
- [ ] `transcript.status === 'error'` logged with transcript ID and error message
- [ ] WebSocket disconnect triggers reconnection for streaming
- [ ] LeMUR errors handled (invalid transcript ID, context too long)

#### Performance
- [ ] Transcript results cached where appropriate
- [ ] Concurrent transcription jobs limited via queue (p-queue or similar)
- [ ] Webhook processing is async (don't block the response)
- [ ] Long audio files processed with `webhook_url` instead of polling

### Health Check Implementation

```typescript
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

export async function healthCheck(): Promise<{
  status: 'healthy' | 'degraded' | 'down';
  assemblyai: { connected: boolean; latencyMs: number };
}> {
  const start = Date.now();
  try {
    // List transcripts as a lightweight connectivity check
    await client.transcripts.list({ limit: 1 });
    return {
      status: 'healthy',
      assemblyai: { connected: true, latencyMs: Date.now() - start },
    };
  } catch (error) {
    return {
      status: 'degraded',
      assemblyai: { connected: false, latencyMs: Date.now() - start },
    };
  }
}
```

### Webhook-Based Processing (Recommended for Production)

```typescript
// Instead of polling, use webhooks for transcription completion
const transcript = await client.transcripts.submit({
  audio: audioUrl,
  webhook_url: 'https://your-app.com/webhooks/assemblyai',
  webhook_auth_header_name: 'X-Webhook-Secret',
  webhook_auth_header_value: process.env.ASSEMBLYAI_WEBHOOK_SECRET!,
  speaker_labels: true,
  sentiment_analysis: true,
});

console.log('Submitted:', transcript.id, '(webhook will fire on completion)');
```

```typescript
// Webhook handler
import express from 'express';

app.post('/webhooks/assemblyai', express.json(), async (req, res) => {
  // Verify auth header
  const secret = req.headers['x-webhook-secret'];
  if (secret !== process.env.ASSEMBLYAI_WEBHOOK_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const { transcript_id, status } = req.body;

  if (status === 'completed') {
    // Fetch full transcript
    const transcript = await client.transcripts.get(transcript_id);
    await processCompletedTranscript(transcript);
  } else if (status === 'error') {
    console.error(`Transcript ${transcript_id} failed:`, req.body.error);
    await handleFailedTranscript(transcript_id, req.body.error);
  }

  res.status(200).json({ received: true });
});
```

### Monitoring & Alerting

| Alert | Condition | Severity |
|-------|-----------|----------|
| API unreachable | Health check fails 3x consecutive | P1 |
| High error rate | >5% of transcriptions fail | P2 |
| Rate limited | 429 errors > 5/min | P2 |
| Auth failure | Any 401 response | P1 |
| Slow transcription | Queue wait > 5 min | P3 |
| Webhook delivery failure | Webhook retries exhausted | P2 |

### Gradual Rollout

```bash
# 1. Pre-flight: verify AssemblyAI API is healthy
curl -s https://status.assemblyai.com/api/v2/status.json | jq '.status.description'

# 2. Deploy to canary (10% traffic)
# 3. Monitor error rate and latency for 10 minutes
# 4. If healthy, roll to 50%, then 100%
# 5. Keep previous version ready for instant rollback
```

## Output
- Production-ready deployment with health checks
- Webhook-based transcription processing
- Monitoring and alerting configuration
- Gradual rollout strategy

## Error Handling
| Issue | Detection | Response |
|-------|-----------|----------|
| API key invalid in prod | 401 on first call | Rotate key immediately |
| Transcription backlog | Queue size growing | Scale workers, check rate limits |
| Webhook endpoint down | Missed completion events | Poll for stuck transcripts |
| Audio upload timeout | Large file failures | Increase timeout, validate file size |

## Resources
- [AssemblyAI Webhooks Guide](https://www.assemblyai.com/docs/getting-started/webhooks)
- [AssemblyAI Status Page](https://status.assemblyai.com)
- [AssemblyAI Account Management](https://www.assemblyai.com/docs/deployment/account-management)

## Next Steps
For version upgrades, see `assemblyai-upgrade-migration`.
