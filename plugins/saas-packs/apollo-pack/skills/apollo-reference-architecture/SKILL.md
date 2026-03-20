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
---
# Apollo Reference Architecture

## Overview
Production-ready reference architecture for Apollo.io integrations. Implements a layered design with API client, service layer, background job processing, database models, and CRM sync — all built around the Apollo REST API (`https://api.apollo.io/v1`).

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ with TypeScript
- PostgreSQL or similar database
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Define the Layered Architecture
```
┌─────────────────────────────────────────┐
│              API Layer                   │  Express/Fastify routes
│  POST /api/leads/search                  │  GET /api/leads/:id
├─────────────────────────────────────────┤
│           Service Layer                  │  Business logic
│  LeadService   EnrichmentService         │  SequenceService
├─────────────────────────────────────────┤
│           Client Layer                   │  Apollo API wrapper
│  ApolloClient  RateLimiter  Cache        │  CircuitBreaker
├─────────────────────────────────────────┤
│         Background Jobs                  │  Bull queues
│  EnrichmentJob  SyncJob  CleanupJob      │
├─────────────────────────────────────────┤
│          Data Layer                      │  TypeORM/Prisma models
│  Contact  Organization  Sequence  Audit  │
└─────────────────────────────────────────┘
```

### Step 2: Implement the Service Layer
```typescript
// src/services/lead-service.ts
import { getApolloClient } from '../apollo/client';
import { withRetry } from '../apollo/retry';
import { cachedRequest } from '../apollo/cache';

export class LeadService {
  private client = getApolloClient();

  async searchLeads(params: {
    domains: string[];
    titles?: string[];
    seniority?: string[];
    page?: number;
  }) {
    return cachedRequest(
      '/people/search',
      () => withRetry(() =>
        this.client.post('/people/search', {
          q_organization_domains: params.domains,
          person_titles: params.titles,
          person_seniorities: params.seniority,
          page: params.page ?? 1,
          per_page: 100,
        }),
      ),
      params,
    );
  }

  async enrichContact(email: string) {
    return withRetry(() =>
      this.client.post('/people/match', { email }),
    );
  }

  async enrichOrganization(domain: string) {
    return cachedRequest(
      '/organizations/enrich',
      () => withRetry(() =>
        this.client.get('/organizations/enrich', { params: { domain } }),
      ),
      { domain },
    );
  }
}
```

### Step 3: Add Background Job Processing
```typescript
// src/jobs/enrichment-job.ts
import { Queue, Worker, Job } from 'bullmq';
import { LeadService } from '../services/lead-service';

const enrichmentQueue = new Queue('apollo-enrichment', {
  connection: { host: process.env.REDIS_HOST ?? 'localhost', port: 6379 },
  defaultJobOptions: {
    attempts: 3,
    backoff: { type: 'exponential', delay: 5000 },
    removeOnComplete: 1000,
    removeOnFail: 5000,
  },
});

const worker = new Worker('apollo-enrichment', async (job: Job) => {
  const leadService = new LeadService();

  switch (job.name) {
    case 'enrich-contact':
      return leadService.enrichContact(job.data.email);

    case 'enrich-organization':
      return leadService.enrichOrganization(job.data.domain);

    case 'bulk-search': {
      const results = [];
      for (const domain of job.data.domains) {
        const { data } = await leadService.searchLeads({ domains: [domain] });
        results.push(...data.people);
        await job.updateProgress(results.length);
      }
      return { total: results.length };
    }
  }
}, {
  connection: { host: process.env.REDIS_HOST ?? 'localhost', port: 6379 },
  concurrency: 3,
  limiter: { max: 50, duration: 60_000 },  // 50 jobs per minute
});

// Queue jobs from API routes:
// await enrichmentQueue.add('enrich-contact', { email: 'jane@example.com' });
// await enrichmentQueue.add('bulk-search', { domains: ['stripe.com', 'notion.so'] });
```

