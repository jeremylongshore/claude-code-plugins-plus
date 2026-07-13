# Clay Reference Architecture - Implementation Details

## Configuration

### Project Layout

```
my-clay-integration/
├── src/
│   ├── client/               # Clay API client wrapper
│   │   ├── index.ts          # Exported client factory
│   │   ├── types.ts          # TypeScript interfaces
│   │   └── interceptors.ts   # Request/response interceptors
│   ├── enrichment/           # Enrichment pipeline
│   │   ├── pipeline.ts       # Main enrichment orchestrator
│   │   ├── transforms.ts     # Data transformation functions
│   │   └── validators.ts     # Input validation
│   ├── webhooks/             # Webhook handlers
│   │   ├── router.ts         # Express/Fastify webhook routes
│   │   ├── verify.ts         # Signature verification
│   │   └── handlers/         # Per-event-type handlers
│   ├── storage/              # Data persistence layer
│   │   ├── repository.ts     # Database operations
│   │   └── cache.ts          # Redis cache layer
│   └── config/               # Environment configuration
│       ├── clay.ts           # Clay-specific config
│       └── index.ts          # Config aggregation
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/
│   ├── seed-dev.ts           # Dev data seeding
│   └── health-check.ts       # Production health check
└── docker-compose.yml        # Local dev environment
```

## Advanced Patterns

### Layered Client Architecture

```typescript
// Layer 1: Raw HTTP client
class ClayHttpClient {
  constructor(private config: ClayConfig) {}

  async request<T>(method: string, path: string, data?: any): Promise<T> {
    const response = await fetch(`${this.config.baseUrl}${path}`, {
      method,
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) throw new ClayApiError(response);
    return response.json();
  }
}

// Layer 2: Domain-specific operations
class ClayEnrichmentService {
  constructor(private http: ClayHttpClient) {}

  async enrichPerson(email: string) {
    return this.http.request('POST', '/enrich/person', { email });
  }

  async enrichCompany(domain: string) {
    return this.http.request('POST', '/enrich/company', { domain });
  }

  async bulkEnrich(items: Array<{ email: string }>) {
    return this.http.request('POST', '/enrich/bulk', { items });
  }
}

// Layer 3: Application-level orchestration
class EnrichmentPipeline {
  constructor(
    private enrichment: ClayEnrichmentService,
    private cache: CacheService,
    private db: DatabaseRepository
  ) {}

  async process(contacts: Contact[]) {
    const uncached = await this.filterCached(contacts);
    const enriched = await this.enrichment.bulkEnrich(uncached);
    await this.cache.setMany(enriched);
    await this.db.upsertContacts(enriched);
    return enriched;
  }
}
```

### Dependency Injection Pattern

```typescript
// container.ts
import { createContainer, asClass, asValue } from 'awilix';

const container = createContainer();

container.register({
  config: asValue(getClayConfig()),
  httpClient: asClass(ClayHttpClient).singleton(),
  enrichmentService: asClass(ClayEnrichmentService).singleton(),
  webhookVerifier: asClass(WebhookVerifier).singleton(),
  cache: asClass(RedisCache).singleton(),
  db: asClass(PostgresRepository).singleton(),
  pipeline: asClass(EnrichmentPipeline).scoped(),
});

export { container };
```

### Health Check Endpoint

```typescript
async function clayHealthCheck(): Promise<HealthStatus> {
  const checks = {
    api: false,
    webhook: false,
    rateLimit: { remaining: 0, limit: 0 },
  };

  try {
    const me = await clay.get('/me');
    checks.api = true;
    checks.rateLimit = parseRateLimits(me.headers);
  } catch { /* logged by interceptor */ }

  try {
    checks.webhook = await verifyWebhookEndpoint();
  } catch { /* logged */ }

  return {
    service: 'clay',
    healthy: checks.api && checks.webhook,
    checks,
    timestamp: new Date().toISOString(),
  };
}
```

## Troubleshooting

### Verifying Architecture Layers

```bash
# Test each layer independently
# Layer 1: Raw HTTP
curl -H "Authorization: Bearer $CLAY_API_KEY" https://api.clay.com/v1/me

# Layer 2: Run enrichment service test
npx ts-node -e "
  const { container } = require('./src/config/container');
  container.resolve('enrichmentService').enrichPerson('test@example.com').then(console.log);
"

# Layer 3: Run pipeline health check
npx ts-node scripts/health-check.ts
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
