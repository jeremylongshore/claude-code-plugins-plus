# Variant B: Service Layer (Moderate)

## Variant B: Service Layer (Moderate)

**Best for:** Growing startups, 10K-100K DAU, multiple integrations

```
my-app/
├── src/
│   ├── services/
│   │   ├── supabase/
│   │   │   ├── client.ts      # Client wrapper
│   │   │   ├── service.ts     # Business logic
│   │   │   ├── repository.ts  # Data access
│   │   │   └── types.ts
│   │   └── index.ts           # Service exports
│   ├── controllers/
│   │   └── supabase.ts
│   ├── routes/
│   ├── middleware/
│   ├── queue/
│   │   └── supabase-processor.ts  # Async processing
│   └── index.ts
├── config/
│   └── supabase/
└── package.json
```

### Key Characteristics

- Separation of concerns
- Background job processing
- Redis caching
- Circuit breaker pattern
- Structured error handling

### Code Pattern

```typescript
// Service layer abstraction
class SupabaseService {
  constructor(
    private client: SupabaseClient,
    private cache: CacheService,
    private queue: QueueService
  ) {}

  async createResource(data: CreateInput): Promise<Resource> {
    // Business logic before API call
    const validated = this.validate(data);

    // Check cache
    const cached = await this.cache.get(cacheKey);
    if (cached) return cached;

    // API call with retry
    const result = await this.withRetry(() =>
      this.client.create(validated)
    );

    // Cache result
    await this.cache.set(cacheKey, result, 300);

    // Async follow-up
    await this.queue.enqueue('supabase.post-create', result);

    return result;
  }
}
```

---
