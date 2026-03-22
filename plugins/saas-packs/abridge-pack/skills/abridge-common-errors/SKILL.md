---
name: abridge-common-errors
description: |
  Diagnose and fix common Abridge clinical AI integration errors.
  Use when encountering EHR connectivity failures, note generation errors,
  audio streaming issues, or FHIR validation problems with Abridge.
  Trigger: "abridge error", "abridge not working", "abridge debug",
  "fix abridge issue", "abridge troubleshoot".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, troubleshooting]
compatible-with: claude-code
---

# Abridge Common Errors

## Overview

Comprehensive troubleshooting guide for Abridge clinical documentation integration. Covers authentication failures, EHR connectivity, audio streaming, note generation, and FHIR push errors.

## Error Reference

### Authentication & Authorization Errors

| Code | Error | Root Cause | Fix |
|------|-------|-----------|-----|
| `401` | `INVALID_CREDENTIALS` | Expired or wrong partner secret | Rotate credentials in Abridge Partner Portal |
| `401` | `TOKEN_EXPIRED` | SMART on FHIR token expired | Refresh token before 60-min expiry |
| `403` | `ORG_NOT_PROVISIONED` | org_id not activated | Contact Abridge sales engineer |
| `403` | `SPECIALTY_NOT_LICENSED` | Specialty not in contract | Check licensed specialties in Partner Portal |
| `403` | `PROVIDER_NOT_ENROLLED` | Provider not onboarded | Complete provider enrollment in Abridge admin |

### Session & Encounter Errors

| Code | Error | Root Cause | Fix |
|------|-------|-----------|-----|
| `409` | `SESSION_ALREADY_ACTIVE` | Duplicate session for same encounter | Reuse existing session_id |
| `422` | `INVALID_SPECIALTY` | Unsupported specialty code | Use codes from `/specialties` endpoint |
| `422` | `PATIENT_NOT_FOUND` | Patient ID not in EHR context | Verify FHIR Patient resource exists |
| `408` | `SESSION_TIMEOUT` | Session idle > 30 minutes | Create new session; old ones auto-expire |
| `500` | `SESSION_CORRUPTED` | Server-side state error | Create new session; report to Abridge support |

### Audio & Transcription Errors

```typescript
// Common audio streaming diagnostics
async function diagnoseAudioIssues(wsUrl: string): Promise<string[]> {
  const issues: string[] = [];

  // Check WebSocket connectivity
  try {
    const ws = new WebSocket(wsUrl);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
      setTimeout(() => reject(new Error('Connection timeout')), 5000);
    });
    ws.close();
  } catch {
    issues.push('WebSocket connection failed — check firewall allows wss:// on port 443');
  }

  // Check audio format requirements
  // Abridge requires: 16kHz, mono, 16-bit PCM little-endian
  const requiredFormat = { sampleRate: 16000, channels: 1, encoding: 'pcm_s16le' };
  issues.push(`Verify audio format: ${JSON.stringify(requiredFormat)}`);

  return issues;
}
```

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Empty transcript | Microphone not capturing | Check audio input device; verify 16kHz sample rate |
| Garbled transcript | Wrong encoding | Must be 16-bit PCM LE mono at 16kHz |
| Speaker mislabeled | Single-channel audio | Use stereo mic or speaker diarization hints |
| WebSocket drops | Network instability | Implement reconnect with buffered chunks |
| High latency | Large audio chunks | Send 100ms chunks, not full sentences |

### Note Generation Errors

```typescript
// Note generation failure handler
async function handleNoteFailure(sessionId: string, error: any): Promise<void> {
  const status = error.response?.status;
  const code = error.response?.data?.error_code;

  switch (code) {
    case 'INSUFFICIENT_CONTENT':
      console.error('Transcript too short — need at least 30 seconds of clinical conversation');
      break;
    case 'UNSUPPORTED_LANGUAGE':
      console.error('Language not in Abridge supported set (28+ languages)');
      break;
    case 'TEMPLATE_NOT_FOUND':
      console.error('Note template not available — use: soap, hp, progress, procedure');
      break;
    case 'GENERATION_TIMEOUT':
      console.error('Note generation exceeded 120s — complex encounter, retry once');
      break;
    default:
      console.error(`Unknown note error: ${status} ${code}`);
  }
}
```

### FHIR Integration Errors

| Error | Root Cause | Fix |
|-------|-----------|-----|
| FHIR `422 Unprocessable` | Invalid DocumentReference | Validate against FHIR R4 schema |
| FHIR `401 Unauthorized` | Epic token expired | Re-authenticate via SMART on FHIR |
| FHIR `404 Not Found` | Wrong FHIR base URL | Verify Epic FHIR endpoint in EHR config |
| FHIR `409 Conflict` | Duplicate document ID | Generate unique DocumentReference IDs |
| Epic SmartPhrase error | Template mismatch | Verify SmartPhrase names match Epic config |

### HIPAA Compliance Errors

```typescript
// PHI leak detection in error logs
function auditErrorLog(error: any): void {
  const serialized = JSON.stringify(error);

  // Check for accidental PHI in error output
  const phiPatterns = [
    /\b\d{3}-\d{2}-\d{4}\b/,        // SSN
    /\b\d{10}\b/,                     // MRN (10-digit)
    /\b[A-Z][a-z]+\s[A-Z][a-z]+\b/,  // Patient names (heuristic)
    /\b\d{1,2}\/\d{1,2}\/\d{4}\b/,   // DOB
  ];

  for (const pattern of phiPatterns) {
    if (pattern.test(serialized)) {
      console.error('WARNING: Possible PHI detected in error log — redact before logging');
      return;
    }
  }
}
```

## Diagnostic Script

```bash
#!/bin/bash
# abridge-diagnostic.sh — Run before opening a support ticket

echo "=== Abridge Integration Diagnostics ==="

# 1. Check credentials
echo "Checking credentials..."
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $ABRIDGE_CLIENT_SECRET" \
  -H "X-Org-Id: $ABRIDGE_ORG_ID" \
  "${ABRIDGE_BASE_URL}/health"

# 2. Check FHIR server
echo "Checking FHIR connectivity..."
curl -s -o /dev/null -w "%{http_code}" \
  "${EPIC_FHIR_BASE_URL}/metadata"

# 3. Check WebSocket
echo "Checking WebSocket..."
curl -s -o /dev/null -w "%{http_code}" \
  --header "Upgrade: websocket" \
  "${ABRIDGE_BASE_URL/http/ws}/ws/health"

echo "=== Diagnostics Complete ==="
```

## Output

- Identified root cause from error code lookup
- Applied targeted fix for the specific error
- HIPAA-safe error logging verified

## Resources

- [Abridge Platform](https://www.abridge.com/product)
- [FHIR R4 Operation Outcomes](https://hl7.org/fhir/R4/operationoutcome.html)
- [HIPAA Breach Notification Rule](https://www.hhs.gov/hipaa/for-professionals/breach-notification/)

## Next Steps

For collecting debug evidence for support tickets, see `abridge-debug-bundle`.
