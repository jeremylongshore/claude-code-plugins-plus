---
name: finta-reference-architecture
description: 'Reference architecture for fundraising operations with Finta CRM.

  Trigger with phrases like "finta architecture", "finta fundraising stack".

  '
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- fundraising-crm
- investor-management
- finta
compatibility: Designed for Claude Code
---
# Finta Reference Architecture

## Overview

Production architecture for fundraising operations integrating with Finta's CRM platform. Designed for startup founders and fund managers who need investor pipeline visibility, automated round management, and document room analytics. Key design drivers: deal velocity tracking, investor communication audit trail, capital collection automation via Stripe, and CRM integration with external systems like HubSpot or Salesforce for LP relationship management.

## Architecture Diagram
```
Founder Dashboard ──→ Pipeline Service ──→ Cache (Redis) ──→ Finta API
                           ↓                                  /investors
                      Queue (Bull) ──→ Email Sync Worker      /rounds
                           ↓                                  /deal-rooms
                      Doc Room Service ──→ Finta Deal Rooms   /documents
                           ↓
                      Zapier Webhooks ──→ Slack / Sheets / CRM
```

## Service Layer
```typescript
class FundraiseService {
  constructor(private finta: FintaClient, private cache: CacheLayer) {}

  async getPipelineSnapshot(roundId: string): Promise<PipelineSnapshot> {
    const investors = await this.cache.getOrFetch(`round:${roundId}:investors`,
      () => this.finta.getInvestorsByRound(roundId));
    return { total: investors.length, byStage: this.groupByStage(investors),
             committed: investors.filter(i => i.stage === 'committed').reduce((s, i) => s + i.amount, 0) };
  }

  async moveInvestor(investorId: string, toStage: string): Promise<void> {
    await this.finta.updateInvestor(investorId, { stage: toStage });
    await this.cache.invalidate(`investor:${investorId}`);
    await this.queue.add('stage-change', { investorId, toStage, timestamp: Date.now() });
  }
}
```

## Caching Strategy
```typescript
const CACHE_CONFIG = {
  rounds:     { ttl: 600, prefix: 'round' },     // 10 min — round terms rarely change mid-raise
  investors:  { ttl: 120, prefix: 'investor' },   // 2 min — stage changes need freshness
  documents:  { ttl: 300, prefix: 'doc' },         // 5 min — doc list stable between uploads
  dealRooms:  { ttl: 60,  prefix: 'room' },        // 1 min — view analytics need near-real-time
  metrics:    { ttl: 30,  prefix: 'metric' },      // 30s — commitment totals are time-sensitive
};
// Stage-change webhooks flush investor cache immediately for dashboard accuracy
```

## Event Pipeline
```typescript
class FundraiseEventPipeline {
  private queue = new Bull('finta-events', { redis: process.env.REDIS_URL });

  async onStageChange(event: StageChangeEvent): Promise<void> {
    await this.queue.add('notify', event, { attempts: 3, backoff: { type: 'exponential', delay: 2000 } });
  }

  async processNotification(event: StageChangeEvent): Promise<void> {
    if (event.toStage === 'committed') await this.notifySlack(`${event.investorName} committed $${event.amount}`);
    if (event.toStage === 'passed') await this.logPassReason(event);
    await this.syncToCRM(event);  // Push stage change to HubSpot/Salesforce
  }
}
```

## Data Model
```typescript
interface Round     { id: string; name: string; targetAmount: number; instrument: 'SAFE' | 'convertible-note' | 'priced'; status: 'active' | 'closed'; }
interface Investor  { id: string; name: string; email: string; firm: string; roundId: string; stage: 'contacted' | 'meeting' | 'dd' | 'term-sheet' | 'committed' | 'passed'; amount: number; }
interface DealRoom  { id: string; roundId: string; investorIds: string[]; documents: Document[]; viewAnalytics: ViewEvent[]; }
interface Document  { id: string; name: string; type: 'pitch-deck' | 'financials' | 'cap-table' | 'legal'; uploadedAt: string; viewCount: number; }
```

## Scaling Considerations
- Partition investor pipelines by round to keep active-raise queries fast and isolated
- Buffer email sync operations — Gmail/Outlook API rate limits are aggressive for bulk tracking
- Batch Zapier webhook deliveries to avoid per-event overhead during rapid stage updates
- Cache commitment totals at round level; invalidate on any investor stage change
- Use read-through cache for deal room analytics — investors check rooms sporadically but in bursts

## Error Handling
| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| Investor sync | Finta API rate limit | Queue with exponential backoff, per-round circuit breaker |
| Deal room upload | S3/storage timeout | Retry with resumable upload, notify founder on failure |
| Email tracking | Gmail OAuth token expired | Auto-refresh token, fallback to manual logging alert |
| Stripe collection | Payment declined | Retry schedule (1d, 3d, 7d), escalate to founder dashboard |
| CRM sync | HubSpot conflict | Last-write-wins with Finta as source of truth, log discrepancies |

## Resources
- [Finta Website](https://www.trustfinta.com)
- [Finta for Fund Managers](https://www.trustfinta.com/blog/finta-for-fund-managers-venture-capital-crm)

## Next Steps
See `finta-deploy-integration`.
