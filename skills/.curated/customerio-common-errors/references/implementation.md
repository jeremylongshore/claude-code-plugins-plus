# Customer.io Common Errors - Implementation Details

## Configuration

### Error Classification Map

```typescript
interface CioErrorInfo {
  type: string;
  retryable: boolean;
  resolution: string;
}

const CIO_ERROR_MAP: Record<number, CioErrorInfo> = {
  400: { type: 'BAD_REQUEST', retryable: false, resolution: 'Validate payload: check required fields, data types, and size limits' },
  401: { type: 'UNAUTHORIZED', retryable: false, resolution: 'Verify site_id + api_key pair; check key has not been revoked' },
  404: { type: 'NOT_FOUND', retryable: false, resolution: 'Customer does not exist; call identify() before track()' },
  408: { type: 'REQUEST_TIMEOUT', retryable: true, resolution: 'Retry; increase client timeout beyond 5s for bulk operations' },
  429: { type: 'RATE_LIMITED', retryable: true, resolution: 'Back off exponentially; Track API limit is ~100 req/s' },
  500: { type: 'INTERNAL_ERROR', retryable: true, resolution: 'Retry 3x with backoff; check status.customer.io if persistent' },
  503: { type: 'SERVICE_UNAVAILABLE', retryable: true, resolution: 'CIO is down; queue events locally and replay later' },
};

function handleCioError(status: number, body?: any): CioErrorInfo {
  return CIO_ERROR_MAP[status] ?? {
    type: 'UNKNOWN',
    retryable: false,
    resolution: `Unexpected status ${status}; check CIO API docs`,
  };
}
```

## Advanced Patterns

### Auto-Retry Wrapper

```typescript
async function withCioRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      const info = handleCioError(err.statusCode ?? 0);
      if (!info.retryable || attempt === maxRetries) {
        console.error(`[CIO] Non-retryable error: ${info.type} - ${info.resolution}`);
        throw err;
      }
      const delay = Math.pow(2, attempt) * 1000 + Math.random() * 500;
      console.warn(`[CIO] ${info.type}, retry ${attempt + 1} in ${Math.round(delay)}ms`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error('unreachable');
}
```

### Safe Track (Auto-Identify on 404)

```typescript
async function safeTrack(userId: string, event: string, data: any) {
  try {
    await cio.track(userId, { name: event, data });
  } catch (err: any) {
    if (err.statusCode === 404) {
      console.warn(`[CIO] Customer ${userId} not found, auto-identifying`);
      await cio.identify(userId, { _auto_created: true, created_at: Math.floor(Date.now() / 1000) });
      await cio.track(userId, { name: event, data });
    } else {
      throw err;
    }
  }
}
```

### Bulk Operation Error Handling

```typescript
interface BulkResult {
  succeeded: number;
  failed: Array<{ item: any; error: string }>;
}

async function bulkIdentify(customers: Array<{ id: string; attrs: any }>): Promise<BulkResult> {
  const result: BulkResult = { succeeded: 0, failed: [] };

  for (const chunk of chunkArray(customers, 100)) {
    const results = await Promise.allSettled(
      chunk.map((c) => cio.identify(c.id, c.attrs))
    );
    results.forEach((r, i) => {
      if (r.status === 'fulfilled') result.succeeded++;
      else result.failed.push({ item: chunk[i], error: r.reason?.message });
    });
  }

  return result;
}
```

## Troubleshooting

### Quick Credential Check

```bash
# Test Track API (basic auth: site_id:api_key)
curl -s -w "\nHTTP %{http_code}\n" \
  -u "$CIO_SITE_ID:$CIO_API_KEY" \
  https://track.customer.io/api/v2/entity

# Test App API (bearer token)
curl -s -w "\nHTTP %{http_code}\n" \
  -H "Authorization: Bearer $CIO_APP_API_KEY" \
  https://api.customer.io/v1/campaigns

# Check CIO status page
curl -s https://status.customer.io/api/v2/status.json | jq '.status'
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
