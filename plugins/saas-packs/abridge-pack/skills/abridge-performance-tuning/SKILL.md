---
name: abridge-performance-tuning
description: |
  Optimize Abridge clinical AI integration performance for high-volume deployments.
  Use when reducing note generation latency, optimizing audio streaming throughput,
  improving FHIR push performance, or scaling for multi-site health systems.
  Trigger: "abridge performance", "abridge latency", "abridge optimization",
  "abridge slow", "abridge scale".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, performance]
compatible-with: claude-code
---

# Abridge Performance Tuning

## Overview

Performance optimization for high-volume Abridge deployments. Large health systems process thousands of encounters daily — latency in note generation directly impacts clinical workflow throughput.

## Performance Targets

| Metric | Target | Critical Threshold |
|--------|--------|--------------------|
| Audio stream → first transcript | < 2s | > 5s |
| Encounter → completed note | < 30s | > 60s |
| Note → EHR push | < 3s | > 10s |
| Patient summary generation | < 10s | > 30s |
| Concurrent sessions per org | 100+ | < 50 |

## Instructions

### Step 1: Audio Streaming Optimization

```typescript
// src/performance/audio-optimizer.ts
// Optimize audio chunk size and streaming for lowest latency

interface AudioStreamMetrics {
  chunkSize: number;
  sendInterval: number;
  bufferUtilization: number;
  latencyP50: number;
  latencyP99: number;
}

class OptimizedAudioStream {
  private buffer: Buffer[] = [];
  private metrics: AudioStreamMetrics = {
    chunkSize: 3200,       // 100ms at 16kHz 16-bit mono = 3200 bytes
    sendInterval: 100,     // Send every 100ms
    bufferUtilization: 0,
    latencyP50: 0,
    latencyP99: 0,
  };

  constructor(
    private ws: WebSocket,
    private sampleRate: number = 16000,
  ) {}

  // Optimal chunk size: 100ms for low latency, 500ms for bandwidth efficiency
  processAudioChunk(chunk: Buffer): void {
    this.buffer.push(chunk);

    const totalSize = this.buffer.reduce((sum, b) => sum + b.length, 0);
    if (totalSize >= this.metrics.chunkSize) {
      const combined = Buffer.concat(this.buffer);
      this.buffer = [];

      if (this.ws.readyState === WebSocket.OPEN) {
        const start = performance.now();
        this.ws.send(combined);
        this.recordLatency(performance.now() - start);
      }
    }
  }

  private recordLatency(ms: number): void {
    // Track P50/P99 for monitoring
    this.metrics.latencyP50 = ms; // Simplified — use histogram in production
  }

  getMetrics(): AudioStreamMetrics {
    return { ...this.metrics };
  }
}
```

### Step 2: Note Generation Pipeline Optimization

```typescript
// src/performance/note-pipeline.ts
// Pre-warm note generation and parallelize post-processing

interface PipelineStage {
  name: string;
  durationMs: number;
  parallel: boolean;
}

async function optimizedNotePipeline(
  api: any,
  sessionId: string,
): Promise<{ note: any; metrics: PipelineStage[] }> {
  const stages: PipelineStage[] = [];

  // Stage 1: Finalize session (triggers AI processing)
  const t1 = performance.now();
  await api.post(`/encounters/sessions/${sessionId}/finalize`);
  stages.push({ name: 'finalize', durationMs: performance.now() - t1, parallel: false });

  // Stage 2: Poll with exponential backoff (adaptive polling)
  const t2 = performance.now();
  let pollInterval = 500;  // Start fast
  let note = null;

  for (let i = 0; i < 30; i++) {
    const { data } = await api.get(`/encounters/sessions/${sessionId}/note`);
    if (data.status === 'completed') {
      note = data.note;
      break;
    }
    await new Promise(r => setTimeout(r, pollInterval));
    pollInterval = Math.min(pollInterval * 1.5, 3000); // Back off gradually
  }
  stages.push({ name: 'note_generation', durationMs: performance.now() - t2, parallel: false });

  if (!note) throw new Error('Note generation timed out');

  // Stage 3: Parallel post-processing
  const t3 = performance.now();
  const [patientSummary, ehrResult] = await Promise.allSettled([
    api.post(`/encounters/sessions/${sessionId}/patient-summary`, { language: 'en' }),
    pushNoteToEhr(note),
  ]);
  stages.push({ name: 'post_processing', durationMs: performance.now() - t3, parallel: true });

  return { note, metrics: stages };
}
```

