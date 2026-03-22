---
name: deepgram-incident-runbook
description: |
  Execute Deepgram incident response procedures for production issues.
  Use when handling Deepgram outages, debugging production failures,
  or responding to service degradation.
  Trigger: "deepgram incident", "deepgram outage", "deepgram production issue",
  "deepgram down", "deepgram emergency", "deepgram 500 errors".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, debugging, incident-response]

---
# Deepgram Incident Runbook

## Overview
Standardized incident response for Deepgram-related production issues. Includes automated triage script, severity classification (SEV1-SEV4), immediate mitigation actions, fallback activation, and post-incident review template.

## Quick Reference

| Resource | URL |
|----------|-----|
| Deepgram Status | https://status.deepgram.com |
| Deepgram Console | https://console.deepgram.com |
| Support Email | support@deepgram.com |
| Community | https://github.com/orgs/deepgram/discussions |

## Severity Classification

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| SEV1 | Complete outage, all transcriptions failing | Immediate | 100% 5xx errors |
| SEV2 | Major degradation, >50% error rate | < 15 min | Specific model failing |
| SEV3 | Minor degradation, elevated latency | < 1 hour | P95 > 30s |
| SEV4 | Single feature affected, cosmetic | < 24 hours | Diarization inaccurate |

## Instructions

### Step 1: Automated Triage (First 5 Minutes)

```bash
#!/bin/bash
set -euo pipefail
echo "=== Deepgram Incident Triage ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# 1. Check Deepgram status page
echo "--- Status Page ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://status.deepgram.com)
echo "Status page: HTTP $STATUS"

# 2. Test API connectivity
echo ""
echo "--- API Connectivity ---"
curl -s -w "\nHTTP: %{http_code} | Latency: %{time_total}s\n" \
  'https://api.deepgram.com/v1/projects' \
  -H "Authorization: Token $DEEPGRAM_API_KEY" | head -5

# 3. Test transcription
echo ""
echo "--- Transcription Test ---"
RESULT=$(curl -s -w "\n%{http_code}" \
  -X POST 'https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true' \
  -H "Authorization: Token $DEEPGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav"}')
HTTP_CODE=$(echo "$RESULT" | tail -1)
echo "Transcription: HTTP $HTTP_CODE"

# 4. Test multiple models
echo ""
echo "--- Model Tests ---"
for MODEL in nova-3 nova-2 base; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "https://api.deepgram.com/v1/listen?model=$MODEL" \
    -H "Authorization: Token $DEEPGRAM_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"url":"https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav"}')
  echo "$MODEL: HTTP $CODE"
done

# 5. Query internal metrics (if available)
echo ""
echo "--- Internal Metrics ---"
curl -s localhost:3000/health 2>/dev/null || echo "Health endpoint unavailable"
```

### Step 2: SEV1 Response (Complete Outage)

```typescript
import { createClient } from '@deepgram/sdk';

class DeepgramFallbackService {
  private primaryClient: ReturnType<typeof createClient>;
  private isInFallbackMode = false;
  private failedRequests: Array<{ url: string; options: any; timestamp: Date }> = [];

  constructor(apiKey: string) {
    this.primaryClient = createClient(apiKey);
  }

  async transcribe(url: string, options: any) {
    if (this.isInFallbackMode) {
      return this.handleFallback(url, options);
    }

    try {
      const { result, error } = await this.primaryClient.listen.prerecorded.transcribeUrl(
        { url }, options
      );
      if (error) throw error;
      return { source: 'deepgram', result };
    } catch (err) {
      console.error('Deepgram failed, entering fallback mode');
      this.isInFallbackMode = true;
      return this.handleFallback(url, options);
    }
  }

  private handleFallback(url: string, options: any) {
    // Queue for later replay
    this.failedRequests.push({ url, options, timestamp: new Date() });
    console.warn(`Queued for replay: ${url} (${this.failedRequests.length} in queue)`);

    return {
      source: 'fallback',
      message: 'Transcription queued — Deepgram is currently unavailable',
      queuePosition: this.failedRequests.length,
    };
  }

  // Call when Deepgram recovers
  async replayQueue() {
    console.log(`Replaying ${this.failedRequests.length} queued requests...`);
    const queue = [...this.failedRequests];
    this.failedRequests = [];
    this.isInFallbackMode = false;

    for (const req of queue) {
      try {
        await this.transcribe(req.url, req.options);
        console.log(`Replayed: ${req.url}`);
      } catch (err: any) {
        console.error(`Replay failed: ${req.url} — ${err.message}`);
        this.failedRequests.push(req);
      }
    }
  }
}
```

### Step 3: SEV2 Response (Partial Degradation)

