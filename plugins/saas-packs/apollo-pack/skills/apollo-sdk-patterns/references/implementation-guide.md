# Apollo SDK Patterns - Implementation Guide

> Full implementation details and code examples for the `apollo-sdk-patterns` skill.

# Apollo SDK Patterns

## Overview
Production-ready patterns for Apollo.io API integration with type safety, error handling, and retry logic.

## Prerequisites
- Completed `apollo-install-auth` setup
- Familiarity with async/await patterns
- Understanding of TypeScript generics

## Pattern 1: Type-Safe Client Singleton

```typescript
// src/lib/apollo/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';
import { z } from 'zod';

// Response schemas
const PersonSchema = z.object({
  id: z.string(),
  name: z.string(),
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  title: z.string().optional(),
  email: z.string().email().optional(),
  linkedin_url: z.string().url().optional(),
  organization: z.object({
    id: z.string(),
    name: z.string(),
    domain: z.string().optional(),
  }).optional(),
});

const PeopleSearchResponseSchema = z.object({
  people: z.array(PersonSchema),
  pagination: z.object({
    page: z.number(),
    per_page: z.number(),
    total_entries: z.number(),
    total_pages: z.number(),
  }),
});

export type Person = z.infer<typeof PersonSchema>;
export type PeopleSearchResponse = z.infer<typeof PeopleSearchResponseSchema>;

class ApolloClient {
  private static instance: ApolloClient;
  private client: AxiosInstance;

  private constructor() {
    this.client = axios.create({
      baseURL: 'https://api.apollo.io/v1',
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' },
      params: { api_key: process.env.APOLLO_API_KEY },
    });

    this.setupInterceptors();
  }

  static getInstance(): ApolloClient {
    if (!ApolloClient.instance) {
      ApolloClient.instance = new ApolloClient();
    }
    return ApolloClient.instance;
  }

  private setupInterceptors() {
    this.client.interceptors.response.use(
      (response) => response,
      this.handleError.bind(this)
    );
  }

  private handleError(error: AxiosError) {
    if (error.response?.status === 429) {
      throw new ApolloRateLimitError('Rate limit exceeded');
    }
    if (error.response?.status === 401) {
      throw new ApolloAuthError('Invalid API key');
    }
    throw error;
  }

  async searchPeople(params: PeopleSearchParams): Promise<PeopleSearchResponse> {
    const { data } = await this.client.post('/people/search', params);
    return PeopleSearchResponseSchema.parse(data);
  }
}

export const apollo = ApolloClient.getInstance();
```

## Pattern 2: Retry with Exponential Backoff

```typescript
// src/lib/apollo/retry.ts
interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
}

const defaultConfig: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 30000,
};

export async function withRetry<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const { maxRetries, baseDelay, maxDelay } = { ...defaultConfig, ...config };

  let lastError: Error;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (error instanceof ApolloAuthError) {
        throw error; // Don't retry auth errors
      }

      if (attempt < maxRetries) {
        const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError!;
}

// Usage
const people = await withRetry(() => apollo.searchPeople({ domain: 'stripe.com' }));
```

## Pattern 3: Paginated Iterator

```typescript
// src/lib/apollo/pagination.ts
export async function* paginateSearch(
  searchFn: (page: number) => Promise<PeopleSearchResponse>,
  options: { maxPages?: number } = {}
): AsyncGenerator<Person[], void, unknown> {
  const maxPages = options.maxPages || Infinity;
  let page = 1;
  let totalPages = 1;

  while (page <= Math.min(totalPages, maxPages)) {
    const response = await searchFn(page);
    totalPages = response.pagination.total_pages;

    yield response.people;
    page++;

    // Respect rate limits
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
}

// Usage
async function getAllPeople(domain: string): Promise<Person[]> {
  const allPeople: Person[] = [];

  for await (const batch of paginateSearch(
    (page) => apollo.searchPeople({ q_organization_domains: [domain], page, per_page: 100 })
  )) {
    allPeople.push(...batch);
  }

  return allPeople;
}
```

## Pattern 4: Request Batching

```typescript
// src/lib/apollo/batch.ts
class ApolloBatcher {
  private queue: Array<{ domain: string; resolve: Function; reject: Function }> = [];
  private timeout: NodeJS.Timeout | null = null;
  private readonly batchSize = 10;
  private readonly batchDelay = 100;

  async enrichCompany(domain: string): Promise<Organization> {
    return new Promise((resolve, reject) => {
      this.queue.push({ domain, resolve, reject });
      this.scheduleBatch();
    });
  }

  private scheduleBatch() {
    if (this.timeout) return;

    this.timeout = setTimeout(async () => {
      this.timeout = null;
      const batch = this.queue.splice(0, this.batchSize);

      try {
        // Apollo doesn't have batch endpoint, process sequentially with rate limiting
        for (const item of batch) {
          try {
            const result = await apollo.enrichOrganization(item.domain);
            item.resolve(result);
          } catch (error) {
            item.reject(error);
          }
          await new Promise((r) => setTimeout(r, 50)); // Rate limit spacing
        }
      } catch (error) {
        batch.forEach((item) => item.reject(error));
      }

      if (this.queue.length > 0) {
        this.scheduleBatch();
      }
    }, this.batchDelay);
  }
}

export const apolloBatcher = new ApolloBatcher();
```

## Pattern 5: Custom Error Classes

```typescript
// src/lib/apollo/errors.ts
export class ApolloError extends Error {
  constructor(message: string, public readonly code?: string) {
    super(message);
    this.name = 'ApolloError';
  }
}

export class ApolloRateLimitError extends ApolloError {
  constructor(message: string = 'Rate limit exceeded') {
    super(message, 'RATE_LIMIT');
    this.name = 'ApolloRateLimitError';
  }
}

export class ApolloAuthError extends ApolloError {
  constructor(message: string = 'Authentication failed') {
    super(message, 'AUTH_ERROR');
    this.name = 'ApolloAuthError';
  }
}

export class ApolloValidationError extends ApolloError {
  constructor(message: string, public readonly details?: unknown) {
    super(message, 'VALIDATION_ERROR');
    this.name = 'ApolloValidationError';
  }
}
```

## Output
- Type-safe client singleton with Zod validation
- Robust error handling with custom error classes
- Automatic retry with exponential backoff
- Async pagination iterator
- Request batching for bulk operations

## Error Handling
| Pattern | When to Use |
|---------|-------------|
| Singleton | Always - ensures single client instance |
| Retry | Network errors, 429/500 responses |
| Pagination | Large result sets (>100 records) |
| Batching | Multiple enrichment calls |
| Custom Errors | Distinguish error types in catch blocks |

## Resources
- [Zod Documentation](https://zod.dev/)
- [Axios Interceptors](https://axios-http.com/docs/interceptors)
- [TypeScript Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)

## Next Steps
Proceed to `apollo-core-workflow-a` for lead search implementation.
