# Juicebox Reference Architecture - Service Layer Code

## Juicebox Client

A thin wrapper that handles auth, retries, and circuit breaking for all Juicebox API calls.

```typescript
// src/services/juicebox-client.ts
import { buildAuthHeader } from '../lib/secrets';

const JUICEBOX_API = 'https://api.juicebox.ai/v1';
const REQUEST_TIMEOUT = 15_000;

export interface SearchParams {
  query: string;
  limit?: number;
  cursor?: string;
  filters?: {
    location?: string;
    companies?: string[];
    skills?: string[];
    experienceYears?: { min?: number; max?: number };
  };
}

export interface Profile {
  id: string;
  name: string;
  title: string;
  company: string;
  location: string;
  linkedin_url: string;
  skills: string[];
  experience: Array<{
    title: string;
    company: string;
    startDate: string;
    endDate?: string;
  }>;
}

export interface EnrichedProfile extends Profile {
  email?: string;
  phone?: string;
  education: Array<{ school: string; degree: string; year?: number }>;
}

export interface SearchResult {
  profiles: Profile[];
  total: number;
  nextCursor?: string;
}

export class JuiceboxClient {
  async search(params: SearchParams): Promise<SearchResult> {
    const headers = await buildAuthHeader();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const res = await fetch(`${JUICEBOX_API}/search`, {
        method: 'POST',
        headers,
        body: JSON.stringify(params),
        signal: controller.signal,
      });

      if (res.status === 429) {
        const retryAfter = parseInt(res.headers.get('retry-after') || '10', 10);
        throw new RateLimitError(retryAfter);
      }
      if (!res.ok) {
        throw new JuiceboxApiError(res.status, await res.text());
      }
      return await res.json();
    } finally {
      clearTimeout(timeout);
    }
  }

  async enrichProfile(profileId: string): Promise<EnrichedProfile> {
    const headers = await buildAuthHeader();
    const res = await fetch(`${JUICEBOX_API}/profiles/${profileId}/enrich`, {
      method: 'POST',
      headers,
    });

    if (!res.ok) {
      throw new JuiceboxApiError(res.status, await res.text());
    }
    return await res.json();
  }

  async getMe(): Promise<{ username: string; plan: string; creditsRemaining: number }> {
    const headers = await buildAuthHeader();
    const res = await fetch(`${JUICEBOX_API}/me`, { headers });
    if (!res.ok) {
      throw new JuiceboxApiError(res.status, await res.text());
    }
    return await res.json();
  }
}

export class JuiceboxApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`Juicebox API error ${status}: ${body}`);
    this.name = 'JuiceboxApiError';
  }
}

export class RateLimitError extends Error {
  constructor(public retryAfterSeconds: number) {
    super(`Rate limited. Retry after ${retryAfterSeconds}s`);
    this.name = 'RateLimitError';
  }
}
```

## Search Service with Caching

```typescript
// src/services/search.service.ts
import { JuiceboxClient, SearchParams, SearchResult, RateLimitError } from './juicebox-client';
import { CacheService } from '../lib/cache';

const SEARCH_CACHE_TTL = 300; // 5 minutes
const MAX_RETRIES = 3;

export class SearchService {
  constructor(
    private client: JuiceboxClient,
    private cache: CacheService,
  ) {}

  async search(params: SearchParams): Promise<SearchResult> {
    // Check cache
    const cacheKey = `search:${this.hashParams(params)}`;
    const cached = await this.cache.get<SearchResult>(cacheKey);
    if (cached) {
      return { ...cached, _fromCache: true } as SearchResult & { _fromCache: boolean };
    }

    // Call Juicebox with retry
    let lastError: Error | undefined;
    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
      try {
        const result = await this.client.search(params);
        await this.cache.set(cacheKey, result, SEARCH_CACHE_TTL);
        return result;
      } catch (err) {
        lastError = err as Error;
        if (err instanceof RateLimitError) {
          await this.sleep(err.retryAfterSeconds * 1000);
        } else {
          await this.sleep(Math.pow(2, attempt) * 1000);
        }
      }
    }
    throw lastError;
  }

  async searchAll(params: Omit<SearchParams, 'cursor'>): AsyncGenerator<SearchResult['profiles'][0]> {
    let cursor: string | undefined;
    do {
      const result = await this.search({ ...params, cursor });
      for (const profile of result.profiles) {
        yield profile;
      }
      cursor = result.nextCursor;
    } while (cursor);
  }

  private hashParams(params: SearchParams): string {
    return Buffer.from(JSON.stringify(params)).toString('base64url');
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## Enrichment Service

```typescript
// src/services/enrichment.service.ts
import { JuiceboxClient, EnrichedProfile } from './juicebox-client';
import { ProfileService } from './profile.service';

