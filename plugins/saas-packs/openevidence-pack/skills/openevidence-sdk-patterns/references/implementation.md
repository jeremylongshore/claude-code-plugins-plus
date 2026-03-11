# OpenEvidence SDK Patterns - Implementation Details

## Client Singleton with DI
```typescript
export class OpenEvidenceClientFactory {
  private static instance: OpenEvidenceClient;
  static configure(config: OpenEvidenceConfig): void { this.config = config; this.instance = null!; }
  static getClient(): OpenEvidenceClient {
    if (!this.instance) this.instance = new OpenEvidenceClient(this.config);
    return this.instance;
  }
}
```

## Typed Clinical Queries
```typescript
export type ClinicalSpecialty = 'internal-medicine' | 'emergency-medicine' | 'cardiology' | 'oncology' | 'neurology' | 'pediatrics' | 'psychiatry' | 'surgery' | 'family-medicine' | 'pharmacology';
export type QueryUrgency = 'stat' | 'urgent' | 'routine' | 'research';
```

## Query Builder Pattern
```typescript
const query = new ClinicalQueryBuilder()
  .question('What is the recommended statin dosing for secondary prevention?')
  .specialty('cardiology')
  .urgency('routine')
  .withPatient(65, 'male')
  .withConditions(['prior MI', 'hyperlipidemia'])
  .includeGuidelines()
  .maxCitations(5)
  .build();
```

## Response Transformer
```typescript
export function transformResponse(raw: RawOpenEvidenceResponse): FormattedClinicalAnswer {
  return {
    summary: raw.answer.split('.')[0] + '.',
    detailedAnswer: raw.answer,
    keyPoints: extractKeyPoints(raw.answer),
    evidence: raw.citations.map(c => ({ source: c.source, strength: determineEvidenceStrength(c), year: c.year })),
    confidence: { score: raw.confidence, level: raw.confidence > 0.9 ? 'high' : raw.confidence > 0.7 ? 'moderate' : 'low' },
    disclaimer: 'Clinical answers are for informational purposes. Always verify with current guidelines.',
  };
}
```

## Caching Strategy
```typescript
export class ClinicalQueryCache {
  private defaultTTL = 3600000; // 1 hour for clinical data
  get<T>(query: any): T | null { /* SHA-256 key, TTL check */ }
  set<T>(query: any, data: T, ttl?: number): void { /* Store with timestamp */ }
}
```

## Complete Service Example
```typescript
export async function getClinicalEvidence(question: string, specialty: string): Promise<FormattedClinicalAnswer> {
  const query = new ClinicalQueryBuilder().question(question).specialty(specialty).urgency('routine').build();
  const cached = cache.get<FormattedClinicalAnswer>(query);
  if (cached) return cached;
  const response = await OpenEvidenceClientFactory.getClient().query(query);
  const formatted = transformResponse(response);
  cache.set(query, formatted);
  return formatted;
}
```
