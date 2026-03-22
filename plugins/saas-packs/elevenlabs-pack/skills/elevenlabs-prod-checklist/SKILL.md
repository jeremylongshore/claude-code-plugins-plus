---
name: elevenlabs-prod-checklist
description: |
  Execute ElevenLabs production deployment checklist with health checks and rollback.
  Use when deploying TTS/voice integrations to production, preparing for launch,
  or implementing go-live procedures for ElevenLabs-powered apps.
  Trigger: "elevenlabs production", "deploy elevenlabs",
  "elevenlabs go-live", "elevenlabs launch checklist", "production TTS".
allowed-tools: Read, Bash(curl:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, production, deployment]
compatible-with: claude-code
---

# ElevenLabs Production Checklist

## Overview

Complete checklist for deploying ElevenLabs TTS/voice integrations to production. Covers API configuration, health checks, circuit breakers, monitoring, and rollback procedures.

## Prerequisites

- Staging environment tested and verified
- Production API key (separate from dev/staging)
- Monitoring and alerting infrastructure ready

## Instructions

### Step 1: Pre-Deployment Verification

**Configuration:**
- [ ] Production API key stored in secure vault (not in code)
- [ ] `ELEVENLABS_API_KEY` set in deployment platform's secrets
- [ ] Webhook secret configured (if using webhooks)
- [ ] Using production model ID (`eleven_multilingual_v2` or `eleven_v3`)

**Code Quality:**
- [ ] All tests passing with mocked ElevenLabs SDK
- [ ] No hardcoded API keys (scan with `grep -r "sk_" src/`)
- [ ] Error handling covers 400, 401, 404, 429, 5xx responses
- [ ] Rate limiting implemented matching plan concurrency limit
- [ ] Text splitting handles inputs > 5,000 characters
- [ ] Audio output format appropriate for use case

**Quota Planning:**
- [ ] Estimated monthly character usage fits within plan limit
- [ ] Usage-based billing enabled (Creator+ plans) if needed
- [ ] Flash/Turbo models used where latency matters more than quality

### Step 2: Health Check Endpoint

```typescript
// src/api/health.ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  elevenlabs: {
    connected: boolean;
    latencyMs: number;
    quotaRemaining: number | null;
    quotaPctUsed: number | null;
  };
  timestamp: string;
}

export async function healthCheck(): Promise<HealthStatus> {
  const client = new ElevenLabsClient();
  const start = Date.now();

  try {
    const user = await client.user.get();
    const latency = Date.now() - start;
    const { character_count, character_limit } = user.subscription;
    const remaining = character_limit - character_count;
    const pctUsed = Math.round((character_count / character_limit) * 100);

    return {
      status: pctUsed > 90 ? "degraded" : "healthy",
      elevenlabs: {
        connected: true,
        latencyMs: latency,
        quotaRemaining: remaining,
        quotaPctUsed: pctUsed,
      },
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    return {
      status: "unhealthy",
      elevenlabs: {
        connected: false,
        latencyMs: Date.now() - start,
        quotaRemaining: null,
        quotaPctUsed: null,
      },
      timestamp: new Date().toISOString(),
    };
  }
}
```

### Step 3: Circuit Breaker

```typescript
// src/elevenlabs/circuit-breaker.ts
type CircuitState = "closed" | "open" | "half-open";

export class ElevenLabsCircuitBreaker {
  private state: CircuitState = "closed";
  private failures = 0;
  private lastFailure = 0;

  constructor(
    private failureThreshold = 5,       // Open after N consecutive failures
    private resetTimeMs = 30_000,       // Try again after 30s
  ) {}

  async execute<T>(operation: () => Promise<T>, fallback?: () => T): Promise<T> {
    if (this.state === "open") {
      if (Date.now() - this.lastFailure > this.resetTimeMs) {
        this.state = "half-open";
      } else {
        if (fallback) return fallback();
        throw new Error("ElevenLabs circuit breaker is open — service unavailable");
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      if (fallback) return fallback();
      throw error;
    }
  }

  private onSuccess() {
    this.failures = 0;
    this.state = "closed";
  }

  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.failureThreshold) {
      this.state = "open";
      console.error(`[ElevenLabs] Circuit breaker OPEN after ${this.failures} failures`);
    }
  }

  getState(): CircuitState {
    return this.state;
  }
}

// Usage: graceful degradation when ElevenLabs is down
const breaker = new ElevenLabsCircuitBreaker();

async function generateSpeechWithFallback(text: string, voiceId: string) {
  return breaker.execute(
    () => client.textToSpeech.convert(voiceId, {
      text,
      model_id: "eleven_multilingual_v2",
    }),
    () => {
      // Fallback: return pre-generated placeholder audio or null
      console.warn("[ElevenLabs] Using fallback — TTS unavailable");
      return null;
    }
  );
}
```