```typescript
async function mitigateSev2() {
  const client = createClient(process.env.DEEPGRAM_API_KEY!);
  const testUrl = 'https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav';

  console.log('=== SEV2 Mitigation ===');

  // Test each model to find working ones
  const models = ['nova-3', 'nova-2', 'base', 'whisper-large'] as const;
  const working: string[] = [];
  const broken: string[] = [];

  for (const model of models) {
    try {
      const { error } = await client.listen.prerecorded.transcribeUrl(
        { url: testUrl }, { model }
      );
      if (error) throw error;
      working.push(model);
      console.log(`  [OK] ${model}`);
    } catch {
      broken.push(model);
      console.log(`  [FAIL] ${model}`);
    }
  }

  // Recommended actions
  console.log(`\nWorking models: ${working.join(', ')}`);
  console.log(`Broken models: ${broken.join(', ')}`);

  if (working.length > 0) {
    console.log(`\nAction: Switch to ${working[0]} until ${broken.join(', ')} recovers`);
  } else {
    console.log('\nAction: All models failing — escalate to SEV1');
  }

  // Test features
  const features = [
    { name: 'diarize', opts: { diarize: true } },
    { name: 'smart_format', opts: { smart_format: true } },
    { name: 'utterances', opts: { utterances: true } },
  ];

  console.log('\n--- Feature Tests ---');
  for (const { name, opts } of features) {
    try {
      const { error } = await client.listen.prerecorded.transcribeUrl(
        { url: testUrl }, { model: working[0] ?? 'nova-3', ...opts }
      );
      console.log(`  [${error ? 'FAIL' : 'OK'}] ${name}`);
    } catch {
      console.log(`  [FAIL] ${name}`);
    }
  }
}
```

### Step 4: SEV3/SEV4 Mitigation

```typescript
// SEV3: Elevated latency — increase timeouts and enable aggressive retry
function configureSev3Mitigation() {
  return {
    timeout: 60000,          // Increase from 30s to 60s
    maxRetries: 5,           // Increase from 3 to 5
    model: 'nova-2',         // Fallback to proven model
    diarize: false,          // Disable to reduce processing
    smart_format: true,      // Keep basic formatting
    utterances: false,       // Disable to reduce processing
    summarize: false,        // Disable
    detect_topics: false,    // Disable
  };
}

// SEV4: Single feature broken — disable and continue
function configureSev4Mitigation(brokenFeature: string) {
  const overrides: Record<string, any> = {};
  overrides[brokenFeature] = false;
  console.log(`Disabled ${brokenFeature} — filing Deepgram support ticket`);
  return overrides;
}
```

### Step 5: Post-Incident Review Template

```markdown
## Deepgram Incident Report

**Date:** YYYY-MM-DD
**Duration:** HH:MM start — HH:MM end (X minutes total)
**Severity:** SEV1/2/3/4
**On-Call:** [Name]

### Timeline
| Time (UTC) | Event |
|------------|-------|
| HH:MM | Alert fired: [alert name] |
| HH:MM | On-call acknowledged |
| HH:MM | Triage completed, classified as SEV[N] |
| HH:MM | Mitigation applied: [action taken] |
| HH:MM | Service restored |
| HH:MM | All-clear confirmed |

### Impact
- **Failed requests:** N
- **Affected users:** N
- **Revenue impact:** $X
- **SLA impact:** X minutes of downtime

### Root Cause
[Description of root cause — Deepgram outage / configuration issue / etc.]

### What Went Well
- [Item 1]
- [Item 2]

### What Could Be Improved
- [Item 1]
- [Item 2]

### Action Items
| Action | Owner | Due Date |
|--------|-------|----------|
| [Action 1] | [Name] | YYYY-MM-DD |
| [Action 2] | [Name] | YYYY-MM-DD |
```

### Step 6: Escalation Matrix

| Level | Contact | When |
|-------|---------|------|
| L1 | On-call engineer | Alert fires |
| L2 | Team lead | 15 min without resolution |
| L3 | Deepgram support (support@deepgram.com) | Confirmed Deepgram-side issue |
| L4 | Engineering director | SEV1 > 1 hour |

## Output
- Automated triage script (bash, runs in <30s)
- SEV1 fallback service with request queue and replay
- SEV2 model/feature diagnosis and auto-fallback
- SEV3/SEV4 mitigation configurations
- Post-incident review template

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Triage script can't reach Deepgram | Network or DNS | Check outbound HTTPS to api.deepgram.com |
| Fallback queue growing | Extended outage | Alert if queue > 1000, consider alternate STT |
| Replay failures | Audio URLs expired | Re-fetch audio from source before replay |
| Status page shows green but API fails | Partial outage not yet reflected | Report to Deepgram support immediately |

## Resources
- [Status Page](https://status.deepgram.com)
- [Support Portal](https://developers.deepgram.com/support)
- [Deepgram Community](https://github.com/orgs/deepgram/discussions)
