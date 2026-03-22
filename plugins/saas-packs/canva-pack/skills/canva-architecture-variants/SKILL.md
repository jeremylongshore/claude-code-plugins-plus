---
name: canva-architecture-variants
description: |
  Choose and implement Canva Connect API architecture blueprints for different scales.
  Use when designing new Canva integrations, choosing between monolith/service/microservice
  architectures, or planning migration paths.
  Trigger with phrases like "canva architecture", "canva blueprint",
  "how to structure canva", "canva project layout", "canva microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Architecture Variants

## Overview

Three validated architecture patterns for Canva Connect API integrations. All use the REST API at `api.canva.com/rest/v1/*` with OAuth 2.0 PKCE tokens. The key architectural decision is how to handle token storage, async operations (exports, autofills), and rate limit management.

## Variant A: Monolith (Simple)

**Best for:** MVPs, small teams, < 100 Canva users

```
my-app/
├── src/
│   ├── canva/
│   │   ├── client.ts          # REST client with auto-refresh
│   │   ├── auth.ts            # OAuth PKCE flow
│   │   └── types.ts
│   ├── routes/
│   │   ├── auth.ts            # OAuth callback
│   │   └── designs.ts         # Design CRUD
│   ├── store/
│   │   └── tokens.ts          # SQLite/file token store
│   └── index.ts
```

```typescript
// Direct API calls in route handlers
app.post('/api/designs', async (req, res) => {
  const canva = getClientForUser(req.user.id);

  const { design } = await canva.request('/designs', {
    method: 'POST',
    body: JSON.stringify({
      design_type: { type: 'custom', width: 1080, height: 1080 },
      title: req.body.title,
    }),
  });

  res.json({ designId: design.id, editUrl: design.urls.edit_url });
});
```

**Pros:** Fast to build, simple token management, easy to debug.
**Cons:** Synchronous exports block requests, no job queue for autofills.

---

## Variant B: Service Layer (Moderate)

**Best for:** Growing apps, 100-1,000 users, multiple Canva features

```
my-app/
├── src/
│   ├── canva/
│   │   ├── client.ts
│   │   └── auth.ts
│   ├── services/
│   │   ├── design.service.ts   # Business logic + caching
│   │   ├── export.service.ts   # Async export with polling
│   │   ├── asset.service.ts    # Upload management
│   │   └── template.service.ts # Autofill orchestration
│   ├── queue/
│   │   └── export-worker.ts    # Background export processing
│   ├── routes/
│   └── store/
│       └── tokens.ts           # PostgreSQL encrypted tokens
```

```typescript
// Service layer handles caching, retry, and async operations
class ExportService {
  constructor(
    private canva: CanvaClient,
    private cache: Redis,
    private queue: Bull.Queue
  ) {}

  async exportDesign(designId: string, format: object): Promise<string> {
    // Check cache for recent export
    const cached = await this.cache.get(`export:${designId}:${JSON.stringify(format)}`);
    if (cached) return cached;

    // Queue export job — don't block the request
    const job = await this.queue.add('canva-export', { designId, format });
    return job.id;
  }
}

// Background worker polls Canva export API
exportQueue.process('canva-export', async (job) => {
  const { designId, format } = job.data;
  const canva = await getServiceClient();

  const { job: exportJob } = await canva.request('/exports', {
    method: 'POST',
    body: JSON.stringify({ design_id: designId, format }),
  });

  // Poll for completion
  let result = exportJob;
  while (result.status === 'in_progress') {
    await new Promise(r => setTimeout(r, 2000));
    const poll = await canva.request(`/exports/${result.id}`);
    result = poll.job;
  }

  return result.status === 'success' ? result.urls : null;
});
```

**Pros:** Non-blocking exports, caching, separation of concerns.
**Cons:** More infrastructure (Redis, job queue), more complex deployment.

---

## Variant C: Microservice (Enterprise)

**Best for:** 1,000+ users, multi-team, strict SLAs, Canva Enterprise with autofill

```
canva-service/                # Dedicated microservice
├── src/
│   ├── api/
│   │   └── grpc/             # Internal gRPC API
│   ├── canva/
│   │   ├── client.ts
│   │   └── auth.ts
│   ├── services/
│   ├── workers/
│   │   ├── export.worker.ts
│   │   ├── autofill.worker.ts
│   │   └── webhook.worker.ts
│   └── store/
│       └── tokens.ts         # Vault-backed token storage
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hpa.yaml              # Scale based on queue depth
```

**Key differences:**
- Dedicated service owns all Canva API interaction
- gRPC for internal services, REST for external
- Separate workers for exports, autofills, webhooks
- Circuit breaker per operation type
- Token storage in HashiCorp Vault or KMS
- HPA scales based on export queue depth

---

## Decision Matrix

| Factor | Monolith | Service Layer | Microservice |
|--------|----------|---------------|--------------|
| Users | < 100 | 100-1,000 | 1,000+ |
| Team Size | 1-3 | 3-10 | 10+ |
| Export Volume | < 100/day | 100-2,000/day | 2,000-5,000/day |
| Canva Tier | Free/Pro | Pro/Teams | Enterprise |
| Infrastructure | Single server | App + Redis + queue | Kubernetes |
| Time to Build | 1-2 days | 1-2 weeks | 2-4 weeks |

## Migration Path

```
Monolith → Service Layer:
1. Extract canva/ to services/
2. Add Redis for caching
3. Add BullMQ for async exports
4. Move token store to PostgreSQL

Service Layer → Microservice:
1. Create canva-service repository
2. Define gRPC contract
3. Add per-operation workers
4. Deploy to Kubernetes
5. Migrate token store to Vault
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Over-engineering | Wrong variant | Start simpler, migrate when needed |
| Export blocking requests | No job queue (Variant A) | Queue with BullMQ |
| Token management complex | Multi-user | Use factory pattern per user |
| Integration export quota | > 5,000/day | Contact Canva for increase |

## Resources

- [Canva Starter Kit](https://github.com/canva-sdks/canva-connect-api-starter-kit)
- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)
- [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html)

## Next Steps

For common anti-patterns, see `canva-known-pitfalls`.
