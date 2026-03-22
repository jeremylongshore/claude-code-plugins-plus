---
name: deepgram-security-basics
description: |
  Apply Deepgram security best practices for API key management and data protection.
  Use when securing Deepgram integrations, implementing key rotation,
  or auditing security configurations.
  Trigger: "deepgram security", "deepgram API key security", "secure deepgram",
  "deepgram key rotation", "deepgram data protection", "deepgram PII redaction".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, api, security, compliance]

---
# Deepgram Security Basics

## Overview
Security best practices for Deepgram integration: scoped API keys, key rotation, Deepgram's built-in PII redaction feature, client-side temporary keys, SSRF prevention for audio URLs, and audit logging.

## Security Checklist
- [ ] API keys in environment variables or secret manager (never in code)
- [ ] Separate keys per environment (dev/staging/prod)
- [ ] Keys scoped to minimum required permissions
- [ ] Key rotation schedule (90 days recommended)
- [ ] Deepgram `redact` option enabled for PII-sensitive audio
- [ ] Audio URLs validated (HTTPS only, no private IPs)
- [ ] Audit logging on all transcription operations

## Instructions

### Step 1: Scoped API Keys

Create keys with minimal permissions in Console > Settings > API Keys:

```typescript
// Production transcription service — only needs listen scope
const sttKey = process.env.DEEPGRAM_STT_KEY;  // Scope: listen

// TTS service — only needs speak scope
const ttsKey = process.env.DEEPGRAM_TTS_KEY;  // Scope: speak

// Monitoring dashboard — only needs usage read
const monitorKey = process.env.DEEPGRAM_MONITOR_KEY;  // Scope: usage:read

// Admin operations — separate key, restricted access
const adminKey = process.env.DEEPGRAM_ADMIN_KEY;  // Scope: manage, keys
```

### Step 2: Deepgram Built-in PII Redaction

```typescript
import { createClient } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

// Deepgram redacts PII directly in the transcript
const { result } = await deepgram.listen.prerecorded.transcribeUrl(
  { url: audioUrl },
  {
    model: 'nova-3',
    smart_format: true,
    // Built-in redaction — replaces sensitive data in transcript
    redact: ['pci', 'ssn', 'numbers'],
    // pci     — Credit card numbers → [REDACTED]
    // ssn     — Social Security numbers → [REDACTED]
    // numbers — All numeric sequences → [REDACTED]
  }
);

// Transcript will contain [REDACTED] in place of sensitive numbers
console.log(result.results.channels[0].alternatives[0].transcript);
// "My card number is [REDACTED] and my SSN is [REDACTED]"
```

### Step 3: Temporary Keys for Client-Side

```typescript
// Generate short-lived keys for browser/mobile clients
// This prevents exposing your main API key

import { createClient } from '@deepgram/sdk';
import express from 'express';

const app = express();
const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

app.post('/api/deepgram/token', async (req, res) => {
  // Create a temporary key that expires in 10 seconds
  // Use for browser WebSocket connections
  const { result, error } = await deepgram.manage.createProjectKey(
    process.env.DEEPGRAM_PROJECT_ID!,
    {
      comment: `temp-key-${Date.now()}`,
      scopes: ['listen'],          // Minimal scope
      time_to_live_in_seconds: 10, // Short-lived
    }
  );

  if (error) return res.status(500).json({ error: error.message });
  res.json({ key: result.key, expires_in: 10 });
});

// Browser client uses temporary key:
// const { key } = await fetch('/api/deepgram/token').then(r => r.json());
// const ws = new WebSocket('wss://api.deepgram.com/v1/listen', ['token', key]);
```

### Step 4: Key Rotation