### Step 3: Connection Pooling for FHIR Push

```typescript
// src/performance/connection-pool.ts
import axios from 'axios';
import https from 'https';

// Reuse TCP connections for FHIR endpoint
const fhirAgent = new https.Agent({
  keepAlive: true,
  keepAliveMsecs: 30000,
  maxSockets: 20,          // Max concurrent FHIR connections
  maxFreeSockets: 5,
  minVersion: 'TLSv1.3',
});

const fhirClient = axios.create({
  baseURL: process.env.EPIC_FHIR_BASE_URL,
  httpsAgent: fhirAgent,
  timeout: 10000,
});

// Batch FHIR pushes for multi-encounter processing
async function batchFhirPush(notes: Array<{ docRef: any }>): Promise<void> {
  // FHIR Bundle for batch operations
  const bundle = {
    resourceType: 'Bundle',
    type: 'batch',
    entry: notes.map(n => ({
      resource: n.docRef,
      request: { method: 'POST', url: 'DocumentReference' },
    })),
  };

  await fhirClient.post('/', bundle, {
    headers: { 'Content-Type': 'application/fhir+json' },
  });
}
```

### Step 4: Performance Monitoring Dashboard

```typescript
// src/performance/monitor.ts
interface PerformanceSnapshot {
  timestamp: string;
  activeSessions: number;
  avgNoteLatencyMs: number;
  p99NoteLatencyMs: number;
  fhirPushSuccessRate: number;
  audioStreamDropRate: number;
}

class PerformanceMonitor {
  private noteLatencies: number[] = [];
  private fhirPushResults: boolean[] = [];

  recordNoteLatency(ms: number): void {
    this.noteLatencies.push(ms);
    if (this.noteLatencies.length > 1000) this.noteLatencies.shift();
  }

  recordFhirPush(success: boolean): void {
    this.fhirPushResults.push(success);
    if (this.fhirPushResults.length > 1000) this.fhirPushResults.shift();
  }

  getSnapshot(activeSessions: number): PerformanceSnapshot {
    const sorted = [...this.noteLatencies].sort((a, b) => a - b);
    return {
      timestamp: new Date().toISOString(),
      activeSessions,
      avgNoteLatencyMs: sorted.length ? sorted.reduce((a, b) => a + b, 0) / sorted.length : 0,
      p99NoteLatencyMs: sorted.length ? sorted[Math.floor(sorted.length * 0.99)] : 0,
      fhirPushSuccessRate: this.fhirPushResults.length
        ? this.fhirPushResults.filter(Boolean).length / this.fhirPushResults.length
        : 1,
      audioStreamDropRate: 0, // Populated by audio stream metrics
    };
  }
}
```

## Output

- Optimized audio streaming with 100ms chunking
- Adaptive polling for note generation (500ms → 3s backoff)
- Connection-pooled FHIR batch pushes
- Real-time performance monitoring with P50/P99 latency tracking

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High note latency | Complex encounter | Pre-segment long encounters |
| FHIR push timeout | EHR server overloaded | Use connection pool; batch pushes |
| Audio drops | Network jitter | Buffer 500ms; reconnect on drop |

## Resources

- [Abridge Platform](https://www.abridge.com/product)
- [Node.js HTTPS Agent](https://nodejs.org/api/https.html#class-httpsagent)

## Next Steps

For cost optimization, see `abridge-cost-tuning`.
