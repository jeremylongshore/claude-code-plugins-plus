---
name: apollo-reference-architecture
description: |
  Implement Apollo.io reference architecture.
  Use when designing Apollo integrations, establishing patterns,
  or building production-grade sales intelligence systems.
  Trigger with phrases like "apollo architecture", "apollo system design",
  "apollo integration patterns", "apollo best practices architecture".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, apollo-reference]

---
# Apollo Reference Architecture

## Overview
Production-ready reference architecture for Apollo.io integrations. Layered design with API client, service layer, background jobs, database models, CRM sync, and deals pipeline — all built around Apollo's REST API with correct endpoints and `x-api-key` authentication.

## Prerequisites
- Apollo master API key
- Node.js 18+ with TypeScript
- PostgreSQL for data layer
- Redis for job queues

## Instructions

### Step 1: Architecture Diagram
```
┌───────────────────────────────────────────────┐
│                 API Layer                      │  Express routes
│  POST /api/leads/search     GET /api/org/:d    │  POST /api/deals
├───────────────────────────────────────────────┤
│              Service Layer                     │  Business logic
│  LeadService    EnrichService   DealService    │  SequenceService
├───────────────────────────────────────────────┤
│              Client Layer                      │  Apollo API wrapper
│  ApolloClient   RateLimiter   Cache            │  CreditTracker
├───────────────────────────────────────────────┤
│            Background Jobs                     │  BullMQ queues
│  EnrichJob    SyncJob    StageChangeJob        │  TaskCreatorJob
├───────────────────────────────────────────────┤
│              Data Layer                        │  Prisma/TypeORM
│  Contact   Organization   Deal   AuditLog      │
└───────────────────────────────────────────────┘
```

### Step 2: Service Layer
```typescript
// src/services/lead-service.ts
import { getApolloClient } from '../apollo/client';
import { withRetry } from '../apollo/retry';
import { cachedRequest } from '../apollo/cache';

export class LeadService {
  private client = getApolloClient();

  async searchPeople(params: { domains: string[]; titles?: string[]; seniorities?: string[]; page?: number }) {
    return cachedRequest('/mixed_people/api_search',
      () => withRetry(() => this.client.post('/mixed_people/api_search', {
        q_organization_domains_list: params.domains,
        person_titles: params.titles,
        person_seniorities: params.seniorities,
        page: params.page ?? 1, per_page: 100,
      })),
      params,
    );
  }

  async enrichPerson(email: string) {
    return withRetry(() => this.client.post('/people/match', { email }));
  }

  async enrichOrg(domain: string) {
    return cachedRequest('/organizations/enrich',
      () => withRetry(() => this.client.get('/organizations/enrich', { params: { domain } })),
      { domain },
    );
  }
}
```

### Step 3: Deals/Opportunities Service
Apollo has a full Deals API for tracking revenue pipeline.

```typescript
// src/services/deal-service.ts
export class DealService {
  private client = getApolloClient();

  async createDeal(params: {
    name: string;
    amount: number;
    ownerId: string;       // Apollo user ID
    accountId?: string;    // Apollo account ID
    contactIds?: string[]; // Apollo contact IDs
    stageId?: string;      // Deal stage ID
  }) {
    const { data } = await this.client.post('/opportunities', {
      name: params.name,
      amount: params.amount,
      owner_id: params.ownerId,
      account_id: params.accountId,
      contact_ids: params.contactIds,
      opportunity_stage_id: params.stageId,
    });
    return { dealId: data.opportunity.id, name: data.opportunity.name };
  }

  async listDeals(page: number = 1) {
    const { data } = await this.client.post('/opportunities/search', { page, per_page: 50 });
    return data.opportunities.map((d: any) => ({
      id: d.id, name: d.name, amount: d.amount,
      stage: d.opportunity_stage?.name, owner: d.owner?.name,
    }));
  }

  async getDealStages() {
    const { data } = await this.client.get('/opportunity_stages');
    return data.opportunity_stages.map((s: any) => ({ id: s.id, name: s.name, order: s.display_order }));
  }

  async updateDeal(dealId: string, updates: { amount?: number; stageId?: string }) {
    await this.client.patch(`/opportunities/${dealId}`, {
      amount: updates.amount,
      opportunity_stage_id: updates.stageId,
    });
  }
}
```