### Step 4: Define Database Models
```typescript
// src/models/contact.ts (TypeORM example)
import { Entity, Column, PrimaryColumn, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

@Entity('contacts')
export class Contact {
  @PrimaryColumn()
  apolloId: string;

  @Column()
  @Index()
  email: string;

  @Column()
  name: string;

  @Column({ nullable: true })
  title: string;

  @Column({ nullable: true })
  seniority: string;

  @Column({ nullable: true })
  phone: string;

  @Column({ nullable: true })
  linkedinUrl: string;

  @Column({ nullable: true })
  organizationId: string;

  @Column({ type: 'jsonb', nullable: true })
  rawApolloData: Record<string, any>;

  @Column({ default: 'active' })
  status: 'active' | 'enriched' | 'deleted';

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @Column({ nullable: true })
  lastEnrichedAt: Date;
}
```

### Step 5: Build CRM Sync Service
```typescript
// src/services/crm-sync.ts
import { LeadService } from './lead-service';

interface CrmContact {
  externalId: string;
  email: string;
  name: string;
  title: string;
  company: string;
  phone?: string;
  source: 'apollo';
}

export class CrmSyncService {
  private leadService = new LeadService();

  async syncNewLeads(domains: string[]): Promise<CrmContact[]> {
    const contacts: CrmContact[] = [];

    for (const domain of domains) {
      const { data } = await this.leadService.searchLeads({
        domains: [domain],
        seniority: ['vp', 'director', 'c_suite'],
      });

      for (const person of data.people) {
        contacts.push({
          externalId: person.id,
          email: person.email,
          name: person.name,
          title: person.title,
          company: person.organization?.name ?? domain,
          phone: person.phone_numbers?.[0]?.sanitized_number,
          source: 'apollo',
        });
      }
    }

    // Push to your CRM (Salesforce, HubSpot, etc.)
    // await this.crmClient.upsertContacts(contacts);

    return contacts;
  }
}
```

### Step 6: Expose API Endpoints
```typescript
// src/api/routes.ts
import express from 'express';
import { LeadService } from '../services/lead-service';

const router = express.Router();
const leadService = new LeadService();

router.post('/api/leads/search', async (req, res) => {
  const { domains, titles, seniority, page } = req.body;
  const { data } = await leadService.searchLeads({ domains, titles, seniority, page });
  res.json({
    leads: data.people,
    pagination: data.pagination,
  });
});

router.post('/api/leads/enrich', async (req, res) => {
  const { email } = req.body;
  const { data } = await leadService.enrichContact(email);
  res.json({ contact: data.person });
});

router.get('/api/organizations/:domain', async (req, res) => {
  const { data } = await leadService.enrichOrganization(req.params.domain);
  res.json({ organization: data.organization });
});

export { router };
```

## Output
- Layered architecture diagram (API, Service, Client, Jobs, Data)
- `LeadService` with cached search, retried enrichment, and org lookup
- BullMQ background jobs for async enrichment and bulk search
- TypeORM entity model for contacts with Apollo data
- CRM sync service converting Apollo contacts to CRM format
- Express API routes exposing search and enrichment endpoints

## Error Handling
| Layer | Strategy |
|-------|----------|
| Client | Retry with exponential backoff, circuit breaker |
| Service | Graceful degradation, return cached data on failure |
| Jobs | 3 retries with exponential backoff, dead letter queue after max retries |
| API | Structured error responses with status codes and messages |

## Examples

### Full Stack Usage
```typescript
import { LeadService } from './services/lead-service';
import { enrichmentQueue } from './jobs/enrichment-job';

const leadService = new LeadService();

// 1. Search leads synchronously
const { data } = await leadService.searchLeads({
  domains: ['stripe.com'],
  seniority: ['vp', 'director'],
});
console.log(`Found ${data.people.length} leads`);

// 2. Queue async enrichment for each lead
for (const person of data.people) {
  await enrichmentQueue.add('enrich-contact', { email: person.email });
}
```

## Resources
- [BullMQ Documentation](https://docs.bullmq.io/)
- [TypeORM Entities](https://typeorm.io/entities)
- [Apollo API Documentation](https://apolloio.github.io/apollo-api-docs/)

## Next Steps
Proceed to `apollo-multi-env-setup` for environment configuration.
