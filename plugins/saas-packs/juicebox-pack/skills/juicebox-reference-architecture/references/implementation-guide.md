# Juicebox Reference Architecture - Implementation Guide

Detailed implementation examples and code patterns.

## Architecture Patterns

### Pattern 1: Simple Integration
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Backend   │────▶│  Juicebox   │
│   (React)   │     │   (Node)    │     │    API      │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Best for:** Small applications, MVPs, single-tenant systems

### Pattern 2: Cached Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Backend   │────▶│   Redis     │
│   (React)   │     │   (Node)    │     │   Cache     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                        ┌───────▼───────┐
                                        │   Juicebox    │
                                        │     API       │
                                        └───────────────┘
```

**Best for:** Medium applications, cost optimization

### Pattern 3: Enterprise Architecture
```
                    ┌─────────────────────────────────────────┐
                    │             Load Balancer               │
                    └────────────────────┬────────────────────┘
                                         │
            ┌────────────────────────────┼────────────────────────────┐
            │                            │                            │
    ┌───────▼───────┐           ┌────────▼────────┐          ┌────────▼────────┐
    │   API Server  │           │   API Server    │          │   API Server    │
    │   (Node.js)   │           │   (Node.js)     │          │   (Node.js)     │
    └───────┬───────┘           └────────┬────────┘          └────────┬────────┘
            │                            │                            │
            └────────────────────────────┼────────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
            ┌───────▼───────┐   ┌────────▼────────┐  ┌────────▼────────┐
            │   Redis       │   │   PostgreSQL    │  │   Message       │
            │   (Cache)     │   │   (Profiles)    │  │   Queue         │
            └───────────────┘   └─────────────────┘  └────────┬────────┘
                                                              │
                                                     ┌────────▼────────┐
                                                     │   Worker Pool   │
                                                     │   (Enrichment)  │
                                                     └────────┬────────┘
                                                              │
                                                     ┌────────▼────────┐
                                                     │   Juicebox API  │
                                                     └─────────────────┘
```

**Best for:** Large-scale applications, multi-tenant, high availability

## Implementation

### Core Components

#### 1. API Gateway
```typescript
// gateway/index.ts
import express from 'express';
import { createRateLimiter } from './middleware/rate-limiter';
import { authenticate } from './middleware/auth';
import { validateRequest } from './middleware/validation';

const app = express();

app.use('/api/v1/search', [
  authenticate,
  createRateLimiter({ windowMs: 60000, max: 100 }),
  validateRequest(searchSchema),
  searchController
]);

app.use('/api/v1/profiles', [
  authenticate,
  createRateLimiter({ windowMs: 60000, max: 200 }),
  validateRequest(profileSchema),
  profileController
]);
```

#### 2. Service Layer
```typescript
// services/people-search.service.ts
export class PeopleSearchService {
  constructor(
    private juicebox: JuiceboxClient,
    private cache: CacheService,
    private db: DatabaseService,
    private queue: QueueService
  ) {}

  async search(query: string, options: SearchOptions): Promise<SearchResult> {
    // Check cache first
    const cacheKey = this.getCacheKey(query, options);
    const cached = await this.cache.get(cacheKey);
    if (cached) return cached;

    // Perform search
    const results = await this.juicebox.search.people({
      query,
      ...options
    });

    // Cache results
    await this.cache.set(cacheKey, results, 300);

    // Queue enrichment for top results
    if (options.autoEnrich) {
      await this.queue.add('enrich-profiles', {
        profileIds: results.profiles.slice(0, 10).map(p => p.id)
      });
    }

    return results;
  }

  async getProfile(id: string): Promise<Profile> {
    // Check local DB first
    const local = await this.db.profiles.findUnique({ where: { id } });
    if (local && !this.isStale(local)) {
      return local;
    }

    // Fetch from Juicebox
    const profile = await this.juicebox.profiles.get(id);

    // Store locally
    await this.db.profiles.upsert({
      where: { id },
      create: profile,
      update: profile
    });

    return profile;
  }
}
```

#### 3. Worker Pool
```typescript
// workers/enrichment.worker.ts
import { Worker } from 'bullmq';

const worker = new Worker('enrich-profiles', async (job) => {
  const { profileIds } = job.data;

  const enriched = await juiceboxService.enrichProfiles(profileIds);

  // Store enriched data
  for (const profile of enriched) {
    await db.profiles.upsert({
      where: { id: profile.id },
      create: { ...profile, enrichedAt: new Date() },
      update: { ...profile, enrichedAt: new Date() }
    });
  }

  return { enrichedCount: enriched.length };
}, { connection: redis });
```

#### 4. Database Schema
```sql
-- PostgreSQL schema
CREATE TABLE profiles (
  id VARCHAR(255) PRIMARY KEY,
  name VARCHAR(500),
  title VARCHAR(500),
  company VARCHAR(500),
  location VARCHAR(500),
  email VARCHAR(255),
  phone VARCHAR(50),
  linkedin_url VARCHAR(500),
  skills JSONB,
  experience JSONB,
  education JSONB,
  raw_data JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  enriched_at TIMESTAMP
);

CREATE INDEX idx_profiles_company ON profiles(company);
CREATE INDEX idx_profiles_location ON profiles(location);
CREATE INDEX idx_profiles_skills ON profiles USING GIN(skills);
```

## Deployment Topology

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: juicebox-api
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: api
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: juicebox-workers
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: worker
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
```
