## Implementation Guide

### Step 1: Implement Singleton Pattern (Recommended)

```typescript
// src/vercel/client.ts
import { VercelClient } from 'vercel';

let instance: VercelClient | null = null;

export function getVercelClient(): VercelClient {
  if (!instance) {
    instance = new VercelClient({
      apiKey: process.env.VERCEL_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper

```typescript
import { VercelError } from 'vercel';

async function safeVercelCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof VercelError) {
      console.error({
        code: err.code,
        message: err.message,
      });
    }
    return { data: null, error: err as Error };
  }
}
```

### Step 3: Implement Retry Logic

```typescript
async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  backoffMs = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === maxRetries) throw err;
      const delay = backoffMs * Math.pow(2, attempt - 1);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
