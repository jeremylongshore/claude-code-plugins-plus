# OpenEvidence Performance Tuning - Implementation Details

## Query Optimization
```typescript
function optimizeQuestion(question: string): string {
  return question.replace(/\b(please|can you|could you)\b/gi, '').replace(/\s+/g, ' ').trim() + '?';
}

function optimizeContext(context: ClinicalContext): ClinicalContext {
  return {
    specialty: context.specialty,
    urgency: context.urgency,
    ...(context.relevantConditions && { relevantConditions: context.relevantConditions.slice(0, 5) }),
    ...(context.currentMedications && { currentMedications: context.currentMedications.slice(0, 10) }),
  };
}
```

## Intelligent Caching Layer
```typescript
export class ClinicalQueryCache {
  private getTTL(question: string, context: ClinicalContext): number {
    if (context.urgency === 'stat') return 300; // 5 min for urgent
    if (/mechanism|pharmacokinetics|half-life/.test(question.toLowerCase())) return 86400; // 24h for stable facts
    if (/guideline|first-line|recommended/.test(question.toLowerCase())) return 3600; // 1h for guidelines
    return this.defaultTTL;
  }

  async get(question: string, context: ClinicalContext): Promise<any | null> { /* SHA-256 key lookup */ }
  async set(question: string, context: ClinicalContext, data: any): Promise<void> { /* Store with TTL */ }
}
```

## Connection Pooling & Keep-Alive
```typescript
const httpsAgent = new Agent({ keepAlive: true, keepAliveMsecs: 30000, maxSockets: 10, maxFreeSockets: 5 });
export const optimizedClient = new OpenEvidenceClient({ httpAgent: httpsAgent, timeout: 30000 });
```

## Request Batching
```typescript
const queryBatcher = new DataLoader(async (queries) => {
  return Promise.all(queries.map(q => optimizedClient.query(q)));
}, { maxBatchSize: 5, batchScheduleFn: (cb) => setTimeout(cb, 50) });
```

## Response Streaming
```typescript
export async function streamingClinicalQuery(question: string, context: ClinicalContext, onPartial: (partial: string) => void) {
  if (optimizedClient.supportsStreaming?.()) {
    const stream = await optimizedClient.query.stream({ question, context });
    let fullAnswer = '';
    for await (const chunk of stream) { fullAnswer += chunk.text; onPartial(fullAnswer); }
    return stream.finalResponse;
  }
  const response = await optimizedClient.query({ question, context });
  onPartial(response.answer);
  return response;
}
```

## Performance Monitoring
Prometheus metrics: queryLatency histogram, cacheHits/Misses counters, queueSize gauge.
