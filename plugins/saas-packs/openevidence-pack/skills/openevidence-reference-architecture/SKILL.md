---
name: openevidence-reference-architecture
description: 'Reference Architecture for OpenEvidence.

  Trigger: "openevidence reference architecture".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openevidence
- healthcare
compatibility: Designed for Claude Code
---
# OpenEvidence Reference Architecture

## Overview

Production architecture for clinical decision support integrations with OpenEvidence. Designed for healthcare platforms needing evidence-based query processing, citation-backed clinical answers, and full audit logging for regulatory compliance. Key design drivers: HIPAA-compliant data handling, deterministic citation pipelines for clinical accuracy, query audit trails for malpractice risk mitigation, and sub-second response times for point-of-care workflows where clinicians need answers during patient encounters.

## Architecture Diagram
```
Clinician UI ──→ API Gateway (auth + HIPAA) ──→ Query Service ──→ OpenEvidence API
                        ↓                            ↓             /query
                   Audit Logger ──→ Audit DB    Cache (Redis)      /citations
                        ↓                            ↓
                   Analytics ──→ Usage Dashboard  Citation Store ──→ Evidence DB
```

## Service Layer
```typescript
class ClinicalQueryService {
  constructor(private oe: OpenEvidenceClient, private cache: CacheLayer, private audit: AuditLogger) {}

  async queryEvidence(query: ClinicalQuery): Promise<EvidenceResponse> {
    await this.audit.log({ type: 'query_submitted', clinicianId: query.clinicianId, queryText: query.text, timestamp: new Date() });
    const cacheKey = `evidence:${this.hashQuery(query.text)}`;
    const cached = await this.cache.get(cacheKey);
    if (cached) { await this.audit.log({ type: 'cache_hit', cacheKey }); return cached; }
    const response = await this.oe.query(query.text, { specialty: query.specialty });
    await this.storeCitations(response.citations);
    await this.cache.set(cacheKey, response, CACHE_CONFIG.evidence.ttl);
    await this.audit.log({ type: 'query_completed', citationCount: response.citations.length });
    return response;
  }

  async getCitationChain(citationId: string): Promise<Citation[]> {
    return this.evidenceDb.getCitationWithReferences(citationId);
  }
}
```

## Caching Strategy
```typescript
const CACHE_CONFIG = {
  evidence:   { ttl: 86400, prefix: 'evidence' },  // 24 hr — clinical evidence changes slowly
  citations:  { ttl: 604800, prefix: 'cite' },     // 7 days — published citations are stable
  queryHist:  { ttl: 3600, prefix: 'qhist' },      // 1 hr — recent query dedup for same clinician
  guidelines: { ttl: 43200, prefix: 'guide' },      // 12 hr — clinical guidelines update infrequently
  audit:      { ttl: 0, prefix: 'audit' },          // never cached — every audit entry must persist
};
// New guideline publication events invalidate evidence cache for affected specialties
```

## Event Pipeline
```typescript
class ClinicalEventPipeline {
  private queue = new Bull('clinical-events', { redis: process.env.REDIS_URL });

  async onQueryCompleted(event: QueryCompletedEvent): Promise<void> {
    await this.queue.add('process', event, { attempts: 5, backoff: { type: 'exponential', delay: 2000 } });
  }

  async processQueryEvent(event: QueryCompletedEvent): Promise<void> {
    await this.updateUsageAnalytics(event.clinicianId, event.specialty);
    if (event.feedbackScore !== undefined) await this.logFeedback(event);
    await this.checkGuidelineAlignment(event);  // Flag if answer diverges from current guidelines
  }
}
```

## Data Model
```typescript
interface ClinicalQuery    { clinicianId: string; text: string; specialty: string; patientContext?: string; urgency: 'routine' | 'urgent'; }
interface EvidenceResponse { answer: string; confidence: number; citations: Citation[]; specialty: string; responseTimeMs: number; }
interface Citation         { id: string; title: string; journal: string; year: number; doi: string; relevanceScore: number; evidenceLevel: 'I' | 'II' | 'III' | 'IV' | 'V'; }
interface AuditEntry       { id: string; type: string; clinicianId: string; timestamp: Date; queryText?: string; citationCount?: number; ipAddress: string; }
```

## Scaling Considerations
- Separate audit write path from query path — audit logging must never slow clinical responses
- Cache evidence responses aggressively — same clinical questions recur across clinicians
- Partition audit DB by month for compliance retention windows and query performance
- Use read replicas for analytics dashboard; primary DB reserved for audit writes
- Rate-limit per clinician to prevent abuse while ensuring genuine clinical queries are never blocked

## Error Handling
| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| Evidence query | OpenEvidence API timeout | Serve cached response if available, degrade to "consult specialist" message |
| Audit logging | Audit DB write failure | Buffer to local WAL, retry with dead-letter queue — never drop audit entries |
| Citation retrieval | DOI resolution failure | Return citation metadata without full text link, flag for manual review |
| Cache layer | Redis connection lost | Bypass cache, query API directly, alert ops for cache restoration |
| HIPAA compliance | Unauthorized access attempt | Immediate block, audit log, alert security team, preserve evidence |

## Resources
- [OpenEvidence Platform](https://www.openevidence.com)
- [OpenEvidence for Clinicians](https://www.openevidence.com/about)

## Next Steps
See `openevidence-deploy-integration`.
