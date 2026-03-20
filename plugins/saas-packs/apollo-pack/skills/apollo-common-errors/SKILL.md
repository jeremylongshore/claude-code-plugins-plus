---
name: apollo-common-errors
description: |
  Diagnose and fix common Apollo.io API errors.
  Use when encountering Apollo API errors, debugging integration issues,
  or troubleshooting failed requests.
  Trigger with phrases like "apollo error", "apollo api error",
  "debug apollo", "apollo 401", "apollo 429", "apollo troubleshoot".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Common Errors

## Overview
Comprehensive guide to diagnosing and fixing Apollo.io API errors (`https://api.apollo.io/v1`). Covers HTTP status codes, authentication failures, rate limiting, and malformed request debugging with specific code fixes.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Identify the Error Category
```typescript
// src/apollo/error-handler.ts
import { AxiosError } from 'axios';

type ErrorCategory = 'auth' | 'rate_limit' | 'validation' | 'server' | 'network';

function categorizeError(err: AxiosError): ErrorCategory {
  if (!err.response) return 'network';
  switch (err.response.status) {
    case 401: case 403: return 'auth';
    case 429: return 'rate_limit';
    case 400: case 422: return 'validation';
    default: return 'server';
  }
}
```

### Step 2: Handle Authentication Errors (401 / 403)
```typescript
// Diagnosis: verify your API key is valid
async function diagnoseAuth() {
  try {
    await client.post('/people/search', {
      q_organization_domains: ['apollo.io'],
      per_page: 1,
    });
    console.log('API key is valid');
  } catch (err: any) {
    if (err.response?.status === 401) {
      console.error('Invalid API key. Check:');
      console.error('  1. APOLLO_API_KEY env var is set');
      console.error('  2. Key matches Apollo Dashboard > Settings > Integrations > API');
      console.error('  3. Key has not been revoked or expired');
    }
    if (err.response?.status === 403) {
      console.error('Insufficient permissions. Your plan may not include API access.');
    }
  }
}
```

### Step 3: Handle Rate Limiting (429)
```typescript
// Apollo rate limits vary by plan:
//   Free: 100 requests/hour
//   Basic: 300 requests/hour
//   Professional: 600 requests/hour
//   Enterprise: custom limits
//
// The 429 response includes a Retry-After header (seconds).

async function handleRateLimit<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (err: any) {
    if (err.response?.status === 429) {
      const retryAfter = parseInt(err.response.headers['retry-after'] ?? '60', 10);
      console.warn(`Rate limited. Retrying in ${retryAfter}s...`);
      await new Promise((r) => setTimeout(r, retryAfter * 1000));
      return fn();
    }
    throw err;
  }
}
```

### Step 4: Handle Validation Errors (400 / 422)
```typescript
// Common 422 causes:
//   - Missing required fields in request body
//   - Invalid email format in /people/match
//   - Invalid domain format in /organizations/enrich
//   - page/per_page out of bounds (per_page max: 100)

function logValidationError(err: AxiosError) {
  const body = err.response?.data as any;
  console.error('Validation error:', {
    status: err.response?.status,
    message: body?.message ?? body?.error,
    details: body?.errors ?? body?.error_details,
    requestUrl: err.config?.url,
    requestBody: err.config?.data,
  });
}

// Fix: validate inputs before sending
function validateSearchParams(params: any) {
  if (params.per_page && (params.per_page < 1 || params.per_page > 100)) {
    throw new Error('per_page must be between 1 and 100');
  }
  if (params.q_organization_domains) {
    for (const d of params.q_organization_domains) {
      if (!/^[a-zA-Z0-9][a-zA-Z0-9-]*\.[a-zA-Z]{2,}$/.test(d)) {
        throw new Error(`Invalid domain: ${d}`);
      }
    }
  }
}
```

### Step 5: Build a Comprehensive Error Handler
```typescript
// src/apollo/error-middleware.ts
export function createErrorHandler() {
  return async function handleApolloError(err: AxiosError) {
    const status = err.response?.status;
    const body = err.response?.data as any;

    const errorInfo = {
      status,
      endpoint: err.config?.url,
      message: body?.message ?? err.message,
      timestamp: new Date().toISOString(),
      requestId: err.response?.headers['x-request-id'],
    };

    switch (categorizeError(err)) {
      case 'auth':
        console.error('[APOLLO AUTH]', errorInfo);
        break;
      case 'rate_limit':
        console.warn('[APOLLO RATE LIMIT]', errorInfo);
        break;
      case 'validation':
        console.error('[APOLLO VALIDATION]', errorInfo);
        break;
      case 'server':
        console.error('[APOLLO SERVER]', errorInfo);
        break;
      case 'network':
        console.error('[APOLLO NETWORK] Cannot reach api.apollo.io', errorInfo);
        break;
    }

    throw err;
  };
}

// Attach to axios client
client.interceptors.response.use(
  (response) => response,
  createErrorHandler(),
);
```

## Output
- Error categorization function mapping HTTP codes to actionable categories
- Authentication diagnostic utility
- Rate limit handler with `Retry-After` header support
- Input validation for search/enrichment parameters
- Axios interceptor for global error logging

## Error Handling
| Code | Meaning | Fix |
|------|---------|-----|
| 401 | Invalid API key | Verify `APOLLO_API_KEY` env var, regenerate in dashboard |
| 403 | Plan lacks API access | Upgrade Apollo plan or check feature entitlements |
| 422 | Malformed request body | Validate inputs: domain format, per_page range (1-100) |
| 429 | Rate limit exceeded | Read `Retry-After` header, implement backoff |
| 500 | Apollo server error | Retry with backoff, check [status.apollo.io](https://status.apollo.io) |
| ECONNREFUSED | Network/firewall block | Ensure outbound HTTPS to `api.apollo.io` is allowed |

## Examples

### Quick Diagnostic Script
```bash
# Test API key validity from the command line
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.apollo.io/v1/people/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$APOLLO_API_KEY\", \"per_page\": 1}"
# 200 = valid, 401 = invalid key, 429 = rate limited
```

## Resources
- [Apollo API Error Codes](https://apolloio.github.io/apollo-api-docs/#errors)
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Rate Limits](https://apolloio.github.io/apollo-api-docs/#rate-limits)

## Next Steps
Proceed to `apollo-debug-bundle` for collecting debug evidence.
