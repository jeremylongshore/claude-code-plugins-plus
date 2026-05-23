# Key Components

## Key Components

### Step 1: Client Wrapper

```typescript
// src/vercel/client.ts
export class VercelService {
  private client: VercelClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: VercelConfig) {
    this.client = new VercelClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('vercel');
  }

  async get(id: string): Promise<Resource> {
    return this.cache.getOrFetch(id, () =>
      this.monitor.track('get', () => this.client.get(id))
    );
  }
}
```

### Step 2: Error Boundary

```typescript
// src/vercel/errors.ts
export class VercelServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'VercelServiceError';
  }
}

export function wrapVercelError(error: unknown): VercelServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check

```typescript
// src/vercel/health.ts
export async function checkVercelHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await vercelClient.ping();
    return {
      status: 'healthy',
      latencyMs: Date.now() - start,
    };
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
  }
}
```