```typescript
import { createClient } from '@deepgram/sdk';

async function rotateApiKey(projectId: string) {
  const admin = createClient(process.env.DEEPGRAM_ADMIN_KEY!);

  // 1. Create new key with same scopes
  const { result: newKey } = await admin.manage.createProjectKey(projectId, {
    comment: `rotated-${new Date().toISOString().split('T')[0]}`,
    scopes: ['listen', 'speak'],
    expiration_date: new Date(Date.now() + 90 * 86400000).toISOString(), // 90 days
  });
  console.log('New key created:', newKey.key_id);

  // 2. Update secret manager (example: GCP Secret Manager)
  // await updateSecret('DEEPGRAM_API_KEY', newKey.key);

  // 3. Validate new key works
  const testClient = createClient(newKey.key);
  const { error } = await testClient.manage.getProjects();
  if (error) throw new Error('New key validation failed — aborting rotation');

  // 4. Delete old key (after services have picked up new key)
  // await admin.manage.deleteProjectKey(projectId, oldKeyId);

  return newKey;
}
```

### Step 5: Audio URL Validation (SSRF Prevention)

```typescript
import { URL } from 'url';
import { lookup } from 'dns/promises';

async function validateAudioUrl(url: string): Promise<void> {
  const parsed = new URL(url);

  // Require HTTPS
  if (parsed.protocol !== 'https:') {
    throw new Error('Only HTTPS audio URLs allowed');
  }

  // Block private/internal IPs
  const { address } = await lookup(parsed.hostname);
  const privateRanges = [
    /^127\./, /^10\./, /^172\.(1[6-9]|2\d|3[01])\./, /^192\.168\./,
    /^0\./, /^169\.254\./, /^::1$/, /^fc00:/, /^fe80:/,
  ];
  if (privateRanges.some(r => r.test(address))) {
    throw new Error(`Blocked: ${parsed.hostname} resolves to private IP`);
  }

  // Block known internal hostnames
  const blockedHosts = ['localhost', 'metadata.google.internal', '169.254.169.254'];
  if (blockedHosts.includes(parsed.hostname)) {
    throw new Error(`Blocked hostname: ${parsed.hostname}`);
  }
}

// Use before transcription:
await validateAudioUrl(userProvidedUrl);
const { result } = await deepgram.listen.prerecorded.transcribeUrl(
  { url: userProvidedUrl }, { model: 'nova-3' }
);
```

### Step 6: Audit Logging

```typescript
interface AuditEntry {
  timestamp: string;
  action: 'transcribe' | 'tts' | 'key_create' | 'key_delete';
  userId: string;
  requestId?: string;
  model: string;
  audioDuration?: number;
  success: boolean;
  error?: string;
  ip?: string;
}

function logAudit(entry: AuditEntry) {
  // Structured JSON for log aggregation (Datadog, CloudWatch, etc.)
  const log = {
    ...entry,
    service: 'deepgram-integration',
    level: entry.success ? 'info' : 'error',
  };
  console.log(JSON.stringify(log));
}

// Usage in transcription middleware
async function transcribeWithAudit(userId: string, url: string, ip: string) {
  const start = Date.now();
  try {
    const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
      { url }, { model: 'nova-3', smart_format: true }
    );
    logAudit({
      timestamp: new Date().toISOString(),
      action: 'transcribe',
      userId, model: 'nova-3', ip,
      requestId: result?.metadata?.request_id,
      audioDuration: result?.metadata?.duration,
      success: !error,
      error: error?.message,
    });
    if (error) throw error;
    return result;
  } catch (err: any) {
    logAudit({
      timestamp: new Date().toISOString(),
      action: 'transcribe',
      userId, model: 'nova-3', ip,
      success: false, error: err.message,
    });
    throw err;
  }
}
```

## Output
- Scoped API keys per service/environment
- Built-in PII redaction via `redact` parameter
- Temporary keys for client-side (browser/mobile)
- Key rotation with validation and cleanup
- SSRF-safe audio URL validation
- Structured audit logging

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 403 after scoping | Key missing required scope | Add scope in Console (e.g., `listen`) |
| Temp key expired | TTL too short | Increase `time_to_live_in_seconds` |
| Rotation broke service | New key not propagated | Use overlap period — both keys active |
| Redaction missed PII | Wrong redact option | Use `redact: ['pci', 'ssn', 'numbers']` |

## Resources
- [API Key Management](https://developers.deepgram.com/docs/api-key-management)
- [PII Redaction](https://developers.deepgram.com/docs/redaction)
- [Deepgram Security](https://deepgram.com/security)
- [SOC 2 / HIPAA](https://deepgram.com/hipaa)