### Step 4: Monitoring & Alerting

```typescript
// src/elevenlabs/monitor.ts
interface TTSMetric {
  operation: string;
  voiceId: string;
  modelId: string;
  textLength: number;
  latencyMs: number;
  success: boolean;
  errorCode?: string;
}

function emitMetric(metric: TTSMetric) {
  // Send to your monitoring system (Datadog, CloudWatch, Prometheus, etc.)
  console.log(JSON.stringify({
    ...metric,
    timestamp: new Date().toISOString(),
    service: "elevenlabs",
  }));
}

// Alert thresholds
const ALERT_RULES = {
  p99_latency_ms: 5000,       // Alert if p99 > 5 seconds
  error_rate_pct: 5,           // Alert if error rate > 5%
  quota_used_pct: 80,          // Alert when 80% quota used
  circuit_breaker_open: true,  // Alert on circuit breaker trip
};
```

### Step 5: Pre-Flight Check Script

```bash
#!/bin/bash
# pre-flight-check.sh — Run before deploying

echo "=== ElevenLabs Pre-Flight Check ==="

# 1. API connectivity
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}")
echo "API connectivity: HTTP $HTTP"
[ "$HTTP" != "200" ] && echo "FAIL: API not reachable" && exit 1

# 2. Quota check
QUOTA=$(curl -s https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
  jq '.subscription | (.character_limit - .character_count)')
echo "Characters remaining: $QUOTA"
[ "$QUOTA" -lt 10000 ] && echo "WARN: Low quota"

# 3. Voice availability
VOICE_COUNT=$(curl -s https://api.elevenlabs.io/v1/voices \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | jq '.voices | length')
echo "Voices available: $VOICE_COUNT"

# 4. TTS smoke test
TTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text":"Pre-flight check.","model_id":"eleven_flash_v2_5"}')
echo "TTS smoke test: HTTP $TTS_STATUS"
[ "$TTS_STATUS" != "200" ] && echo "FAIL: TTS not working" && exit 1

echo "=== All checks passed ==="
```

## Deployment Monitoring

| Alert | Condition | Severity |
|-------|-----------|----------|
| API unreachable | Health check fails 3x | P1 — Critical |
| Quota exhausted | 401 `quota_exceeded` | P1 — Critical |
| High error rate | 5xx > 5% of requests | P2 — High |
| Rate limited | 429 > 10/min sustained | P2 — High |
| High latency | p99 > 5000ms | P3 — Medium |
| Quota warning | > 80% used | P3 — Medium |

## Error Handling

| Scenario | Response |
|----------|----------|
| ElevenLabs API down | Circuit breaker opens; fallback to cached/placeholder audio |
| Quota exhausted mid-day | Alert team; switch to Flash model (0.5x cost); queue non-urgent requests |
| Voice deleted | Return 404 to caller; alert; fall back to default voice |
| Webhook delivery failing | Monitor ElevenLabs webhook health; webhooks auto-disable after 10 failures |

## Resources

- [ElevenLabs Status](https://status.elevenlabs.io)
- [ElevenLabs API Reference](https://elevenlabs.io/docs/api-reference/introduction)
- [Usage Dashboard](https://elevenlabs.io/app/usage)

## Next Steps

For version upgrades, see `elevenlabs-upgrade-migration`. For cost optimization, see `elevenlabs-cost-tuning`.