export class EnrichmentService {
  constructor(
    private client: JuiceboxClient,
    private profiles: ProfileService,
  ) {}

  async enrichAndStore(profileId: string): Promise<EnrichedProfile> {
    // Check if already enriched recently
    const existing = await this.profiles.findById(profileId);
    if (existing?.enrichedAt && !this.isStale(existing.enrichedAt)) {
      return existing as EnrichedProfile;
    }

    // Enrich via Juicebox API
    const enriched = await this.client.enrichProfile(profileId);

    // Persist to PostgreSQL
    await this.profiles.upsert({
      ...enriched,
      enrichedAt: new Date(),
    });

    return enriched;
  }

  async enrichBatch(profileIds: string[]): Promise<EnrichedProfile[]> {
    const results: EnrichedProfile[] = [];
    for (const id of profileIds) {
      try {
        const enriched = await this.enrichAndStore(id);
        results.push(enriched);
      } catch (err) {
        console.error(`Enrichment failed for ${id}:`, err);
        // Continue with remaining profiles
      }
    }
    return results;
  }

  private isStale(enrichedAt: Date): boolean {
    const ONE_DAY = 24 * 60 * 60 * 1000;
    return Date.now() - enrichedAt.getTime() > ONE_DAY;
  }
}
```

## ATS Sync Service

```typescript
// src/services/ats-sync.service.ts

interface ATSCandidate {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  linkedin_url?: string;
  job_id: string;
  source: string;
}

export class ATSSyncService {
  private mergeApiKey: string;
  private mergeAccountToken: string;

  constructor(mergeApiKey: string, mergeAccountToken: string) {
    this.mergeApiKey = mergeApiKey;
    this.mergeAccountToken = mergeAccountToken;
  }