### Step 4: Background Job Processing
```typescript
// src/jobs/enrichment-job.ts
import { Queue, Worker, Job } from 'bullmq';
import { LeadService } from '../services/lead-service';

const connection = { host: process.env.REDIS_HOST ?? 'localhost', port: 6379 };

export const enrichmentQueue = new Queue('apollo-enrichment', {
  connection,
  defaultJobOptions: {
    attempts: 3,
    backoff: { type: 'exponential', delay: 5000 },
    removeOnComplete: 1000,
  },
});

const leadService = new LeadService();

new Worker('apollo-enrichment', async (job: Job) => {
  switch (job.name) {
    case 'enrich-person':
      return leadService.enrichPerson(job.data.email);
    case 'enrich-org':
      return leadService.enrichOrg(job.data.domain);
    case 'bulk-search': {
      const results: any[] = [];
      for (const domain of job.data.domains) {
        const { data } = await leadService.searchPeople({ domains: [domain] });
        results.push(...data.people);
        await job.updateProgress(results.length);
      }
      return { total: results.length };
    }
  }
}, { connection, concurrency: 3, limiter: { max: 50, duration: 60_000 } });
```

### Step 5: Database Model
```typescript
// src/models/contact.ts (Prisma schema excerpt)
// model Contact {
//   id             String   @id @default(cuid())
//   apolloId       String   @unique
//   email          String   @unique
//   name           String
//   title          String?
//   seniority      String?
//   phone          String?
//   linkedinUrl    String?
//   organizationId String?
//   rawApolloData  Json?
//   enrichedAt     DateTime?
//   createdAt      DateTime @default(now())
//   updatedAt      DateTime @updatedAt
// }

// TypeORM version
import { Entity, Column, PrimaryColumn, CreateDateColumn, UpdateDateColumn } from 'typeorm';

@Entity('contacts')
export class Contact {
  @PrimaryColumn() apolloId: string;
  @Column({ unique: true }) email: string;
  @Column() name: string;
  @Column({ nullable: true }) title: string;
  @Column({ nullable: true }) seniority: string;
  @Column({ nullable: true }) phone: string;
  @Column({ nullable: true }) linkedinUrl: string;
  @Column({ type: 'jsonb', nullable: true }) rawApolloData: Record<string, any>;
  @Column({ nullable: true }) enrichedAt: Date;
  @CreateDateColumn() createdAt: Date;
  @UpdateDateColumn() updatedAt: Date;
}
```

### Step 6: API Routes
```typescript
// src/api/routes.ts
import { Router } from 'express';
import { LeadService } from '../services/lead-service';
import { DealService } from '../services/deal-service';

const router = Router();
const leads = new LeadService();
const deals = new DealService();

router.post('/api/leads/search', async (req, res) => {
  const { data } = await leads.searchPeople(req.body);
  res.json({ leads: data.people, pagination: data.pagination });
});

router.post('/api/leads/enrich', async (req, res) => {
  const { data } = await leads.enrichPerson(req.body.email);
  res.json({ contact: data.person });
});

router.get('/api/organizations/:domain', async (req, res) => {
  const { data } = await leads.enrichOrg(req.params.domain);
  res.json({ organization: data.organization });
});

router.post('/api/deals', async (req, res) => {
  const result = await deals.createDeal(req.body);
  res.json(result);
});

router.get('/api/deals', async (req, res) => {
  const list = await deals.listDeals(parseInt(req.query.page as string) || 1);
  res.json({ deals: list });
});

export { router };
```

## Output
- Layered architecture: API, Service, Client, Jobs, Data
- `LeadService` with cached search and retried enrichment
- `DealService` with create, list, update, and stage management
- BullMQ background jobs for async enrichment
- Database model (Prisma + TypeORM)
- Express API routes for search, enrichment, and deals

## Error Handling
| Layer | Strategy |
|-------|----------|
| Client | Retry with backoff, circuit breaker for prolonged outages |
| Service | Cache fallback on failure, credit budget enforcement |
| Jobs | 3 retries with exponential backoff, dead letter after max |
| API | Structured JSON error responses with error codes |

## Resources
- [Apollo API Overview](https://docs.apollo.io/docs/api-overview)
- [Create Deal](https://docs.apollo.io/reference/create-deal)
- [List Deals](https://docs.apollo.io/reference/list-all-deals)
- [Deal Stages](https://docs.apollo.io/reference/list-deal-stages)
- [BullMQ Documentation](https://docs.bullmq.io/)

## Next Steps
Proceed to `apollo-multi-env-setup` for environment configuration.
