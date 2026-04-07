---
name: juicebox-reference-architecture
description: |
  Implement Juicebox reference architecture.
  Trigger: "juicebox architecture", "recruiting platform design".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Reference Architecture

## Overview

Production architecture for AI-powered candidate analysis integrations with Juicebox. Designed for recruiting teams needing automated dataset ingestion from job descriptions, intelligent candidate scoring and ranking, result caching for repeated searches, and seamless export to ATS platforms like Greenhouse and Lever. Key design drivers: search result freshness, candidate deduplication across sources, outreach sequencing, and analysis pipeline throughput for high-volume hiring.

## Architecture Diagram
```
Recruiter Dashboard ──→ Search Service ──→ Cache (Redis) ──→ Juicebox API
                             ↓                                /search
                        Queue (Bull) ──→ Analysis Worker      /profiles
                             ↓                                /outreach
                        ATS Export Service ──→ Greenhouse/Lever
                             ↓
                        Webhook Handler ←── Juicebox Events
```

## Service Layer
```typescript
class CandidateSearchService {
  constructor(private juicebox: JuiceboxClient, private cache: CacheLayer) {}

  async findAndRank(criteria: SearchCriteria): Promise<RankedCandidate[]> {
    const cacheKey = `search:${this.hashCriteria(criteria)}`;
    const cached = await this.cache.get(cacheKey);
    if (cached) return cached;
    const results = await this.juicebox.search(criteria);
    const ranked = results.profiles.map(p => ({ ...p, score: this.scoreCandidate(p, criteria) }))
      .sort((a, b) => b.score - a.score);
    await this.cache.set(cacheKey, ranked, CACHE_CONFIG.searchResults.ttl);
    return ranked;
  }

  async exportToATS(candidates: string[], jobId: string, ats: 'greenhouse' | 'lever'): Promise<ExportResult> {
    const deduped = await this.deduplicateAgainstATS(candidates, jobId, ats);
    return this.juicebox.export({ profiles: deduped, destination: ats, job_id: jobId });
  }
}
```

## Caching Strategy
```typescript
const CACHE_CONFIG = {
  searchResults: { ttl: 1800, prefix: 'search' },   // 30 min — candidate pools shift slowly
  profiles:      { ttl: 3600, prefix: 'profile' },   // 1 hr — profile data stable short-term
  analysisRuns:  { ttl: 7200, prefix: 'analysis' },   // 2 hr — analysis results are expensive to recompute
  atsState:      { ttl: 300,  prefix: 'ats' },        // 5 min — ATS pipeline freshness for dedup
  outreach:      { ttl: 60,   prefix: 'outreach' },   // 1 min — sequence status changes frequently
};
// New search invalidates matching cached results; ATS export clears ats cache for that job
```

## Event Pipeline
```typescript
class RecruitingPipeline {
  private queue = new Bull('juicebox-events', { redis: process.env.REDIS_URL });

  async onSearchComplete(searchId: string, results: RankedCandidate[]): Promise<void> {
    await this.queue.add('analyze', { searchId, candidateIds: results.map(r => r.id) },
      { attempts: 3, backoff: { type: 'exponential', delay: 2000 } });
  }

  async processOutreachEvent(event: OutreachEvent): Promise<void> {
    if (event.type === 'reply_received') await this.flagForRecruiterReview(event);
    if (event.type === 'bounced') await this.markInvalid(event.candidateId);
    await this.syncStatusToATS(event);
  }
}
```

## Data Model
```typescript
interface SearchCriteria   { role: string; skills: string[]; location?: string; experienceYears?: number; companySize?: string; }
interface RankedCandidate  { id: string; name: string; title: string; company: string; score: number; skills: string[]; profileUrl: string; }
interface OutreachSequence { id: string; candidateId: string; jobId: string; steps: OutreachStep[]; status: 'active' | 'replied' | 'bounced' | 'opted-out'; }
interface ExportResult     { exported: number; duplicatesSkipped: number; atsJobId: string; }
```

## Scaling Considerations
- Parallelize search requests across role categories — Juicebox API supports concurrent queries
- Cache analysis results aggressively — AI scoring is the most expensive operation per candidate
- Batch ATS exports by job requisition to minimize Greenhouse/Lever API round-trips
- Deduplicate candidates across searches before outreach to avoid double-contacting
- Rate-limit outreach sequencing to maintain sender reputation and deliverability

## Error Handling
| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| Candidate search | Juicebox API timeout | Retry with reduced result count, serve cached results if available |
| Analysis pipeline | Scoring model latency spike | Queue with timeout, return unscored results with flag |
| ATS export | Greenhouse rate limit | Batch retry with exponential backoff, notify recruiter on persistent failure |
| Outreach sequence | Email bounce | Mark candidate invalid, remove from active sequences, update ATS |
| Webhook handler | Duplicate event delivery | Idempotency key on event ID + candidate ID |

## Resources
- [Juicebox AI](https://juicebox.ai)
- [Juicebox Integrations](https://juicebox.ai/integrations)

## Next Steps
See `juicebox-deploy-integration`.