  /**
   * Export an enriched Juicebox profile to your ATS via Merge API.
   * Supports Greenhouse, Lever, Ashby, Workday, and 50+ other systems.
   */
  async exportCandidate(
    enrichedProfile: EnrichedProfile,
    jobId: string,
  ): Promise<{ mergeId: string; atsId: string }> {
    const [firstName, ...lastParts] = enrichedProfile.name.split(' ');
    const lastName = lastParts.join(' ') || firstName;

    const candidate: ATSCandidate = {
      first_name: firstName,
      last_name: lastName,
      email: enrichedProfile.email || '',
      phone: enrichedProfile.phone,
      linkedin_url: enrichedProfile.linkedin_url,
      job_id: jobId,
      source: 'Juicebox PeopleGPT',
    };

    const res = await fetch('https://api.merge.dev/api/ats/v1/candidates', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.mergeApiKey}`,
        'X-Account-Token': this.mergeAccountToken,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ model: candidate }),
    });

    if (!res.ok) {
      throw new Error(`Merge API error ${res.status}: ${await res.text()}`);
    }

    const result = await res.json();
    return {
      mergeId: result.model.id,
      atsId: result.model.remote_id,
    };
  }
}
```

## Enrichment Worker

```typescript
// src/workers/enrichment.worker.ts
import { Worker, Job } from 'bullmq';
import { JuiceboxClient } from '../services/juicebox-client';
import { EnrichmentService } from '../services/enrichment.service';
import { ProfileService } from '../services/profile.service';
import { ATSSyncService } from '../services/ats-sync.service';
import Redis from 'ioredis';

const connection = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

const juicebox = new JuiceboxClient();
const profiles = new ProfileService(/* db connection */);
const enrichment = new EnrichmentService(juicebox, profiles);
const atsSync = new ATSSyncService(
  process.env.MERGE_API_KEY!,
  process.env.MERGE_ACCOUNT_TOKEN!,
);

const worker = new Worker(
  'enrichment',
  async (job: Job) => {
    const { profileIds, jobId, exportToATS } = job.data;

    // Enrich all profiles
    const enrichedProfiles = await enrichment.enrichBatch(profileIds);
    console.log(`Enriched ${enrichedProfiles.length}/${profileIds.length} profiles`);

    // Optionally export to ATS
    if (exportToATS && jobId) {
      let exported = 0;
      for (const profile of enrichedProfiles) {
        if (profile.email) {
          try {
            await atsSync.exportCandidate(profile, jobId);
            exported++;
          } catch (err) {
            console.error(`ATS export failed for ${profile.id}:`, err);
          }
        }
      }
      console.log(`Exported ${exported} candidates to ATS`);
    }

    return {
      enriched: enrichedProfiles.length,
      total: profileIds.length,
    };
  },
  {
    connection,
    concurrency: 5,
    limiter: {
      max: 10,
      duration: 60_000, // 10 jobs per minute to respect rate limits
    },
  },
);

worker.on('failed', (job, err) => {
  console.error(`Job ${job?.id} failed:`, err.message);
});

console.log('Enrichment worker started');
```

## Webhook Handler

```typescript
// src/routes/webhooks.ts
import { Router, Request, Response } from 'express';
import crypto from 'crypto';

const router = Router();
const WEBHOOK_SECRET = process.env.JUICEBOX_WEBHOOK_SECRET!;

function verifySignature(payload: string, signature: string): boolean {
  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature, 'hex'),
    Buffer.from(expected, 'hex'),
  );
}

router.post('/webhooks/juicebox', (req: Request, res: Response) => {
  const signature = req.headers['x-juicebox-signature'] as string;
  const rawBody = JSON.stringify(req.body);

  if (!signature || !verifySignature(rawBody, signature)) {
    res.status(401).json({ error: 'Invalid webhook signature' });
    return;
  }

  const { event, data } = req.body;

  switch (event) {
    case 'agent.completed':
      console.log(`Agent completed: ${data.agentId}, found ${data.candidateCount} candidates`);
      break;
    case 'enrichment.completed':
      console.log(`Enrichment batch ${data.batchId} completed: ${data.enrichedCount} profiles`);
      break;
    case 'credits.low':
      console.warn(`Juicebox credits low: ${data.remaining} remaining`);
      break;
    default:
      console.log(`Unhandled Juicebox webhook event: ${event}`);
  }

  res.status(200).json({ received: true });
});

export default router;
```

## Database Schema

```sql
-- db/schema.sql

CREATE TABLE profiles (
  id            VARCHAR(255) PRIMARY KEY,
  name          VARCHAR(500) NOT NULL,
  title         VARCHAR(500),
  company       VARCHAR(500),
  location      VARCHAR(500),
  email         VARCHAR(255),
  phone         VARCHAR(50),
  linkedin_url  VARCHAR(500),
  skills        JSONB DEFAULT '[]',
  experience    JSONB DEFAULT '[]',
  education     JSONB DEFAULT '[]',
  raw_data      JSONB,
  source        VARCHAR(50) DEFAULT 'juicebox',
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW(),
  enriched_at   TIMESTAMPTZ
);

CREATE INDEX idx_profiles_company ON profiles(company);
CREATE INDEX idx_profiles_location ON profiles(location);
CREATE INDEX idx_profiles_skills ON profiles USING GIN(skills);
CREATE INDEX idx_profiles_enriched ON profiles(enriched_at) WHERE enriched_at IS NOT NULL;

CREATE TABLE search_history (
  id            SERIAL PRIMARY KEY,
  query         TEXT NOT NULL,
  filters       JSONB,
  result_count  INTEGER,
  latency_ms    INTEGER,
  cached        BOOLEAN DEFAULT false,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ats_exports (
  id            SERIAL PRIMARY KEY,
  profile_id    VARCHAR(255) REFERENCES profiles(id),
  merge_id      VARCHAR(255),
  ats_id        VARCHAR(255),
  job_id        VARCHAR(255),
  status        VARCHAR(50) DEFAULT 'pending',
  exported_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_exports_profile ON ats_exports(profile_id);
CREATE INDEX idx_exports_status ON ats_exports(status);
```

## Environment Configuration

```typescript
// src/config.ts

interface JuiceboxConfig {
  apiUrl: string;
  secretId: string;
  cacheTtl: number;
  enrichmentConcurrency: number;
  rateLimitPerMinute: number;
}

const configs: Record<string, JuiceboxConfig> = {
  development: {
    apiUrl: 'https://api.juicebox.ai/v1',
    secretId: 'juicebox/dev-credentials',
    cacheTtl: 60,
    enrichmentConcurrency: 2,
    rateLimitPerMinute: 10,
  },
  staging: {
    apiUrl: 'https://api.juicebox.ai/v1',
    secretId: 'juicebox/staging-credentials',
    cacheTtl: 300,
    enrichmentConcurrency: 5,
    rateLimitPerMinute: 30,
  },
  production: {
    apiUrl: 'https://api.juicebox.ai/v1',
    secretId: 'juicebox/prod-credentials',
    cacheTtl: 300,
    enrichmentConcurrency: 10,
    rateLimitPerMinute: 60,
  },
};

export function getConfig(): JuiceboxConfig {
  const env = process.env.NODE_ENV || 'development';
  const config = configs[env];
  if (!config) {
    throw new Error(`No Juicebox config for environment: ${env}`);
  }
  return config;
}
```
