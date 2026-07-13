# Apollo Common Errors - Implementation Details

## Configuration

### API Client Setup with Error Interception

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';

interface ApolloErrorContext {
  endpoint: string;
  statusCode: number;
  errorType: string;
  retryable: boolean;
  resolution: string;
}

export class ApolloClient {
  private http: AxiosInstance;

  constructor(apiKey: string) {
    this.http = axios.create({
      baseURL: 'https://api.apollo.io/v1',
      headers: {
        'Content-Type': 'application/json',
        'X-Api-Key': apiKey,
      },
      timeout: 30000,
    });

    this.http.interceptors.response.use(
      (res) => res,
      (err: AxiosError) => this.classifyAndThrow(err)
    );
  }

  private classifyAndThrow(error: AxiosError): never {
    const status = error.response?.status ?? 0;
    const url = error.config?.url ?? 'unknown';

    const errorMap: Record<number, { type: string; retryable: boolean; fix: string }> = {
      401: { type: 'INVALID_API_KEY', retryable: false, fix: 'Verify key at app.apollo.io > Settings > API Keys' },
      403: { type: 'PLAN_LIMIT_REACHED', retryable: false, fix: 'Upgrade Apollo plan or check team permissions' },
      404: { type: 'NOT_FOUND', retryable: false, fix: 'Check person/org ID exists and you have access' },
      422: { type: 'VALIDATION_ERROR', retryable: false, fix: 'Validate request body fields per Apollo API docs' },
      429: { type: 'RATE_LIMITED', retryable: true, fix: 'Back off; Apollo allows ~100 requests/min on most plans' },
      500: { type: 'SERVER_ERROR', retryable: true, fix: 'Retry with backoff; check status.apollo.io' },
    };

    const info = errorMap[status] ?? { type: 'UNKNOWN', retryable: false, fix: 'Check Apollo API docs' };
    throw Object.assign(new Error(`Apollo ${info.type} on ${url} (${status})`), {
      retryable: info.retryable,
      resolution: info.fix,
    });
  }
}
```

## Advanced Patterns

### Retry with Exponential Backoff

```typescript
async function withRetry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  for (let i = 0; i <= retries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      if (!err.retryable || i === retries) throw err;
      const ms = 1000 * Math.pow(2, i) + Math.random() * 500;
      await new Promise((r) => setTimeout(r, ms));
    }
  }
  throw new Error('unreachable');
}
```

### Bulk Match Error Aggregation

```typescript
async function bulkMatch(emails: string[]) {
  const results = { matched: [] as any[], errors: [] as any[] };
  for (const chunk of chunkArray(emails, 10)) {
    try {
      const { data } = await client.post('/people/bulk_match', {
        details: chunk.map((email) => ({ email })),
      });
      results.matched.push(...data.matches);
    } catch (err) {
      results.errors.push({ emails: chunk, error: String(err) });
    }
  }
  return results;
}
```

## Troubleshooting

### Key Validation

```bash
# Check key length and hidden characters
echo -n "$APOLLO_API_KEY" | wc -c   # should be ~40
echo -n "$APOLLO_API_KEY" | xxd | tail -1

# Direct health check
curl -s -w "\nHTTP %{http_code}\n" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  https://api.apollo.io/v1/auth/health
```

### Rate Limit Monitoring

```typescript
function parseRateLimits(headers: Record<string, string>) {
  return {
    remaining: parseInt(headers['x-rate-limit-remaining'] ?? '0'),
    limit: parseInt(headers['x-rate-limit-limit'] ?? '0'),
    resetsAt: new Date(Number(headers['x-rate-limit-reset'] ?? 0) * 1000),
  };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
