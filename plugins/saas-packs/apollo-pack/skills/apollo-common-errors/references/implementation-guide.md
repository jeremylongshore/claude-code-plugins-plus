# Apollo Common Errors - Implementation Guide

> Full implementation details and code examples for the `apollo-common-errors` skill.

# Apollo Common Errors

## Overview
Comprehensive guide to diagnosing and fixing common Apollo.io API errors with specific solutions and prevention strategies.

## Error Reference

### 401 Unauthorized

**Symptoms:**
```json
{
  "error": "Unauthorized",
  "message": "Invalid API key"
}
```

**Causes:**
1. Missing API key in request
2. Invalid or expired API key
3. API key revoked by admin
4. Wrong API key (sandbox vs production)

**Solutions:**
```bash
# Verify API key is set
echo $APOLLO_API_KEY | head -c 10

# Test API key directly
curl -s "https://api.apollo.io/v1/auth/health?api_key=$APOLLO_API_KEY" | jq

# Check key in Apollo dashboard
# Settings > Integrations > API > View/Regenerate Key
```

**Prevention:**
```typescript
// Validate API key on startup
async function validateApiKey() {
  try {
    await apollo.healthCheck();
    console.log('Apollo API key valid');
  } catch (error) {
    console.error('Invalid Apollo API key - check APOLLO_API_KEY');
    process.exit(1);
  }
}
```

---

### 403 Forbidden

**Symptoms:**
```json
{
  "error": "Forbidden",
  "message": "You don't have permission to access this resource"
}
```

**Causes:**
1. API feature not available in plan
2. User role doesn't have access
3. IP restriction blocking request
4. Attempting to access another account's data

**Solutions:**
```typescript
// Check plan features before calling
const PLAN_FEATURES = {
  basic: ['people_search', 'organization_enrich'],
  professional: ['sequences', 'bulk_operations'],
  enterprise: ['advanced_search', 'custom_fields'],
};

function checkFeatureAccess(feature: string, plan: string): boolean {
  return PLAN_FEATURES[plan]?.includes(feature) ?? false;
}
```

---

### 422 Unprocessable Entity

**Symptoms:**
```json
{
  "error": "Unprocessable Entity",
  "message": "q_organization_domains must be an array"
}
```

**Causes:**
1. Invalid request body format
2. Missing required fields
3. Wrong data types
4. Invalid enum values

**Common Fixes:**

```typescript
// WRONG: String instead of array
const wrong = { q_organization_domains: 'apollo.io' };

// CORRECT: Array format
const correct = { q_organization_domains: ['apollo.io'] };

// WRONG: Number instead of string
const wrong2 = { per_page: '25' };

// CORRECT: Number type
const correct2 = { per_page: 25 };
```

**Validation Helper:**
```typescript
import { z } from 'zod';

const PeopleSearchSchema = z.object({
  q_organization_domains: z.array(z.string()).optional(),
  person_titles: z.array(z.string()).optional(),
  page: z.number().int().positive().default(1),
  per_page: z.number().int().min(1).max(100).default(25),
});

function validateSearchParams(params: unknown) {
  return PeopleSearchSchema.parse(params);
}
```

---

### 429 Too Many Requests (Rate Limited)

**Symptoms:**
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Please retry after 60 seconds."
}
```

**Rate Limits:**
| Endpoint | Limit | Window |
|----------|-------|--------|
| People Search | 100 req/min | 1 minute |
| Enrichment | 100 req/min | 1 minute |
| Sequences | 50 req/min | 1 minute |
| Bulk Operations | 10 req/min | 1 minute |

**Solution - Exponential Backoff:**
```typescript
class RateLimitHandler {
  private retryAfter = 0;
  private retryCount = 0;
  private maxRetries = 5;

  async executeWithRetry<T>(fn: () => Promise<T>): Promise<T> {
    while (this.retryCount < this.maxRetries) {
      try {
        if (this.retryAfter > 0) {
          await this.wait(this.retryAfter);
          this.retryAfter = 0;
        }
        return await fn();
      } catch (error: any) {
        if (error.response?.status === 429) {
          this.retryAfter = this.parseRetryAfter(error.response);
          this.retryCount++;
          console.warn(`Rate limited, retry ${this.retryCount} after ${this.retryAfter}ms`);
        } else {
          throw error;
        }
      }
    }
    throw new Error('Max retries exceeded');
  }

  private parseRetryAfter(response: any): number {
    const retryHeader = response.headers['retry-after'];
    if (retryHeader) {
      return parseInt(retryHeader) * 1000;
    }
    return Math.pow(2, this.retryCount) * 1000; // Exponential backoff
  }

  private wait(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

---

### 500 Internal Server Error

**Symptoms:**
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

**Causes:**
1. Apollo service outage
2. Malformed request causing server error
3. Timeout on complex queries

**Solutions:**
```bash
# Check Apollo status
curl -s https://status.apollo.io/api/v2/status.json | jq '.status.description'

# Simplify query and retry
curl -X POST "https://api.apollo.io/v1/people/search" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "'$APOLLO_API_KEY'", "page": 1, "per_page": 1}'
```

---

### Empty Results

**Symptoms:**
```json
{
  "people": [],
  "pagination": { "total_entries": 0 }
}
```

**Causes:**
1. Too restrictive filters
2. Invalid domain or company name
3. No matching data in Apollo database

**Diagnostic Steps:**
```typescript
async function diagnoseEmptyResults(criteria: any) {
  // Test each filter individually
  const tests = [
    { name: 'domain', params: { q_organization_domains: criteria.domains } },
    { name: 'titles', params: { person_titles: criteria.titles } },
    { name: 'location', params: { person_locations: criteria.locations } },
  ];

  for (const test of tests) {
    if (test.params[Object.keys(test.params)[0]]) {
      const result = await apollo.searchPeople({ ...test.params, per_page: 1 });
      console.log(`${test.name}: ${result.pagination.total_entries} results`);
    }
  }
}
```

---

## Error Handling Pattern

```typescript
// src/lib/apollo/error-handler.ts
import { AxiosError } from 'axios';

export class ApolloErrorHandler {
  handle(error: AxiosError): never {
    const status = error.response?.status;
    const data = error.response?.data as any;

    switch (status) {
      case 401:
        throw new ApolloAuthError(
          'Invalid API key. Verify APOLLO_API_KEY is set correctly.'
        );
      case 403:
        throw new ApolloPermissionError(
          `Permission denied: ${data?.message || 'Check your plan features'}`
        );
      case 422:
        throw new ApolloValidationError(
          `Invalid request: ${data?.message}`,
          data?.errors
        );
      case 429:
        throw new ApolloRateLimitError(
          'Rate limit exceeded',
          this.parseRetryAfter(error)
        );
      case 500:
        throw new ApolloServerError(
          'Apollo server error. Check status.apollo.io'
        );
      default:
        throw new ApolloError(
          `Apollo API error: ${status} - ${data?.message || error.message}`
        );
    }
  }

  private parseRetryAfter(error: AxiosError): number {
    return parseInt(error.response?.headers['retry-after'] || '60');
  }
}
```

## Resources
- [Apollo API Error Codes](https://apolloio.github.io/apollo-api-docs/#errors)
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support](https://support.apollo.io)

## Next Steps
Proceed to `apollo-debug-bundle` for collecting debug evidence.
