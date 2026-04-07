---
name: openevidence-sdk-patterns
description: |
  Sdk Patterns for OpenEvidence.
  Trigger: "openevidence sdk patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence SDK Patterns

## Overview
Production-ready patterns for the OpenEvidence clinical evidence API. OpenEvidence provides REST endpoints for querying medical literature, retrieving clinical guidelines, and generating evidence-based recommendations. The API authenticates via `OPENEVIDENCE_API_KEY` and returns structured clinical data with citation provenance. A singleton client enforces consistent auth, handles healthcare-specific errors, and preserves citation chains for audit compliance.

## Singleton Client
```typescript
const OE_BASE = 'https://api.openevidence.com/v1';
let _client: OpenEvidenceClient | null = null;
export function getClient(): OpenEvidenceClient {
  if (!_client) {
    const apiKey = process.env.OPENEVIDENCE_API_KEY;
    if (!apiKey) throw new Error('OPENEVIDENCE_API_KEY must be set — get it from openevidence.com/developer');
    _client = new OpenEvidenceClient(apiKey);
  }
  return _client;
}
class OpenEvidenceClient {
  private headers: Record<string, string>;
  constructor(apiKey: string) { this.headers = { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' }; }
  async query(question: string, opts: { specialty?: string; maxResults?: number } = {}): Promise<EvidenceResponse> {
    const res = await fetch(`${OE_BASE}/query`, { method: 'POST', headers: this.headers,
      body: JSON.stringify({ question, specialty: opts.specialty, max_results: opts.maxResults ?? 10 }) });
    if (!res.ok) throw new OEError(res.status, await res.text()); return res.json();
  }
  async getCitation(citationId: string): Promise<Citation> {
    const res = await fetch(`${OE_BASE}/citations/${citationId}`, { headers: this.headers });
    if (!res.ok) throw new OEError(res.status, await res.text()); return res.json();
  }
}
```

## Error Wrapper
```typescript
export class OEError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = 'OEError'; }
}
export async function safeCall<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (err: any) {
    if (err instanceof OEError && err.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    if (err instanceof OEError && err.status === 401) throw new OEError(401, 'Invalid OPENEVIDENCE_API_KEY');
    if (err instanceof OEError && err.status === 422) throw new OEError(422, `${operation}: query rejected — check terminology`);
    throw new OEError(err.status ?? 0, `${operation} failed: ${err.message}`);
  }
}
```

## Request Builder
```typescript
class OEQueryBuilder {
  private body: Record<string, any> = {};
  question(q: string) { this.body.question = q; return this; }
  specialty(s: string) { this.body.specialty = s; return this; }
  maxResults(n: number) { this.body.max_results = Math.min(n, 50); return this; }
  evidenceLevel(level: 'meta-analysis' | 'rct' | 'cohort' | 'any') { this.body.evidence_level = level; return this; }
  yearRange(from: number, to: number) { this.body.year_range = { from, to }; return this; }
  build() { return this.body; }
}
// Usage: new OEQueryBuilder().question('statin efficacy in elderly').specialty('cardiology').evidenceLevel('rct').build();
```

## Response Types
```typescript
interface EvidenceResponse {
  answer: string; confidence: number; citations: Citation[]; specialty: string;
}
interface Citation {
  id: string; title: string; authors: string[]; journal: string; year: number;
  doi: string; evidence_level: 'meta-analysis' | 'rct' | 'cohort' | 'case-report'; abstract: string;
}
interface Guideline {
  id: string; organization: string; title: string; year: number;
  recommendation: string; strength: 'strong' | 'moderate' | 'weak';
}
interface DrugInteraction {
  drug_a: string; drug_b: string; severity: 'major' | 'moderate' | 'minor';
  description: string; citations: Citation[];
}
```

## Testing Utilities
```typescript
export function mockCitation(overrides: Partial<Citation> = {}): Citation {
  return { id: 'cite-001', title: 'Statin Therapy in Older Adults', authors: ['Smith J', 'Doe A'],
    journal: 'NEJM', year: 2024, doi: '10.1056/NEJMoa2401234',
    evidence_level: 'rct', abstract: 'Background: ...', ...overrides };
}
export function mockEvidenceResponse(citationCount = 3): EvidenceResponse {
  return { answer: 'Evidence supports moderate-intensity statin therapy...', confidence: 0.87,
    citations: Array.from({ length: citationCount }, (_, i) => mockCitation({ id: `cite-${i}` })),
    specialty: 'cardiology' };
}
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| `safeCall` wrapper | All API calls | Structured error with clinical operation context |
| Retry on 429 | Batch evidence queries | 5s backoff before retry |
| 422 validation | Malformed clinical queries | Clear message on rejected terminology |
| Citation chain audit | Compliance reporting | Preserve full provenance from response |

## Resources
- [OpenEvidence](https://www.openevidence.com)

## Next Steps
Apply patterns in `openevidence-core-workflow-a`.
