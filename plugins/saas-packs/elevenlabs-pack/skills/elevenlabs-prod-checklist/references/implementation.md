# ElevenLabs Production — Reference Implementation

Full, drop-in TypeScript for the three production resilience primitives referenced
from `SKILL.md`: a health-check endpoint, a circuit breaker with graceful fallback,
and a monitoring/alerting harness. Copy the blocks you need and adapt the import
paths and monitoring sink to your stack.

## Health Check Endpoint

Reports connectivity, round-trip latency, and remaining character quota so your
load balancer / uptime monitor can gate traffic and your dashboards can chart
quota burn. Returns `degraded` once quota crosses 90%, `unhealthy` on any API
failure.

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

## Circuit Breaker

Opens after N consecutive failures, short-circuits calls for a cooldown window,
then probes with a half-open state. Pass a `fallback` to degrade gracefully
(placeholder audio, cached clip, or `null`) instead of throwing when ElevenLabs
is down.

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

## Monitoring & Alerting

Emit one structured metric per TTS call and wire the alert thresholds into your
observability platform (Datadog, CloudWatch, Prometheus, etc.).

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
